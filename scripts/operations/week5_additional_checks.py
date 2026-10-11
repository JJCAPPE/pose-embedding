"""Allocated, immutable supplementary Week 5 checks; no frozen-source edits.

Run from release 731938a or the explicitly supplied reviewed release. Fixture
tests run with real roots unset; dependence tables read only locked IDs.
Geometry mode uses the existing authorized auxiliary-only geometry command.
Neither mode opens novel poses/outcomes or changes frozen scientific code.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import os
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from pose_embed.config import load_protocol
from pose_embed.data.manifest import load_manifest
from pose_embed.dataset_seal import canonical_artifact_root, dataset_access
from pose_embed.evaluation.analysis import metadata_dependence_table_v3
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.protocol import current_code_hashes, protocol_digest
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

TESTS = (
    "tests/unit/test_analysis_v3.py",
    "tests/unit/test_report_integrity.py",
    "tests/unit/test_execution_revision_v3.py",
    "tests/unit/test_training_integrity.py",
    "tests/unit/test_dataset_seal.py",
    "tests/unit/test_development_projection_replay.py",
    "tests/unit/test_geometry_v3.py",
    "tests/unit/test_engineering_evaluation_v3.py",
)


def geometry_destination(root, protocol_relative_path, attempt):
    permitted = root / Path(protocol_relative_path).parent
    return require_path_within(
        permitted / "geometry" / attempt.name, permitted, label="geometry panel"
    )


def self_check():
    root = Path("/tmp/fixture-only-geometry-destination").resolve()
    relative = "study-v3/revisions/execution-r1/locks/protocol.v3.json"
    attempt = root / "study-v3/operations/example-123-geometry"
    output = geometry_destination(root, relative, attempt)
    assert (
        output == root / "study-v3/revisions/execution-r1/locks/geometry" / attempt.name
    )
    try:
        require_path_within(
            root / "study-v3/revisions/execution-r1/attempts" / attempt.name,
            root / Path(relative).parent,
            label="geometry panel",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("the frozen convenience-launcher path must be rejected")
    print("geometry destination contract: passed (no files or allocations used)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("additional-checks", "geometry"), default="additional-checks"
    )
    parser.add_argument("--expected-release", required=True)
    parser.add_argument("--remaining-peak-bytes", type=int, required=True)
    parser.add_argument("--recorded-by", required=True)
    args = parser.parse_args()
    if (
        not os.environ.get("JOB_ID", "").isdecimal()
        or not os.environ.get("TMPDIR")
        or not os.environ.get("NSLOTS", "").isdecimal()
        or args.remaining_peak_bytes < 0
    ):
        parser.error(
            "valid scheduler allocation and nonnegative byte forecast required"
        )
    release = require_clean_repository()
    if release != args.expected_release:
        raise ValueError("checkout differs from the reviewed release")
    repository = Path.cwd().resolve()
    spec = importlib.util.spec_from_file_location(
        "frozen_v3_operations", repository / "scripts/run_v3_execution.py"
    )
    operations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operations)
    signal.signal(signal.SIGTERM, operations.interrupted)
    signal.signal(signal.SIGHUP, operations.interrupted)
    root = canonical_artifact_root()
    revision = root / "study-v3/revisions/execution-r1"
    protocol_path = revision / "locks/protocol.v3.json"
    protocol = load_protocol(protocol_path)
    design = require_v3_design(protocol)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt = (
        root / "study-v3/operations" / f"{stamp}-{os.environ['JOB_ID']}-{args.mode}"
    )
    attempt.mkdir(parents=True, exist_ok=False)
    metadata_dir = (
        geometry_destination(
            root, protocol.test_access.resolved_protocol_relative_path, attempt
        )
        if args.mode == "geometry"
        else revision / "analysis/metadata-dependence" / attempt.name
    )
    print(f"V3_OPERATION_ATTEMPT={attempt}", flush=True)
    code = current_code_hashes().model_dump()
    write_immutable_json(
        attempt / "attempt.json",
        {
            "mode": args.mode,
            "started_at": datetime.now(UTC).isoformat(),
            "release_sha": release,
            "launcher_sha256": sha256_file(__file__),
            "frozen_operations_sha256": sha256_file(
                repository / "scripts/run_v3_execution.py"
            ),
            "code_sha256": code,
            "recorded_by": args.recorded_by,
            "remaining_peak_bytes": args.remaining_peak_bytes,
            "output_directory": str(metadata_dir),
            "scientific_output": str(metadata_dir) if args.mode == "geometry" else None,
            "tests": {path: sha256_file(repository / path) for path in TESTS}
            if args.mode == "additional-checks"
            else {},
            "fixture_roots_isolated": True
            if args.mode == "additional-checks"
            else None,
        },
    )
    try:
        with (root / "study-v3/operations/execution-r1.operation.lock").open(
            "a"
        ) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with dataset_access():
                operations.require_dataset_unopened(require_registry=True)
                write_immutable_json(
                    attempt / "seal-before.json",
                    {
                        "status": "sealed",
                        "recorded_at": datetime.now(UTC).isoformat(),
                        "protocol_sha256": protocol_digest(protocol),
                        "design_lock_sha256": sha256_file(
                            root / protocol.test_access.design_lock_relative_path
                        ),
                    },
                )
                snapshot = operations.resource_snapshot(root, args.remaining_peak_bytes)
                write_immutable_json(attempt / "resources/preflight.json", snapshot)
                if not snapshot["storage_passed"] or not snapshot["host_memory_passed"]:
                    raise ValueError("insufficient storage reserve or allocated RAM")
                commands = [
                    [".venv/bin/python", "scripts/verify_workspace.py"],
                    [
                        ".venv/bin/python",
                        "scripts/fetch_upstreams.py",
                        "--check",
                        "--name",
                        "MotionBERT",
                    ],
                    [
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
                        *TESTS,
                        "--basetemp",
                        str(attempt / "fixture-data"),
                        "--junitxml",
                        str(attempt / "additional-checks.junit.xml"),
                    ],
                ]
                if args.mode == "geometry":
                    commands[-1] = [
                        ".venv/bin/pose-embed",
                        "study-v3",
                        "geometry-panel",
                        "--protocol-config",
                        str(protocol_path),
                        "--manifest-set",
                        os.environ["POSE_EMBED_MANIFEST_SET"],
                        "--output-dir",
                        str(metadata_dir),
                    ]
                for index, command in enumerate(commands):
                    operations.run_command(
                        command,
                        attempt,
                        index,
                        root,
                        args.remaining_peak_bytes,
                        dict(os.environ),
                    )
                if args.mode == "geometry":
                    from pose_embed.geometry_v3 import validate_geometry_panel

                    validate_geometry_panel(metadata_dir / "summary.json", protocol)
                    validation_details = {
                        "geometry_summary": {
                            "relative_path": str(
                                (metadata_dir / "summary.json").relative_to(root)
                            ),
                            "sha256": sha256_file(metadata_dir / "summary.json"),
                        }
                    }
                else:
                    junit = ElementTree.parse(attempt / "additional-checks.junit.xml")
                    cases = junit.findall(".//testcase")
                    if not cases or any(
                        case.find(tag) is not None
                        for case in cases
                        for tag in ("failure", "error", "skipped")
                    ):
                        raise ValueError(
                            "supplementary checks must all execute and pass"
                        )
                    tables = {}
                    for role, count, actions in (
                        (
                            "development_queries",
                            18929,
                            protocol.dataset.development_validation_actions,
                        ),
                        ("novel_query_primary", 18884, protocol.dataset.novel_actions),
                    ):
                        bound = design.manifests[role]
                        manifest = root / bound.relative_path
                        if sha256_file(manifest) != bound.sha256:
                            raise ValueError("locked metadata manifest changed")
                        ids = tuple(row.sample_id for row in load_manifest(manifest))
                        table = metadata_dependence_table_v3(ids)
                        if (
                            len(ids) != count
                            or len(table) != 20
                            or {row["action"] for row in table} != set(actions)
                            or sum(row["query_count"] for row in table) != count
                        ):
                            raise ValueError(
                                "metadata table has wrong actions or query count"
                            )
                        output = metadata_dir / f"{role}.json"
                        write_immutable_json(output, table)
                        tables[role] = {
                            "relative_path": str(output.relative_to(root)),
                            "sha256": sha256_file(output),
                            "manifest": bound.model_dump(mode="json"),
                            "query_count": count,
                        }
                    validation_details = {
                        "tests_passed": len(cases),
                        "junit_sha256": sha256_file(
                            attempt / "additional-checks.junit.xml"
                        ),
                        "tables": tables,
                    }
                operations.require_dataset_unopened(require_registry=True)
                if (
                    require_clean_repository() != release
                    or current_code_hashes().model_dump() != code
                ):
                    raise ValueError("release changed during the allocated checks")
                write_immutable_json(
                    attempt / "seal-after.json",
                    {"status": "sealed", "recorded_at": datetime.now(UTC).isoformat()},
                )
                write_immutable_json(
                    attempt / "validation.json",
                    {
                        "status": "passed",
                        "release_sha": release,
                        "code_sha256": code,
                        "protocol_sha256": protocol_digest(protocol),
                        **validation_details,
                        "fixture_roots_isolated": True
                        if args.mode == "additional-checks"
                        else None,
                        "novel_pose_or_outcome_access": False,
                    },
                )
        write_immutable_json(
            attempt / "outcome.json",
            {
                "status": "passed",
                "ended_at": datetime.now(UTC).isoformat(),
                "output_directory": str(metadata_dir),
                "scientific_output": str(metadata_dir)
                if args.mode == "geometry"
                else None,
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
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    else:
        main()
