"""Add ADR0008 runtime evidence around unchanged allocated Week 5 controllers."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

RELEASE = "f101f0e9d9bd64275d2088deab1b0bdcfcc53620"
GPU_REPORT = (
    "study-v3/operations/week5-runtime-baseline-gpu/20261022T155221Z/runtime.json"
)
GPU_REPORT_SHA = "7c5aa695ec48d545edb352ea645bab884e67bb9ad25fef8d4eee01e9cd6a813b"
CPU_BUILD_SHA = "f3780d63539668f232ae1b35fd8f5bc2a6821369ddb0c0c04a87c5bad80b1d08"
GPU_BUILD_SHA = "8ef1be76262a97c1101484cef940d6dbb63cf1582bda8fd9d5104e1f54ff6b02"
PARITY_ENTRYPOINT = str(
    Path(__file__).with_name("week5_corruption_parity.py").resolve()
)
PARITY_SHA256 = "d07bd168d06513678cacf9a182416fef64b90487a623b5ff87fba4fa32caaaf7"
TARGETS = {
    PARITY_ENTRYPOINT: ("corruptions",),
    "scripts/operations/week5_gpu_context_diagnostic.py": (),
    "scripts/operations/week5_gpu_controller.py": (
        "caches",
        "pilot",
        "corruptions",
        "timing",
    ),
    "scripts/run_v3_execution.py": ("validate-caches", "validate-pilots"),
    "scripts/operations/week5_admission_controller.py": (),
}
OPTIONS = {
    "--revision",
    "--expected-release",
    "--remaining-peak-bytes",
    "--recorded-by",
    "--output-dir",
    "--diagnostic-receipt",
    "--diagnostic-sha256",
    "--method",
    "--cache-dir",
    "--pilot-dirs",
    "--assembler",
    "--inputs",
    "--inputs-sha256",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_startup_profile(helper, observed, expected):
    actual_runtime = observed["profile"].get("runtime")
    expected_runtime = expected.get("runtime")
    if isinstance(actual_runtime, dict) and isinstance(expected_runtime, dict):
        actual_build = actual_runtime.get("torch_build")
        expected_build = expected_runtime.get("torch_build")
        if (
            isinstance(actual_build, str)
            and isinstance(expected_build, str)
            and hashlib.sha256(expected_build.encode()).hexdigest() == CPU_BUILD_SHA
            and hashlib.sha256(actual_build.encode()).hexdigest() == GPU_BUILD_SHA
        ):
            # PyTorch adds the exact retained CUDA report when GPU hooks are available.
            expected = expected | {
                "runtime": expected_runtime | {"torch_build": actual_build}
            }
    helper.require_profile(observed, expected)


def check_command(command):
    if (
        len(command) < 3
        or command[0] != ".venv/bin/python"
        or command[1] not in TARGETS
    ):
        raise ValueError("only unchanged monitored Week 5 entrypoints are permitted")
    if command[1] == PARITY_ENTRYPOINT:
        for flag in ("--inputs", "--inputs-sha256", "--remaining-peak-bytes"):
            if command.count(flag) != 1 or command.index(flag) + 1 >= len(command):
                raise ValueError(
                    "parity prelude requires explicit packet and storage bindings"
                )
        if (
            re.fullmatch(r"[0-9a-f]{64}", command[command.index("--inputs-sha256") + 1])
            is None
        ):
            raise ValueError("parity prelude requires a full input packet hash")
    modes = TARGETS[command[1]]
    if (
        modes
        and command[2] not in modes
        or any(arg.startswith("-") and arg not in OPTIONS for arg in command[2:])
    ):
        raise ValueError("internal workers and other scientific stages are forbidden")
    required = {"--revision": "execution-r2"}
    if command[1] != "scripts/run_v3_execution.py":
        required["--expected-release"] = RELEASE
    for flag, value in required.items():
        if command.count(flag) != 1 or command[
            command.index(flag) + 1 : command.index(flag) + 2
        ] != [value]:
            raise ValueError("command must bind the exact r2 release/revision")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--acceptance-sha256", required=True)
    parser.add_argument("--helper-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    check_command(command)
    if (
        sys.platform != "linux"
        or not os.environ.get("JOB_ID", "").isdecimal()
        or int(os.environ["JOB_ID"]) < 1
        or os.environ.get("NSLOTS") != "4"
        or not os.environ.get("TMPDIR")
        or not Path(os.environ["TMPDIR"]).is_dir()
        or sys.flags.optimize
        or args.remaining_peak_bytes < 0
    ):
        raise ValueError("gate requires an allocation and nonnegative storage bound")
    helper_path = Path(__file__).with_name("runtime_preflight.py")
    from pose_embed.dataset_seal import canonical_artifact_root
    from pose_embed.motionbert_inputs import REPOSITORY, require_clean_repository
    from pose_embed.provenance import (
        require_path_within,
        sha256_file,
        write_immutable_json,
    )

    root = canonical_artifact_root()
    output = require_path_within(
        args.output, root / "study-v3/operations", label="runtime receipt"
    )
    if output.exists():
        raise ValueError("runtime gate receipt already exists")
    record = {
        "status": "failed",
        "started_at": datetime.now(UTC).isoformat(),
        "job_id": os.environ["JOB_ID"],
        "command": command,
    }
    try:
        if (
            Path.cwd().resolve() != REPOSITORY.resolve()
            or Path(".venv").resolve() != Path(sys.prefix).resolve()
        ):
            raise ValueError(
                "working directory, imported repository and environment differ"
            )
        if command[1] != "scripts/operations/week5_gpu_context_diagnostic.py":
            flag = "--remaining-peak-bytes"
            if command.count(flag) != 1 or command[
                command.index(flag) + 1 : command.index(flag) + 2
            ] != [str(args.remaining_peak_bytes)]:
                raise ValueError(
                    "child monitor storage bound must equal the runtime gate bound"
                )
        if hashlib.sha256(helper_path.read_bytes()).hexdigest() != args.helper_sha256:
            raise ValueError("runtime helper differs from its reviewed bytes")
        helper = load(helper_path, "week5_baseline_runtime")
        helper.require_allocation()
        if Path(command[0]).resolve() != Path(sys.executable).resolve():
            raise ValueError("command interpreter differs from the probed interpreter")
        baseline_path = require_path_within(
            args.baseline, root, label="runtime baseline"
        )
        acceptance_path = require_path_within(
            args.acceptance, root, label="independent baseline acceptance"
        )
        gpu_report_path = require_path_within(
            root / GPU_REPORT, root, label="retained GPU build-report evidence"
        )
        bindings = {
            str(baseline_path): args.baseline_sha256,
            str(acceptance_path): args.acceptance_sha256,
            str(gpu_report_path): GPU_REPORT_SHA,
            str(helper_path): args.helper_sha256,
            str(Path(__file__).resolve()): sha256_file(__file__),
        }
        if command[1] == PARITY_ENTRYPOINT:
            packet = require_path_within(
                command[command.index("--inputs") + 1],
                root / "study-v3/operations",
                label="parity input packet",
            )
            bindings[PARITY_ENTRYPOINT] = PARITY_SHA256
            bindings[str(packet)] = command[command.index("--inputs-sha256") + 1]
        record["bindings"] = bindings
        if require_clean_repository() != RELEASE or any(
            sha256_file(path) != digest for path, digest in bindings.items()
        ):
            raise ValueError("source or runtime-baseline bindings differ")
        baseline = json.loads(baseline_path.read_text())
        if (
            baseline["release_sha"] != RELEASE
            or baseline["runtime_helper_sha256"] != args.helper_sha256
        ):
            raise ValueError("baseline refers to another release or runtime helper")
        acceptance = json.loads(acceptance_path.read_text())
        expected = {
            "schema_version": 1,
            "status": "passed",
            "kind": "independent_metadata_completion_review",
            "job_id": "8457156",
            "execution_revision": "execution-r2",
            "release_sha": RELEASE,
            "runtime_profile": {
                "path": str(baseline_path),
                "sha256": args.baseline_sha256,
            },
            **{
                key: baseline[key]
                for key in (
                    "protocol_sha256",
                    "design_lock_sha256",
                    "amendment_sha256",
                )
            },
        }
        if any(acceptance.get(key) != value for key, value in expected.items()) or set(
            acceptance.get("accepted_scopes", [])
        ) != {
            "prospective_startup_runtime_profile",
            "three_fresh_initializations_per_seed",
            "fixed_panel_identity_and_fallback",
            "two_process_geometry_and_allocated_replay",
            "geometry_job_accounting_resources_and_seals",
        }:
            raise ValueError("independent acceptance does not establish this baseline")
        evidence = acceptance["evidence"]
        for name in (
            "runtime_profile",
            "initializations",
            "fixed_panel_identity",
            "validation",
            "geometry_summary",
            "launch",
        ):
            reference = acceptance[name]
            if evidence.get(reference["path"]) != reference["sha256"]:
                raise ValueError("independent acceptance omits required evidence")
        for path, digest in evidence.items():
            resolved = require_path_within(
                path, root, label="accepted baseline evidence"
            )
            if str(resolved) != path or (path in bindings and bindings[path] != digest):
                raise ValueError("accepted evidence path or hash binding differs")
            bindings[path] = digest
        if any(sha256_file(path) != digest for path, digest in bindings.items()):
            raise ValueError("independently accepted baseline evidence changed")
        record["before"] = helper.capture_profile()
        require_startup_profile(helper, record["before"], baseline["profile"])
        operations = load(
            Path("scripts/run_v3_execution.py"), "week5_frozen_operations"
        )
        record["resources"] = operations.resource_snapshot(
            root, args.remaining_peak_bytes
        )
        if (
            not record["resources"]["storage_passed"]
            or not record["resources"]["host_memory_passed"]
        ):
            raise ValueError("current storage reserve or host RAM is insufficient")
        record["returncode"] = subprocess.run(command, check=False).returncode
        record["after"] = helper.capture_profile()
        helper.require_profile(record["after"], record["before"]["profile"])
        if require_clean_repository() != RELEASE or any(
            sha256_file(path) != digest for path, digest in bindings.items()
        ):
            raise ValueError(
                "source or runtime-baseline bindings changed during operation"
            )
        if record["returncode"]:
            raise ValueError("existing Week 5 command failed")
        record["status"] = "passed"
    except BaseException as error:
        record.update(error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        record["ended_at"] = datetime.now(UTC).isoformat()
        write_immutable_json(output, record)


if __name__ == "__main__":
    main()
