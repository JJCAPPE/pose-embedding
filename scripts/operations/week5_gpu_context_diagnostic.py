"""Synthetic exclusive-process CUDA check; no models, poses, or scientific results."""

from __future__ import annotations

import argparse
import csv
import fcntl
import importlib.util
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

import torch

from pose_embed.dataset_seal import canonical_artifact_root, dataset_access
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

RELEASE = "731938a157be575ee433d6939876f8ca0b95e459"
EXECUTION_SOURCES = (
    "scripts/operations/week5_gpu_controller.py",
    "scripts/operations/week5_gpu_context_diagnostic.py",
    "scripts/operations/week5_gpu.qsub",
    "scripts/run_v3_execution.py",
)
REMAINING_PEAK_BYTES = 84_000_000_000
GPU_QUERY = [
    "nvidia-smi",
    "--query-gpu=index,uuid,name,compute_mode,memory.free,memory.total",
    "--format=csv,noheader,nounits",
]
PROCESS_QUERY = [
    "nvidia-smi",
    "--query-compute-apps=pid,gpu_uuid,process_name,used_gpu_memory",
    "--format=csv,noheader,nounits",
]


def read(path):
    return json.loads(Path(path).read_text())


def execution_binding(expected_release, revision):
    if (
        re.fullmatch(r"[0-9a-f]{40}", expected_release) is None
        or revision not in {"execution-r1", "execution-r2"}
        or (revision == "execution-r1") != (expected_release == RELEASE)
        or require_clean_repository() != expected_release
    ):
        raise ValueError("diagnostic requires its clean full release and revision")
    if revision == "execution-r1":
        return {}
    sources = {name: sha256_file(name) for name in EXECUTION_SOURCES}
    if sha256_file(__file__) != sources[EXECUTION_SOURCES[1]]:
        raise ValueError("successor diagnostic differs from its tracked release")
    return sources


def resource_record(output, label, operations, root, process_group=None):
    require_cpu_parent()
    record = operations.resource_snapshot(
        root, REMAINING_PEAK_BYTES, process_group=process_group
    )
    write_immutable_json(output / f"resources/{label}.json", record)
    if (
        record.get("storage_passed") is not True
        or record.get("host_memory_passed") is not True
    ):
        raise ValueError("diagnostic storage reserve or host RAM is insufficient")
    require_cpu_parent()


@contextmanager
def sealed_interval(output, operations):
    with dataset_access():
        operations.require_dataset_unopened(require_registry=True)
        write_immutable_json(
            output / "seal-before.json",
            {"status": "sealed", "recorded_at": datetime.now(UTC).isoformat()},
        )
        try:
            yield
        finally:
            record = {"recorded_at": datetime.now(UTC).isoformat(), "status": "failed"}
            try:
                operations.require_dataset_unopened(require_registry=True)
                record["status"] = "sealed"
            finally:
                write_immutable_json(output / "seal-after.json", record)


