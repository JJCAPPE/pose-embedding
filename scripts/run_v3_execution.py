"""Sequential execution-r1 operations with immutable, periodic resource records."""

from __future__ import annotations

import argparse
import fcntl
import os
import shutil
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import canonical_artifact_root, require_dataset_unopened
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.motionbert_reproducibility import parse_project_quota
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import sha256_file, write_immutable_json

REVISION = Path("study-v3/revisions/execution-r1")
METHODS = ("contrastive", "contextual", "supcon")
CONDITIONS = (
    ("coordinate_jitter", "0.01"),
    ("coordinate_jitter", "0.025"),
    ("coordinate_jitter", "0.05"),
    ("joint_mask", "3"),
    ("joint_mask", "6"),
    ("joint_mask", "8"),
    ("frame_mask", "10"),
    ("frame_mask", "25"),
    ("frame_mask", "40"),
)


def rehearsal_command(attempt):
    return [
        "env",
        "-u",
        "POSE_EMBED_DATA_ROOT",
        "-u",
        "POSE_EMBED_ARTIFACT_ROOT",
        ".venv/bin/python",
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-q",
        "tests/unit/test_rehearsal_v3.py",
        "tests/unit/test_final_bindings_v3.py",
        "tests/unit/test_opening_faults_v3.py",
        "tests/unit/test_novel_pipeline_v3.py",
        "tests/unit/test_opening_capacity_v3.py",
        "tests/unit/test_test_access.py",
        "--basetemp",
        str(attempt / "fixture-data"),
        "--junitxml",
        str(attempt / "rehearsal.junit.xml"),
    ]


def corruption_commands(protocol, bundle, caches, pilots, output):
    """Encode each condition once; retain each of the 27 projections and scores."""
    cli = [".venv/bin/pose-embed"]
    shared = ["--protocol-config", str(protocol)]
    query_manifest = bundle / "development/development-queries.jsonl"
    gallery_manifest = bundle / "development/development-gallery.jsonl"
    for method, pilot in zip(METHODS, pilots, strict=True):
        yield cli + [
            "features",
            "apply-head",
            *shared,
            "--input",
            str(caches / "development-gallery.npz"),
            "--output",
            str(output / f"galleries/{method}.npz"),
            "--manifest",
            str(gallery_manifest),
            "--checkpoint",
            str(pilot / "head.pt"),
            "--run-manifest",
            str(pilot / "run-manifest.json"),
        ]
    for family, severity in CONDITIONS:
        stem = f"{family}-{severity}"
        encoded = output / f"encodings/{stem}.npz"
        yield cli + [
            "features",
            "extract",
            *shared,
            "--backend",
            "motionbert",
            "--input",
            str(Path(os.environ["POSE_EMBED_DATA_ROOT"]) / "ntu120_hrnet.pkl"),
            "--manifest-set",
            str(bundle / "manifest-set.json"),
            "--manifest",
            str(query_manifest),
            "--parity-evidence",
            str(caches / "parity.json"),
            "--development-episode",
            str(bundle / "development/development-episode.json"),
            "--role",
            "query_corrupted",
            "--split",
            "development_validation",
            "--corruption-family",
            family,
            "--corruption-severity",
            severity,
            "--device",
            "cuda",
            "--output",
            str(encoded),
        ]
        for method, pilot in zip(METHODS, pilots, strict=True):
            projected = output / f"projections/{method}-{stem}.npz"
            yield cli + [
                "features",
                "apply-head",
                *shared,
                "--input",
                str(encoded),
                "--output",
                str(projected),
                "--manifest",
                str(query_manifest),
                "--checkpoint",
                str(pilot / "head.pt"),
                "--run-manifest",
                str(pilot / "run-manifest.json"),
            ]
            yield cli + [
                "evaluate",
                *shared,
                "--gallery",
                str(output / f"galleries/{method}.npz"),
                "--queries",
                str(projected),
                "--gallery-manifest",
                str(gallery_manifest),
                "--query-manifest",
                str(query_manifest),
                "--mode",
                "engineering",
                "--method",
                method,
                "--seed",
                "7",
                "--condition",
                f"{family}:{severity}",
                "--query-definition",
                "development",
                "--output",
                str(output / f"results/{method}-{stem}.json"),
            ]


