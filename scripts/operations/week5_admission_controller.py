"""Run the reviewed candidate assembler under the frozen SCC resource monitor.

Submit the companion CPU qsub script from the clean, explicitly bound release. This
wrapper does not publish selection authorization. Every child uses the frozen
60-second process-group monitor and cleanup; inputs and failures are retained.
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

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import canonical_artifact_root, dataset_access
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.protocol import current_code_hashes, protocol_digest
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

RELEASE = "731938a157be575ee433d6939876f8ca0b95e459"
ASSEMBLER_SHA256 = "0dafefae1eb7c70495f65a17bd6274ac8523c4c700ee2a7ff85f6d0d79bcf7cf"
REVISION = Path("study-v3/revisions/execution-r1")
EXECUTION_SOURCES = (
    "scripts/operations/week5_admission_controller.py",
    "scripts/operations/week5_admission_assembler.py",
    "scripts/operations/week5_admission.qsub",
    "scripts/run_v3_execution.py",
)
PARAMETER_FILES = (
    "capacity_measurements",
    "capacity_methodology",
    "allocation_calendar",
    "researcher_availability",
    "researcher_confirmation",
)


def execution_binding(expected_release, revision):
    if (
        re.fullmatch(r"[0-9a-f]{40}", expected_release) is None
        or revision not in {"execution-r1", "execution-r2"}
        or (revision == "execution-r1") != (expected_release == RELEASE)
        or require_clean_repository() != expected_release
    ):
        raise ValueError("admission requires its clean full release and revision")
    if revision == "execution-r1":
        return {}
    sources = {name: sha256_file(name) for name in EXECUTION_SOURCES}
    if sha256_file(__file__) != sources[EXECUTION_SOURCES[0]]:
        raise ValueError("successor controller differs from its tracked release")
    return sources


def read(path):
    return json.loads(Path(path).read_text())


def binding(root, path):
    path = require_path_within(path, root, label="admission operational input")
    if not path.is_file():
        raise ValueError("admission input must be an existing canonical-root file")
    return {"relative_path": str(path.relative_to(root)), "sha256": sha256_file(path)}


def candidate_directory(root, attempt, revision="execution-r1"):
    namespace = Path("study-v3/revisions") / revision
    destination = require_path_within(
        root / namespace / "gates/admission" / attempt.name,
        root / namespace,
        label="candidate output",
    )
    if destination.exists():
        raise ValueError("candidate output directory already exists")
    return destination


def validate_cpu_allocation(qstat_xml, qstat_job, *, job_id, hostname):
    jobs = ElementTree.fromstring(qstat_xml).findall(".//job_list")
    jobs = [job for job in jobs if job.findtext("JB_job_number") == job_id]
    if len(jobs) != 1:
        raise ValueError("CPU admission job is absent or ambiguous")
    job = jobs[0]
    host = (job.findtext("queue_name") or "").partition("@")[2]
    if (
        job.get("state") != "running"
        or job.findtext("state") != "r"
        or host.split(".")[0] != hostname.split(".")[0]
        or job.findtext("slots") != "4"
    ):
        raise ValueError("admission requires a running four-slot job on this host")
    hard = re.search(r"^hard resource_list:\s*(.+)$", qstat_job, re.M)
    if hard is None:
        raise ValueError("scheduler hard resource request is missing")
    requested = dict(part.strip().split("=", 1) for part in hard[1].split(","))
    if (
        requested.get("h_rt") not in {"12:00:00", "43200"}
        or requested.get("mem_per_core") not in {"8G", "8.000G", "8192M"}
        or requested.get("gpus", "0") != "0"
    ):
        raise ValueError("admission requires CPU-only 12h and 8G per core")


def input_bindings(
    root,
    source,
    assembler,
    expected_sha,
    remaining_peak,
    *,
    expected_release=RELEASE,
    revision="execution-r1",
    assembler_sha=None,
):
    if sha256_file(assembler) != (assembler_sha or ASSEMBLER_SHA256):
        raise ValueError("assembler differs from its reviewed SHA256")
    if sha256_file(source) != expected_sha:
        raise ValueError("supplied inputs differ from the reviewed SHA256")
    value = read(source)
    if value["release_sha"] != expected_release or (
        revision == "execution-r2" and value.get("execution_revision") != revision
    ):
        raise ValueError("supplied inputs refer to another release")
    capacity = read(value["capacity_measurements"])
    peak = capacity["remaining_peak_bytes"]
    if isinstance(peak, bool) or not isinstance(peak, int) or peak < 0:
        raise ValueError(
            "a concrete nonnegative remaining-storage forecast is required"
        )
    if remaining_peak < peak:
        raise ValueError("monitor cannot understate the candidate's storage forecast")
    files = [source, assembler, *[value[key] for key in PARAMETER_FILES]]
    files += value["seal_evidence"]
    for operation in value["operations"].values():
        directory = Path(operation["directory"])
        files += [
            directory / "attempt.json",
            directory / "outcome.json",
            operation["scheduler_accounting"],
        ]
        diagnostic_binding = directory / "diagnostic-binding.json"
        if diagnostic_binding.is_file():
            receipt = require_path_within(
                root / read(diagnostic_binding)["relative_path"],
                root,
                label="diagnostic receipt",
            )
            files += [diagnostic_binding, receipt]
            files += [
                require_path_within(
                    receipt.parent / relative,
                    receipt.parent,
                    label="diagnostic evidence",
                )
                for relative in read(receipt)["evidence"]
            ]
            for command_path in sorted(
                (directory / "commands").glob("[0-9][0-9][0-9].json")
            ):
                command = read(command_path)["argv"]
                if "--gpu-preflight-output" in command:
                    index = command.index("--gpu-preflight-output")
                    preflight = require_path_within(
                        command[index + 1],
                        directory / "gpu-preflights",
                        label="GPU preflight input",
                    )
                    files += [command_path, preflight]
    return tuple(binding(root, file) for file in files)


def verify_bindings(root, records):
    for record in records:
        if binding(root, root / record["relative_path"]) != record:
            raise ValueError("bound operational input changed during assembly")


def assembler_command(
    assembler,
    inputs,
    output,
    recorded_by,
    *,
    expected_release=RELEASE,
    revision="execution-r1",
):
    command = [
        ".venv/bin/python3.11",
        str(assembler),
        "--inputs",
        str(inputs),
        "--output-dir",
        str(output),
        "--recorded-by",
        recorded_by,
    ]
    if revision != "execution-r1":
        command += ["--expected-release", expected_release, "--revision", revision]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    parser.add_argument("--recorded-by", required=True)
    parser.add_argument("--expected-release", default=RELEASE)
    parser.add_argument(
        "--revision", choices=("execution-r1", "execution-r2"), default="execution-r1"
    )
    args = parser.parse_args()
    if (
        not os.environ.get("JOB_ID", "").isdecimal()
        or not os.environ.get("TMPDIR")
        or os.environ.get("NSLOTS") != "4"
        or args.remaining_peak_bytes < 0
        or re.fullmatch(r"[0-9a-f]{64}", args.inputs_sha256) is None
        or not args.recorded_by.strip()
    ):
        parser.error(
            "valid four-slot scheduler job, input SHA and byte forecast required"
        )
    source_hashes = execution_binding(args.expected_release, args.revision)
    assembler_sha = source_hashes.get(EXECUTION_SOURCES[1], ASSEMBLER_SHA256)
    revision = Path("study-v3/revisions") / args.revision
    repository = Path.cwd().resolve()
    spec = importlib.util.spec_from_file_location(
        "frozen_admission_operations", repository / "scripts/run_v3_execution.py"
    )
    operations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operations)
    signal.signal(signal.SIGTERM, operations.interrupted)
    signal.signal(signal.SIGHUP, operations.interrupted)
    root = canonical_artifact_root()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt = root / "study-v3/operations" / f"{stamp}-{os.environ['JOB_ID']}-admission"
    attempt.mkdir(parents=True, exist_ok=False)
    print(f"V3_OPERATION_ATTEMPT={attempt}", flush=True)
    write_immutable_json(
        attempt / "attempt.json",
        {
            "mode": "admission-candidate",
            "started_at": datetime.now(UTC).isoformat(),
            "release_sha": args.expected_release,
            "execution_revision": args.revision,
            "execution_sources_sha256": source_hashes,
            "launcher_sha256": sha256_file(__file__),
            "frozen_operations_sha256": sha256_file(
                repository / "scripts/run_v3_execution.py"
            ),
            "expected_assembler_sha256": assembler_sha,
            "expected_inputs_sha256": args.inputs_sha256,
            "remaining_peak_bytes": args.remaining_peak_bytes,
            "recorded_by": args.recorded_by,
            "canonical_authorization_written": False,
        },
    )
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with dataset_access():
                operations.require_dataset_unopened(require_registry=True)
                protocol_path = root / revision / "locks/protocol.v3.json"
                protocol = load_protocol(protocol_path)
                require_v3_design(protocol)
                code = current_code_hashes().model_dump()
                canonical = (
                    root / protocol.test_access.selection_authorization_relative_path
                )
                if canonical.exists():
                    raise ValueError("canonical selection authorization already exists")
                output = candidate_directory(root, attempt, args.revision)
                write_immutable_json(
                    attempt / "seal-before.json",
                    {
                        "status": "sealed",
                        "recorded_at": datetime.now(UTC).isoformat(),
                        "protocol_sha256": protocol_digest(protocol),
                        "code_sha256": code,
                        "canonical_authorization_absent": True,
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
                    validate_cpu_allocation(**allocation)
                    source = args.inputs.resolve()
                    assembler = args.assembler.resolve()
                    records = input_bindings(
                        root,
                        source,
                        assembler,
                        args.inputs_sha256,
                        args.remaining_peak_bytes,
                        expected_release=args.expected_release,
                        revision=args.revision,
                        assembler_sha=assembler_sha,
                    )
                    write_immutable_json(
                        attempt / "input-bindings.json",
                        {
                            "files": records,
                            "output_directory": str(output),
                        },
                    )
                    retained_inputs = attempt / "inputs.json"
                    with retained_inputs.open("xb") as stream:
                        stream.write(source.read_bytes())
                    if sha256_file(retained_inputs) != args.inputs_sha256:
                        raise ValueError(
                            "inputs changed while making immutable attempt copy"
                        )
                    snapshot = operations.resource_snapshot(
                        root, args.remaining_peak_bytes
                    )
                    write_immutable_json(attempt / "resources/preflight.json", snapshot)
                    if (
                        not snapshot["storage_passed"]
                        or not snapshot["host_memory_passed"]
                    ):
                        raise ValueError("storage reserve or host RAM is insufficient")
                    commands = [
                        [".venv/bin/python3.11", "scripts/verify_workspace.py"],
                        [
                            ".venv/bin/python3.11",
                            "scripts/fetch_upstreams.py",
                            "--check",
                            "--name",
                            "MotionBERT",
                        ],
                        assembler_command(
                            assembler,
                            retained_inputs,
                            output,
                            args.recorded_by,
                            expected_release=args.expected_release,
                            revision=args.revision,
                        ),
                    ]
                    for index, command in enumerate(commands):
                        verify_bindings(root, records)
                        if (
                            execution_binding(args.expected_release, args.revision)
                            != source_hashes
                        ):
                            raise ValueError("release changed before monitored command")
                        operations.run_command(
                            command,
                            attempt,
                            index,
                            root,
                            args.remaining_peak_bytes,
                            dict(os.environ),
                        )
                    verify_bindings(root, records)
                    completed = read(output / "assembly-outcome.json")
                    candidate = output / "selection-authorization.candidate.json"
                    if (
                        completed["status"] != "passed"
                        or completed["canonical_authorization_written"] is not False
                        or completed["candidate"] != binding(root, candidate)
                        or completed["complete_authorization_validation_seconds"] <= 0
                        or execution_binding(args.expected_release, args.revision)
                        != source_hashes
                        or current_code_hashes().model_dump() != code
                    ):
                        raise ValueError(
                            "candidate assembler completion evidence differs"
                        )
                finally:
                    seal = {"recorded_at": datetime.now(UTC).isoformat()}
                    try:
                        operations.require_dataset_unopened(require_registry=True)
                        if canonical.exists():
                            raise ValueError(
                                "canonical authorization appeared during "
                                "candidate assembly"
                            )
                        seal.update(
                            status="sealed", canonical_authorization_absent=True
                        )
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
                "candidate": binding(root, candidate),
                "complete_authorization_validation_seconds": completed[
                    "complete_authorization_validation_seconds"
                ],
                "canonical_authorization_written": False,
                "validation_proof_statistics": completed.get(
                    "validation_proof_statistics"
                ),
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
                "canonical_authorization_written": False,
            },
        )
        raise


if __name__ == "__main__":
    main()