def snapshot(output, label, operations, root, process_group=None):
    resource_record(output, label, operations, root, process_group)
    record = {"recorded_at": datetime.now(UTC).isoformat(), "parent_pid": os.getpid()}
    for name, command in (
        ("qstat_xml", ["qstat", "-xml"]),
        ("qstat_job", ["qstat", "-j", os.environ["JOB_ID"]]),
        ("gpus", GPU_QUERY),
        ("processes", PROCESS_QUERY),
    ):
        result = subprocess.run(command, text=True, capture_output=True, timeout=30)
        record[name] = {
            "argv": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        write_immutable_json(output / f"snapshots/{label}-{name}.json", record[name])
        if result.returncode:
            raise ValueError(f"diagnostic {name} observation failed")
    write_immutable_json(output / f"snapshots/{label}.json", record)
    return record


def validate_allocation(record, *, job_id, hostname, visible):
    jobs = ElementTree.fromstring(record["qstat_xml"]["stdout"]).findall(".//job_list")
    jobs = [job for job in jobs if job.findtext("JB_job_number") == job_id]
    if len(jobs) != 1:
        raise ValueError("diagnostic job absent or ambiguous")
    job = jobs[0]
    host = (job.findtext("queue_name") or "").partition("@")[2]
    hard = re.search(
        r"^hard resource_list:\s*(.+)$", record["qstat_job"]["stdout"], re.M
    )
    resources = (
        dict(part.strip().split("=", 1) for part in hard[1].split(",")) if hard else {}
    )
    if (
        (job.get("state"), job.findtext("state"), job.findtext("slots"))
        != ("running", "r", "4")
        or host.split(".")[0] != hostname.split(".")[0]
        or resources.get("gpus") != "1"
        or resources.get("gpu_type") != "L40S"
        or resources.get("mem_per_core") not in {"8G", "8.000G", "8192M"}
        or resources.get("gpu_memory") not in {"16G", "16.000G", "16384M"}
    ):
        raise ValueError(
            "diagnostic requires this host's running four-slot L40S allocation"
        )
    if not visible or "," in visible:
        raise ValueError("diagnostic requires exactly one scheduler-visible GPU")
    rows = list(
        csv.reader(record["gpus"]["stdout"].splitlines(), skipinitialspace=True)
    )
    matches = [row for row in rows if visible in {row[0], row[1]}]
    if len(matches) != 1:
        raise ValueError("visible GPU cannot be matched to retained driver evidence")
    index, uuid, name, mode, free, total = matches[0]
    if (
        name != "NVIDIA L40S"
        or mode.replace(" ", "_").lower() != "exclusive_process"
        or min(int(free), int(total)) < 16 * 1024
    ):
        raise ValueError(
            "diagnostic requires an exclusive-process L40S with 16GiB free"
        )
    return {"index": index, "uuid": uuid, "name": name, "compute_mode": mode}


def gpu_pids(record, uuid):
    return {
        int(row[0])
        for row in csv.reader(
            record["processes"]["stdout"].splitlines(), skipinitialspace=True
        )
        if len(row) >= 2 and row[1] == uuid
    }


def busy_rejection(outcome, returncode):
    message = outcome.get("error_message", "").lower()
    return (
        returncode != 0
        and outcome.get("status") == "failed"
        and any(
            text in message
            for text in (
                "busy or unavailable",
                "device is busy",
                "all cuda-capable devices are busy",
                "cudaerrordevicesunavailable",
                "cudaerrordevicealreadyinuse",
            )
        )
    )


def require_cpu_parent():
    if torch.cuda.is_initialized():
        raise ValueError("diagnostic coordinator must never initialize CUDA")


def worker(role, output, *, expected_release=RELEASE, revision="execution-r1"):
    from pose_embed.models.motionbert import configure_deterministic_inference

    result = {
        "role": role,
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "script_sha256": sha256_file(__file__),
        "source_release": expected_release,
        "execution_revision": revision,
        "scientific_use_allowed": False,
    }
    try:
        configure_deterministic_inference()
        if (
            torch.cuda.device_count() != 1
            or torch.cuda.get_device_name(0) != "NVIDIA L40S"
        ):
            raise ValueError("worker requires exactly one visible L40S")
        result["free_bytes"], result["total_bytes"] = torch.cuda.mem_get_info(0)
        tiny = torch.empty(1024, device="cuda", dtype=torch.float32)
        tiny.zero_()
        torch.cuda.synchronize()
        result.update(
            device_name=torch.cuda.get_device_name(0),
            allocated_bytes=torch.cuda.memory_allocated(),
            cuda_initialized=torch.cuda.is_initialized(),
        )
        if role == "holder":
            write_immutable_json(
                output / "holder-ready.json", result | {"status": "ready"}
            )
            if sys.stdin.readline().strip() != "release":
                raise RuntimeError("holder did not receive its coordinator release")
        del tiny
        torch.cuda.synchronize()
        result["status"] = "passed"
    except BaseException as error:
        result.update(
            status="failed", error_type=type(error).__name__, error_message=str(error)
        )
    result["ended_at"] = datetime.now(UTC).isoformat()
    write_immutable_json(output / f"{role}-outcome.json", result)
    return 0 if result["status"] == "passed" else 1


def launch(output, role, *, expected_release=RELEASE, revision="execution-r1"):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        role,
        "--output-dir",
        str(output),
        "--expected-release",
        expected_release,
        "--revision",
        revision,
    ]
    write_immutable_json(output / f"{role}-command.json", {"argv": command})
    with (output / f"{role}.log").open("xb") as log:
        return subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
            env=dict(os.environ),
        )