def resource_snapshot(root, remaining_peak, *, process_group=None):
    import torch

    quota_text = subprocess.check_output(["pquota", "textconv"], text=True, timeout=30)
    quota = parse_project_quota(quota_text, root)
    record = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "filesystem_free_bytes": shutil.disk_usage(root).free,
        "quota_remaining_bytes": quota["free_bytes"],
        "remaining_peak_bytes": remaining_peak,
        "project_quota_report": quota_text,
        "system_memory": Path("/proc/meminfo").read_text(),
        "process_group_rss_bytes": 0,
    }
    if process_group is not None:
        processes = subprocess.check_output(
            ["ps", "-eo", "pgid=,rss="], text=True, timeout=15
        )
        record["process_group_rss_bytes"] = sum(
            int(rss) * 1024
            for group, rss in (line.split() for line in processes.splitlines())
            if int(group) == process_group
        )
    if shutil.which("nvidia-smi"):
        gpu = subprocess.run(["nvidia-smi"], text=True, capture_output=True, timeout=15)
        record["nvidia_smi"] = gpu.stdout
        record["nvidia_smi_exit_status"] = gpu.returncode
    if torch.cuda.is_initialized():
        free, total = torch.cuda.mem_get_info(0)
        record["allocated_gpu"] = {
            "device": 0,
            "free_bytes": free,
            "total_bytes": total,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        }
        record["gpu_memory_passed"] = process_group is not None or free >= 16 * 2**30
    record["storage_passed"] = min(
        record["filesystem_free_bytes"], quota["free_bytes"]
    ) >= (200 * 2**30 + 1.25 * remaining_peak)
    record["host_memory_limit_bytes"] = int(os.environ["NSLOTS"]) * 8 * 2**30
    available = next(
        int(line.split()[1]) * 1024
        for line in record["system_memory"].splitlines()
        if line.startswith("MemAvailable:")
    )
    record["system_memory_available_bytes"] = available
    record["host_memory_passed"] = record["process_group_rss_bytes"] < record[
        "host_memory_limit_bytes"
    ] and (process_group is not None or available >= record["host_memory_limit_bytes"])
    return record


def stop_process(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_command(command, attempt, index, root, remaining_peak, environment):
    """Never leave a scientific child alive after a monitor failure or cancellation."""
    write_immutable_json(attempt / f"commands/{index:03d}.json", {"argv": command})
    preflight = resource_snapshot(root, remaining_peak)
    write_immutable_json(attempt / f"resources/{index:03d}-preflight.json", preflight)
    if not all(
        preflight.get(key, True)
        for key in ("storage_passed", "host_memory_passed", "gpu_memory_passed")
    ):
        raise RuntimeError(
            "resource reserve or RAM exhausted before launch; attempt retained"
        )
    started = time.perf_counter()
    with (attempt / f"command-{index:03d}.log").open("xb") as log:
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=environment,
            start_new_session=True,
        )
        sample = 0
        outcome = {"status": "failed"}
        try:
            while True:
                snapshot = resource_snapshot(
                    root, remaining_peak, process_group=process.pid
                )
                write_immutable_json(
                    attempt / f"resources/{index:03d}-{sample:04d}.json", snapshot
                )
                if not snapshot["storage_passed"] or not snapshot["host_memory_passed"]:
                    raise RuntimeError(
                        "resource reserve or allocated RAM exhausted; attempt retained"
                    )
                sample += 1
                try:
                    status = process.wait(timeout=60)
                    break
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as error:
            outcome.update(error_type=type(error).__name__, error_message=str(error))
            raise
        finally:
            stop_process(process)
            exit_status = process.poll()
            outcome.update(
                status="passed"
                if exit_status == 0 and "error_type" not in outcome
                else "failed",
                exit_status=exit_status,
                wall_time_seconds=time.perf_counter() - started,
                ended_at=datetime.now(UTC).isoformat(),
            )
            write_immutable_json(
                attempt / f"commands/{index:03d}-outcome.json", outcome
            )
    if status:
        raise RuntimeError(
            f"operation {index} failed with exit status {status}; inspect retained log"
        )


