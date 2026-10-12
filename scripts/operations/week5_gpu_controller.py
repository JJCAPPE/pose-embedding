"""Run unchanged frozen GPU commands with a CUDA-free monitoring parent.

The reviewed synthetic exclusive-context diagnostic must pass first. GPU memory
preflight runs in a short-lived child; its context exits before scientific work.
The frozen monitor retains 60-second NVIDIA, RAM, storage and process records.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import re
import signal
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

import torch

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import canonical_artifact_root, dataset_access
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

RELEASE = "731938a157be575ee433d6939876f8ca0b95e459"
REVISION = Path("study-v3/revisions/execution-r1")
METHODS = ("contrastive", "contextual", "supcon")
DIAGNOSTIC_SHA256 = "751259d69fcd24ca6f36439f304bc59640da80ab8b3356092204cf65ea878d73"
EXECUTION_SOURCES = (
    "scripts/operations/week5_gpu_controller.py",
    "scripts/operations/week5_gpu_context_diagnostic.py",
    "scripts/operations/week5_gpu.qsub",
    "scripts/run_v3_execution.py",
)


def execution_binding(expected_release, revision):
    if (
        re.fullmatch(r"[0-9a-f]{40}", expected_release) is None
        or revision not in {"execution-r1", "execution-r2"}
        or (revision == "execution-r1") != (expected_release == RELEASE)
        or require_clean_repository() != expected_release
    ):
        raise ValueError("GPU controller requires its clean full release and revision")
    if revision == "execution-r1":
        return {}
    sources = {name: sha256_file(name) for name in EXECUTION_SOURCES}
    if sha256_file(__file__) != sources[EXECUTION_SOURCES[0]]:
        raise ValueError("successor controller differs from its tracked release")
    return sources


def read(path):
    return json.loads(Path(path).read_text())


def require_cuda_free_parent():
    if torch.cuda.is_initialized():
        raise RuntimeError("monitoring parent must never initialize CUDA")


def validate_allocation(qstat_xml, qstat_job, *, job_id, hostname):
    jobs = [
        job
        for job in ElementTree.fromstring(qstat_xml).findall(".//job_list")
        if job.findtext("JB_job_number") == job_id
    ]
    if len(jobs) != 1:
        raise ValueError("GPU job is absent or ambiguous in scheduler state")
    job = jobs[0]
    host = (job.findtext("queue_name") or "").partition("@")[2]
    if (
        job.get("state") != "running"
        or job.findtext("state") != "r"
        or host.split(".")[0] != hostname.split(".")[0]
        or job.findtext("slots") != "4"
    ):
        raise ValueError("GPU controller requires four running slots on this host")
    hard = re.search(r"^hard resource_list:\s*(.+)$", qstat_job, re.M)
    if hard is None:
        raise ValueError("scheduler hard resources are missing")
    requested = dict(part.strip().split("=", 1) for part in hard[1].split(","))
    if (
        requested.get("h_rt") not in {"12:00:00", "43200"}
        or requested.get("mem_per_core") not in {"8G", "8.000G", "8192M"}
        or requested.get("gpus") != "1"
        or requested.get("gpu_type") != "L40S"
        or requested.get("gpu_memory") not in {"16G", "16.000G", "16384M"}
    ):
        raise ValueError("GPU controller requires the reviewed 12h/32GiB/L40S request")


def validate_diagnostic(
    root,
    path,
    expected_sha,
    *,
    expected_release=RELEASE,
    revision="execution-r1",
    source_hashes=None,
):
    path = require_path_within(path, root, label="GPU diagnostic receipt")
    if sha256_file(path) != expected_sha:
        raise ValueError("GPU diagnostic receipt differs from the reviewed hash")
    record = read(path)
    expected = {
        "kind": "exclusive_process_cuda_diagnostic",
        "status": "passed",
        "scientific_use_allowed": False,
        "parent_cuda_initialized": False,
        "sequential_probe_count": 2,
        "held_context_probe_rejected": True,
        "script_sha256": DIAGNOSTIC_SHA256,
        "source_release": expected_release,
    }
    if revision == "execution-r2":
        if not source_hashes or set(source_hashes) != set(EXECUTION_SOURCES):
            raise ValueError("successor diagnostic requires complete helper bindings")
        expected.update(
            script_sha256=source_hashes[EXECUTION_SOURCES[1]],
            execution_revision=revision,
            execution_sources_sha256=source_hashes,
        )
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("reviewed exclusive-context diagnostic has not passed")
    evidence = record.get("evidence")
    required = {
        "attempt.json",
        "seal-before.json",
        "seal-after.json",
        "holder-ready.json",
        "holder-outcome.json",
        "held-probe-outcome.json",
        "sequential-1-outcome.json",
        "sequential-2-outcome.json",
        "snapshots/before.json",
        "snapshots/holder-active.json",
    }
    if not isinstance(evidence, dict) or not required <= set(evidence):
        raise ValueError("GPU diagnostic omits its retained observation chain")
    for relative, digest in evidence.items():
        observed = require_path_within(
            path.parent / relative, path.parent, label="GPU diagnostic evidence"
        )
        if not observed.is_file() or sha256_file(observed) != digest:
            raise ValueError("GPU diagnostic evidence changed or is missing")
    return {"relative_path": str(path.relative_to(root)), "sha256": expected_sha}


def gpu_preflight(output, *, expected_release=RELEASE, revision="execution-r1"):
    """This child alone owns CUDA; process exit releases its small context."""
    from pose_embed.models.motionbert import configure_deterministic_inference

    if not os.environ.get("JOB_ID", "").isdigit() or os.environ.get("NSLOTS") != "4":
        raise ValueError("GPU preflight requires its scheduler allocation")
    root = canonical_artifact_root()
    output = require_path_within(
        output, root / "study-v3/operations", label="GPU preflight output"
    )
    execution_binding(expected_release, revision)
    if output.exists():
        raise ValueError("GPU preflight requires new output and the frozen release")
    record = {
        "status": "failed",
        "scientific_use_allowed": False,
        "recorded_at": datetime.now(UTC).isoformat(),
        "pid": os.getpid(),
        "job_id": os.environ["JOB_ID"],
        "hostname": socket.gethostname(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "controller_sha256": sha256_file(__file__),
        "source_release": expected_release,
        "execution_revision": revision,
        "device": 0,
        "minimum_free_bytes": 16 * 2**30,
    }
    try:
        configure_deterministic_inference()
        if torch.cuda.device_count() != 1:
            raise ValueError("exactly one scheduler-visible GPU is required")
        props = torch.cuda.get_device_properties(0)
        if props.name != "NVIDIA L40S":
            raise ValueError("the allocated GPU must be NVIDIA L40S")
        tiny = torch.zeros(1, device="cuda", dtype=torch.float32)
        torch.cuda.synchronize()
        free, total = torch.cuda.mem_get_info(0)
        record.update(
            name=props.name,
            uuid=str(getattr(props, "uuid", "")),
            free_bytes=free,
            total_bytes=total,
            probe_bytes=tiny.numel() * tiny.element_size(),
        )
        if min(free, total) < 16 * 2**30:
            raise ValueError("allocated GPU has less than 16GiB available")
        record["status"] = "passed"
    except BaseException as error:
        record.update(error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        write_immutable_json(output, record)


def stage_commands(args, operations, protocol, bundle, output):
    if args.mode in {"caches", "pilot"}:
        return [
            ["bash", "scripts/study_v3.qsub", args.mode]
            + ([args.method] if args.method else [])
        ]
    if args.mode == "corruptions":
        output.mkdir(parents=True, exist_ok=False)
        return list(
            operations.corruption_commands(
                protocol, bundle, args.cache_dir, args.pilot_dirs, output
            )
        )
    return [
        [
            ".venv/bin/python",
            "scripts/time_v3_resident.py",
            "--protocol-config",
            str(protocol),
            "--cache-dir",
            str(args.cache_dir),
            "--manifest-set",
            str(bundle / "manifest-set.json"),
            "--output-dir",
            str(output),
        ]
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("caches", "pilot", "corruptions", "timing"))
    parser.add_argument("--method", choices=METHODS)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--pilot-dirs", type=Path, nargs=3)
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    parser.add_argument("--recorded-by", required=True)
    parser.add_argument("--diagnostic-receipt", type=Path, required=True)
    parser.add_argument("--diagnostic-sha256", required=True)
    parser.add_argument("--expected-release", default=RELEASE)
    parser.add_argument(
        "--revision", choices=("execution-r1", "execution-r2"), default="execution-r1"
    )
    args = parser.parse_args()
    if (
        not os.environ.get("JOB_ID", "").isdigit()
        or not Path(os.environ.get("TMPDIR", "")).is_dir()
        or not os.environ.get("TMPDIR")
        or os.environ.get("NSLOTS") != "4"
        or args.remaining_peak_bytes < 0
        or not args.recorded_by.strip()
        or re.fullmatch(r"[0-9a-f]{64}", args.diagnostic_sha256) is None
        or ((args.mode == "pilot") != (args.method is not None))
        or ((args.mode != "caches") != (args.cache_dir is not None))
        or ((args.mode == "corruptions") != (args.pilot_dirs is not None))
    ):
        parser.error("valid scheduler allocation, mode inputs and diagnostic required")
    require_cuda_free_parent()
    source_hashes = execution_binding(args.expected_release, args.revision)
    spec = importlib.util.spec_from_file_location(
        "frozen_gpu_operations", Path.cwd() / "scripts/run_v3_execution.py"
    )
    operations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operations)
    signal.signal(signal.SIGTERM, operations.interrupted)
    signal.signal(signal.SIGHUP, operations.interrupted)
    root = canonical_artifact_root()
    launcher_sha256 = sha256_file(__file__)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt = (
        root / "study-v3/operations" / f"{stamp}-{os.environ['JOB_ID']}-{args.mode}"
    )
    revision = Path("study-v3/revisions") / args.revision
    output = root / revision / "attempts" / attempt.name
    protocol_path = root / revision / "locks/protocol.v3.json"
    bundle = Path(os.environ["POSE_EMBED_MANIFEST_SET"]).resolve().parent
    if args.revision == "execution-r2" and bundle != root / revision / "manifests":
        raise ValueError("successor controller requires its own manifest bundle")
    environment = os.environ | {
        "POSE_EMBED_V3_PROTOCOL": str(protocol_path),
        "POSE_EMBED_V3_ATTEMPT": str(output),
    }
    if args.cache_dir:
        args.cache_dir = args.cache_dir.resolve()
        if args.revision == "execution-r2":
            require_path_within(
                args.cache_dir, root / revision, label="successor caches"
            )
        environment["POSE_EMBED_V3_CACHES"] = str(args.cache_dir)
    if args.pilot_dirs:
        args.pilot_dirs = [p.resolve() for p in args.pilot_dirs]
        if args.revision == "execution-r2":
            for path in args.pilot_dirs:
                require_path_within(path, root / revision, label="successor pilot")
    attempt.mkdir(parents=True, exist_ok=False)
    print(f"V3_OPERATION_ATTEMPT={attempt}", flush=True)
    write_immutable_json(
        attempt / "attempt.json",
        {
            "mode": args.mode,
            "started_at": datetime.now(UTC).isoformat(),
            "arguments": vars(args)
            | {
                "cache_dir": str(args.cache_dir) if args.cache_dir else None,
                "pilot_dirs": [str(p) for p in args.pilot_dirs]
                if args.pilot_dirs
                else None,
                "diagnostic_receipt": str(args.diagnostic_receipt),
            },
            "release_sha": args.expected_release,
            "execution_revision": args.revision,
            "execution_sources_sha256": source_hashes,
            "launcher_sha256": launcher_sha256,
            "frozen_operations_sha256": sha256_file("scripts/run_v3_execution.py"),
            "output_directory": str(output),
            "scientific_output": str(output),
            "parent_pid": os.getpid(),
            "parent_cuda_initialized": False,
            "gpu_monitor": "short-lived CUDA preflight; periodic frozen nvidia-smi",
        },
    )
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with dataset_access():
                operations.require_dataset_unopened(require_registry=True)
                require_v3_design(load_protocol(protocol_path))
                diagnostic = validate_diagnostic(
                    root,
                    args.diagnostic_receipt,
                    args.diagnostic_sha256,
                    expected_release=args.expected_release,
                    revision=args.revision,
                    source_hashes=source_hashes,
                )
                write_immutable_json(attempt / "diagnostic-binding.json", diagnostic)
                write_immutable_json(
                    attempt / "seal-before.json",
                    {
                        "status": "sealed",
                        "recorded_at": datetime.now(UTC).isoformat(),
                    },
                )
                try:
                    allocation = {
                        "job_id": os.environ["JOB_ID"],
                        "hostname": socket.gethostname(),
                        "qstat_xml": subprocess.check_output(
                            ["qstat", "-xml"], text=True, timeout=30
                        ),
                        "qstat_job": subprocess.check_output(
                            ["qstat", "-j", os.environ["JOB_ID"]], text=True, timeout=30
                        ),
                    }
                    write_immutable_json(attempt / "allocation.json", allocation)
                    validate_allocation(**allocation)
                    snapshot = operations.resource_snapshot(
                        root, args.remaining_peak_bytes
                    )
                    write_immutable_json(attempt / "resources/preflight.json", snapshot)
                    if (
                        not snapshot["storage_passed"]
                        or not snapshot["host_memory_passed"]
                    ):
                        raise ValueError("storage reserve or host RAM is insufficient")
                    if output.exists():
                        raise ValueError("scientific output directory already exists")
                    commands = [
                        [".venv/bin/python", "scripts/verify_workspace.py"],
                        [
                            ".venv/bin/python",
                            "scripts/fetch_upstreams.py",
                            "--check",
                            "--name",
                            "MotionBERT",
                        ],
                        *stage_commands(
                            args, operations, protocol_path, bundle, output
                        ),
                    ]
                    index = 0
                    for position, command in enumerate(commands):
                        require_cuda_free_parent()
                        if (
                            execution_binding(args.expected_release, args.revision)
                            != source_hashes
                            or sha256_file(__file__) != launcher_sha256
                        ):
                            raise ValueError(
                                "release changed before a monitored command"
                            )
                        if position == 0 or position >= 2:
                            validate_diagnostic(
                                root,
                                args.diagnostic_receipt,
                                args.diagnostic_sha256,
                                expected_release=args.expected_release,
                                revision=args.revision,
                                source_hashes=source_hashes,
                            )
                            gpu_record = (
                                attempt / "gpu-preflights" / f"{index:03d}.json"
                            )
                            operations.run_command(
                                [
                                    ".venv/bin/python3.11",
                                    str(Path(__file__).resolve()),
                                    "--gpu-preflight-output",
                                    str(gpu_record),
                                    "--expected-release",
                                    args.expected_release,
                                    "--revision",
                                    args.revision,
                                ],
                                attempt,
                                index,
                                root,
                                args.remaining_peak_bytes,
                                environment,
                            )
                            require_cuda_free_parent()
                            observed = read(gpu_record)
                            if (
                                observed.get("status") != "passed"
                                or observed.get("controller_sha256") != launcher_sha256
                                or observed.get("source_release")
                                != args.expected_release
                                or observed.get("execution_revision") != args.revision
                            ):
                                raise ValueError("GPU preflight did not pass")
                            if position == 0:
                                write_immutable_json(
                                    attempt / "resources/allocated-gpu.json", observed
                                )
                            index += 1
                        operations.run_command(
                            command,
                            attempt,
                            index,
                            root,
                            args.remaining_peak_bytes,
                            environment,
                        )
                        require_cuda_free_parent()
                        index += 1
                    if (
                        execution_binding(args.expected_release, args.revision)
                        != source_hashes
                        or sha256_file(__file__) != launcher_sha256
                    ):
                        raise ValueError("release changed during GPU work")
                    validate_diagnostic(
                        root,
                        args.diagnostic_receipt,
                        args.diagnostic_sha256,
                        expected_release=args.expected_release,
                        revision=args.revision,
                        source_hashes=source_hashes,
                    )
                finally:
                    seal = {"recorded_at": datetime.now(UTC).isoformat()}
                    try:
                        operations.require_dataset_unopened(require_registry=True)
                        require_cuda_free_parent()
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
        write_immutable_json(
            attempt / "outcome.json",
            {
                "status": "passed",
                "ended_at": datetime.now(UTC).isoformat(),
                "output_directory": str(output),
                "scientific_output": str(output),
                "parent_cuda_initialized": False,
            },
        )
    except BaseException as error:
        write_immutable_json(
            attempt / "outcome.json",
            {
                "status": "failed",
                "ended_at": datetime.now(UTC).isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "parent_cuda_initialized": torch.cuda.is_initialized(),
            },
        )
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3 and sys.argv[1] == "--gpu-preflight-output":
        parser = argparse.ArgumentParser()
        parser.add_argument("--gpu-preflight-output", type=Path, required=True)
        parser.add_argument("--expected-release", default=RELEASE)
        parser.add_argument(
            "--revision",
            choices=("execution-r1", "execution-r2"),
            default="execution-r1",
        )
        options = parser.parse_args()
        gpu_preflight(
            options.gpu_preflight_output,
            expected_release=options.expected_release,
            revision=options.revision,
        )
    else:
        main()