def run_probe(
    output, role, operations, root, *, expected_release=RELEASE, revision="execution-r1"
):
    process = launch(output, role, expected_release=expected_release, revision=revision)
    try:
        resource_record(output, role + "-running", operations, root, process.pid)
        status = process.wait(timeout=60)
        resource_record(output, role + "-postflight", operations, root)
        result = read(output / f"{role}-outcome.json")
        if result["pid"] != process.pid or result["script_sha256"] != sha256_file(
            __file__
        ):
            raise ValueError("probe process/source binding differs")
        return result, status
    finally:
        operations.stop_process(process)
        if process.stdin:
            process.stdin.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-release", default=RELEASE)
    parser.add_argument(
        "--revision", choices=("execution-r1", "execution-r2"), default="execution-r1"
    )
    parser.add_argument(
        "--worker", choices=("holder", "held-probe", "sequential-1", "sequential-2")
    )
    args = parser.parse_args()
    if (
        not os.environ.get("JOB_ID", "").isdecimal()
        or os.environ.get("NSLOTS") != "4"
        or not os.environ.get("TMPDIR")
    ):
        parser.error("valid four-slot scheduler allocation required")
    require_cpu_parent()
    source_hashes = execution_binding(args.expected_release, args.revision)
    root = canonical_artifact_root()
    output = require_path_within(
        args.output_dir, root / "study-v3/operations", label="synthetic GPU diagnostic"
    )
    if args.worker:
        raise SystemExit(
            worker(
                args.worker,
                output,
                expected_release=args.expected_release,
                revision=args.revision,
            )
        )
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location(
        "frozen_diagnostic_operations", Path.cwd() / "scripts/run_v3_execution.py"
    )
    operations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operations)
    signal.signal(signal.SIGTERM, operations.interrupted)
    signal.signal(signal.SIGHUP, operations.interrupted)
    summary = {
        "kind": "exclusive_process_cuda_diagnostic",
        "status": "failed",
        "scientific_use_allowed": False,
        "source_release": args.expected_release,
        "execution_revision": args.revision,
        "execution_sources_sha256": source_hashes,
        "script_sha256": sha256_file(__file__),
        "job_id": os.environ["JOB_ID"],
        "parent_pid": os.getpid(),
        "parent_cuda_initialized": False,
        "sequential_probe_count": 0,
        "held_context_probe_rejected": False,
        "started_at": datetime.now(UTC).isoformat(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    write_immutable_json(output / "attempt.json", summary)
    holder = None
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with sealed_interval(output, operations):
                before = snapshot(output, "before", operations, root)
                device = validate_allocation(
                    before,
                    job_id=os.environ["JOB_ID"],
                    hostname=socket.gethostname(),
                    visible=os.environ.get("CUDA_VISIBLE_DEVICES"),
                )
                summary.update(device_uuid=device["uuid"], device_name=device["name"])
                if gpu_pids(before, device["uuid"]):
                    raise ValueError(
                        "allocated GPU is occupied; no process interrupted"
                    )
                require_cpu_parent()
                holder = launch(
                    output,
                    "holder",
                    expected_release=args.expected_release,
                    revision=args.revision,
                )
                try:
                    deadline = time.monotonic() + 60
                    ready = output / "holder-ready.json"
                    while not ready.is_file():
                        if holder.poll() is not None or time.monotonic() >= deadline:
                            raise RuntimeError("owned holder failed to become ready")
                        time.sleep(0.05)
                    held = read(ready)
                    if (
                        held["pid"] != holder.pid
                        or held["script_sha256"] != sha256_file(__file__)
                        or held["cuda_initialized"] is not True
                    ):
                        raise ValueError("holder readiness binding differs")
                    during = snapshot(
                        output, "holder-active", operations, root, holder.pid
                    )
                    if gpu_pids(during, device["uuid"]) != {holder.pid}:
                        raise ValueError(
                            "driver evidence does not identify only the owned holder"
                        )
                    require_cpu_parent()
                    rejected, status = run_probe(
                        output,
                        "held-probe",
                        operations,
                        root,
                        expected_release=args.expected_release,
                        revision=args.revision,
                    )
                    if (
                        not busy_rejection(rejected, status)
                        or holder.poll() is not None
                    ):
                        raise ValueError(
                            "concurrent probe did not reproduce context contention"
                        )
                    summary["held_context_probe_rejected"] = True
                    snapshot(output, "held-probe-finished", operations, root)
                    holder.stdin.write("release\n")
                    holder.stdin.flush()
                    if (
                        holder.wait(timeout=30) != 0
                        or read(output / "holder-outcome.json")["status"] != "passed"
                    ):
                        raise ValueError(
                            "owned holder did not release its context cleanly"
                        )
                finally:
                    operations.stop_process(holder)
                    if holder.stdin:
                        holder.stdin.close()
                snapshot(output, "holder-released", operations, root)
                require_cpu_parent()
                for index in (1, 2):
                    result, status = run_probe(
                        output,
                        f"sequential-{index}",
                        operations,
                        root,
                        expected_release=args.expected_release,
                        revision=args.revision,
                    )
                    if (
                        status != 0
                        or result["status"] != "passed"
                        or result["device_name"] != device["name"]
                    ):
                        raise ValueError(
                            "sequential probe did not succeed after holder exit"
                        )
                    summary["sequential_probe_count"] += 1
                    snapshot(output, f"sequential-{index}-finished", operations, root)
                    require_cpu_parent()
                if (
                    execution_binding(args.expected_release, args.revision)
                    != source_hashes
                    or sha256_file(__file__) != summary["script_sha256"]
                ):
                    raise ValueError("release changed during diagnostic")
                summary["status"] = "passed"
    except BaseException as error:
        summary.update(
            status="failed", error_type=type(error).__name__, error_message=str(error)
        )
        raise
    finally:
        summary["parent_cuda_initialized"] = torch.cuda.is_initialized()
        summary["ended_at"] = datetime.now(UTC).isoformat()
        summary["evidence"] = {
            str(path.relative_to(output)): sha256_file(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        }
        write_immutable_json(output / "summary.json", summary)


if __name__ == "__main__":
    main()