def interrupted(signum, _frame):
    # Turn scheduler TERM/HUP into an exception so child-group cleanup runs.
    raise SystemExit(128 + signum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=(
            "rehearsal",
            "prepare",
            "caches",
            "pilot",
            "geometry",
            "corruptions",
            "timing",
            "validate-caches",
            "validate-pilots",
        ),
    )
    parser.add_argument("--method", choices=METHODS)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--pilot-dirs", type=Path, nargs=3, metavar="PILOT")
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    parser.add_argument("--recorded-by", required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    if not os.environ.get("JOB_ID", "").isdecimal() or not os.environ.get("TMPDIR"):
        parser.error("submit through the scheduler")
    if args.remaining_peak_bytes < 0:
        parser.error("remaining peak bytes cannot be negative")
    if (args.mode == "pilot") != (args.method is not None):
        parser.error("only pilot requires --method")
    needs_cache = args.mode in {
        "pilot",
        "corruptions",
        "timing",
        "validate-caches",
        "validate-pilots",
    }
    if needs_cache != (args.cache_dir is not None):
        parser.error("this mode has a different --cache-dir requirement")
    if (args.mode in {"corruptions", "validate-pilots"}) != (
        args.pilot_dirs is not None
    ):
        parser.error(
            "corruptions/validate-pilots require contrastive, contextual, "
            "supcon directories in that order"
        )
    require_clean_repository()
    root = canonical_artifact_root()
    require_dataset_unopened(require_registry=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt = (
        root / "study-v3/operations" / f"{stamp}-{os.environ['JOB_ID']}-{args.mode}"
    )
    attempt.mkdir(parents=True, exist_ok=False)
    print(f"V3_OPERATION_ATTEMPT={attempt}", flush=True)
    environment = dict(os.environ)
    protocol = root / REVISION / "locks/protocol.v3.json"
    bundle = Path(os.environ["POSE_EMBED_MANIFEST_SET"]).resolve().parent
    cli = [".venv/bin/pose-embed"]
    environment["POSE_EMBED_V3_PROTOCOL"] = str(protocol)
    # Scientific caches/runs must stay inside the revision namespace.
    environment["POSE_EMBED_V3_ATTEMPT"] = str(
        root / REVISION / "attempts" / attempt.name
    )
    if args.cache_dir:
        environment["POSE_EMBED_V3_CACHES"] = str(args.cache_dir.resolve())
    output = (
        attempt / "fixture-data"
        if args.mode == "rehearsal"
        else root / REVISION
        if args.mode == "prepare"
        else root / REVISION / "attempts" / attempt.name
    )
    started = datetime.now(UTC)
    write_immutable_json(
        attempt / "attempt.json",
        {
            "mode": args.mode,
            "started_at": started.isoformat(),
            "arguments": vars(args)
            | {
                "cache_dir": str(args.cache_dir) if args.cache_dir else None,
                "pilot_dirs": [str(p) for p in args.pilot_dirs]
                if args.pilot_dirs
                else None,
            },
            "release_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "launcher_sha256": sha256_file(__file__),
            "output_directory": str(output),
            "scientific_output": None if args.mode == "rehearsal" else str(output),
        },
    )
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            snapshot = resource_snapshot(root, args.remaining_peak_bytes)
            write_immutable_json(attempt / "resources/preflight.json", snapshot)
            if not snapshot["storage_passed"] or not snapshot["host_memory_passed"]:
                raise RuntimeError(
                    "insufficient reserve or host RAM; no scientific command started"
                )
            if args.mode in {"caches", "pilot", "corruptions", "timing"}:
                import torch

                from pose_embed.models.motionbert import (
                    configure_deterministic_inference,
                )

                configure_deterministic_inference()
                if (
                    torch.cuda.device_count() != 1
                    or torch.cuda.get_device_name(0) != "NVIDIA L40S"
                ):
                    raise ValueError(
                        "GPU mode requires exactly one scheduler-visible NVIDIA L40S"
                    )
                free, total = torch.cuda.mem_get_info(0)
                write_immutable_json(
                    attempt / "resources/allocated-gpu.json",
                    {
                        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                        "device": 0,
                        "name": torch.cuda.get_device_name(0),
                        "free_bytes": free,
                        "total_bytes": total,
                        "minimum_free_bytes": 16 * 2**30,
                    },
                )
                if min(free, total) < 16 * 2**30:
                    raise ValueError(
                        "allocated visible GPU has less than 16 GiB available"
                    )
            if args.mode not in {"prepare", "rehearsal"}:
                require_v3_design(load_protocol(protocol))
            require_dataset_unopened(require_registry=True)
            write_immutable_json(
                attempt / "seal-before.json",
                {
                    "status": "sealed",
                    "recorded_at": datetime.now(UTC).isoformat(),
                },
            )
            commands = [
                [".venv/bin/python", "scripts/verify_workspace.py"],
                [
                    ".venv/bin/python",
                    "scripts/fetch_upstreams.py",
                    "--check",
                    "--name",
                    "MotionBERT",
                ],
            ]
            if args.mode == "rehearsal":
                commands += [rehearsal_command(attempt)]
            elif args.mode == "prepare":
                commands += [
                    cli
                    + [
                        "study-v3",
                        "prepare-execution",
                        "--historical-manifest-set",
                        str(bundle / "manifest-set.json"),
                        "--recorded-by",
                        args.recorded_by,
                    ]
                ]
            elif args.mode in {"caches", "pilot"}:
                commands += [
                    ["bash", "scripts/study_v3.qsub", args.mode]
                    + ([args.method] if args.method else [])
                ]
            elif args.mode == "geometry":
                commands += [
                    cli
                    + [
                        "study-v3",
                        "geometry-panel",
                        "--protocol-config",
                        str(protocol),
                        "--manifest-set",
                        str(bundle / "manifest-set.json"),
                        "--output-dir",
                        str(output),
                    ]
                ]
            elif args.mode == "corruptions":
                output.mkdir(parents=True, exist_ok=False)
                commands += list(
                    corruption_commands(
                        protocol, bundle, args.cache_dir, args.pilot_dirs, output
                    )
                )
            elif args.mode == "timing":
                commands += [
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
            else:
                commands += [
                    [
                        ".venv/bin/python",
                        "scripts/validate_v3_execution.py",
                        args.mode.removeprefix("validate-"),
                        "--protocol-config",
                        str(protocol),
                        "--cache-dir",
                        str(args.cache_dir),
                        "--manifest-set",
                        str(bundle / "manifest-set.json"),
                        "--output",
                        str(attempt / "validation.json"),
                    ]
                    + (
                        ["--pilot-dirs", *[str(p) for p in args.pilot_dirs]]
                        if args.pilot_dirs
                        else []
                    )
                ]
            for index, command in enumerate(commands):
                run_command(
                    command,
                    attempt,
                    index,
                    root,
                    args.remaining_peak_bytes,
                    environment,
                )
            require_dataset_unopened(require_registry=True)
            require_clean_repository()
            write_immutable_json(
                attempt / "seal-after.json",
                {
                    "status": "sealed",
                    "recorded_at": datetime.now(UTC).isoformat(),
                },
            )
            write_immutable_json(
                attempt / "outcome.json",
                {
                    "status": "passed",
                    "ended_at": datetime.now(UTC).isoformat(),
                    "output_directory": str(output),
                    "scientific_output": None
                    if args.mode == "rehearsal"
                    else str(output),
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
            },
        )
        raise
    print(f"V3_OPERATION_COMPLETE={attempt}")


if __name__ == "__main__":
    main()
