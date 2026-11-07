"""Prepare allocation-local parity inputs for the unchanged frozen GPU controller."""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import signal
import socket
from datetime import UTC, datetime
from pathlib import Path

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import canonical_artifact_root, dataset_access
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

RELEASE = "f101f0e9d9bd64275d2088deab1b0bdcfcc53620"
REVISION = "execution-r2"


def prepare_inputs(cache, destination, revision_root):
    """Keep the accepted gallery's resolved identity; only parity is newly produced."""
    cache = require_path_within(cache, revision_root, label="accepted gallery")
    destination = require_path_within(
        destination, revision_root / "corruption-inputs", label="parity inputs"
    )
    sources = [
        cache / name
        for name in ("development-gallery.npz", "development-gallery.npz.manifest.json")
    ]
    if not all(path.is_file() and not path.is_symlink() for path in sources):
        raise ValueError("accepted gallery and sidecar must be original regular files")
    destination.mkdir(parents=True, exist_ok=False)
    for path in sources:
        (destination / path.name).symlink_to(path)
    return {str(destination / path.name): str(path) for path in sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["corruptions"])
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--expected-release", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    args = parser.parse_args()
    if args.expected_release != RELEASE or args.revision != REVISION:
        raise ValueError("parity correction requires the frozen execution-r2 release")
    packet_path, expected_sha = args.inputs, args.inputs_sha256
    if sha256_file(packet_path) != expected_sha:
        raise ValueError("reviewed parity input packet changed")
    packet = json.loads(Path(packet_path).read_text())
    for path, digest in packet["bindings"].items():
        if sha256_file(path) != digest:
            raise ValueError(f"parity prerequisite changed: {path}")
    if packet["remaining_peak_bytes"] != args.remaining_peak_bytes:
        raise ValueError("parity and controller storage bounds must agree")
    modules = {}
    for name, path in (
        ("operations", "scripts/run_v3_execution.py"),
        ("controller", "scripts/operations/week5_gpu_controller.py"),
        ("gate", packet["runtime_gate"]),
    ):
        spec = importlib.util.spec_from_file_location(name, Path.cwd() / path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module
    operations, controller = modules["operations"], modules["controller"]
    controller_command = packet["controller_command"]
    modules["gate"].check_command(controller_command)
    if controller_command[:3] != [
        ".venv/bin/python",
        "scripts/operations/week5_gpu_controller.py",
        "corruptions",
    ]:
        raise ValueError("only the unchanged corruption controller may follow parity")
    for flag, value in {
        "--cache-dir": packet["input_dir"],
        "--remaining-peak-bytes": str(args.remaining_peak_bytes),
    }.items():
        if (
            controller_command.count(flag) != 1
            or controller_command[controller_command.index(flag) + 1] != value
        ):
            raise ValueError(
                "controller must use these parity inputs and storage bound"
            )
    controller.require_cuda_free_parent()
    sources = controller.execution_binding(RELEASE, REVISION)
    signal.signal(signal.SIGTERM, operations.interrupted)
    signal.signal(signal.SIGHUP, operations.interrupted)
    root = canonical_artifact_root()
    revision = root / "study-v3/revisions" / REVISION
    protocol = revision / "locks/protocol.v3.json"
    manifest = revision / "manifests/manifest-set.json"
    if os.environ.get("NSLOTS") != "4" or not os.environ.get("JOB_ID", "").isdigit():
        raise ValueError("parity prelude requires its four-slot allocation")
    inputs = Path(packet["input_dir"])
    attempt = (
        root
        / "study-v3/operations"
        / (f"{inputs.name}-{os.environ['JOB_ID']}-corruption-parity")
    )
    attempt.mkdir(parents=True, exist_ok=False)
    outcome = {"status": "failed"}
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with dataset_access():
                try:
                    operations.require_dataset_unopened(require_registry=True)
                    require_v3_design(load_protocol(protocol))
                    write_immutable_json(
                        attempt / "seal-before.json", {"status": "sealed"}
                    )
                    allocation = {
                        "job_id": os.environ["JOB_ID"],
                        "hostname": socket.gethostname(),
                        "qstat_xml": controller.subprocess.check_output(
                            ["qstat", "-xml"], text=True, timeout=30
                        ),
                        "qstat_job": controller.subprocess.check_output(
                            ["qstat", "-j", os.environ["JOB_ID"]], text=True, timeout=30
                        ),
                    }
                    write_immutable_json(attempt / "allocation.json", allocation)
                    controller.validate_allocation(**allocation)
                    controller.validate_diagnostic(
                        root,
                        packet["diagnostic_receipt"],
                        packet["diagnostic_sha256"],
                        expected_release=RELEASE,
                        revision=REVISION,
                        source_hashes=sources,
                    )
                    aliases = prepare_inputs(packet["cache_dir"], inputs, revision)
                    write_immutable_json(
                        attempt / "attempt.json",
                        {
                            "kind": "allocation_local_corruption_parity",
                            "job_id": os.environ["JOB_ID"],
                            "started_at": datetime.now(UTC).isoformat(),
                            "source_release": RELEASE,
                            "script_sha256": sha256_file(__file__),
                            "packet_sha256": expected_sha,
                            "execution_sources_sha256": sources,
                            "original_gallery_links": aliases,
                            "input_dir": str(inputs),
                            "cache_acceptance": packet["cache_acceptance"],
                            "original_cache_dir": packet["cache_dir"],
                            "new_cache_acceptance": False,
                        },
                    )
                    commands = [
                        [
                            ".venv/bin/python",
                            "scripts/operations/week5_gpu_controller.py",
                            "--gpu-preflight-output",
                            str(attempt / "allocated-gpu.json"),
                            "--expected-release",
                            RELEASE,
                            "--revision",
                            REVISION,
                        ],
                        [
                            ".venv/bin/pose-embed",
                            "features",
                            "parity",
                            "--protocol-config",
                            str(protocol),
                            "--manifest-set",
                            str(manifest),
                            "--output",
                            str(inputs / "parity.json"),
                            "--device",
                            "cuda",
                        ],
                    ]
                    for index, command in enumerate(commands):
                        controller.execution_binding(RELEASE, REVISION)
                        operations.run_command(
                            command,
                            attempt,
                            index,
                            root,
                            packet["remaining_peak_bytes"],
                            os.environ.copy(),
                        )
                        controller.require_cuda_free_parent()
                    controller.execution_binding(RELEASE, REVISION)
                    outcome.update(
                        status="passed",
                        parity_sha256=sha256_file(inputs / "parity.json"),
                    )
                finally:
                    seal = {"recorded_at": datetime.now(UTC).isoformat()}
                    try:
                        operations.require_dataset_unopened(require_registry=True)
                        controller.require_cuda_free_parent()
                        seal["status"] = "sealed"
                    except BaseException as error:
                        seal.update(
                            status="failed",
                            error_type=type(error).__name__,
                            error_message=str(error),
                        )
                        raise
                    finally:
                        write_immutable_json(attempt / "seal-after.json", seal)
    except BaseException as error:
        outcome.update(
            status="failed", error_type=type(error).__name__, error_message=str(error)
        )
        raise
    finally:
        outcome["ended_at"] = datetime.now(UTC).isoformat()
        write_immutable_json(attempt / "outcome.json", outcome)
    os.execv(controller_command[0], controller_command)


if __name__ == "__main__":
    main()
