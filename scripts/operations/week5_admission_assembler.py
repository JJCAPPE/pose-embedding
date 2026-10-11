"""Assemble Week 5 receipts from retained evidence; never publish authorization.

Use --input-template to inspect required inputs. Run assembly under the frozen
run_command monitor in an allocated CPU job. The capacity payload must contain
measured values and a documented remaining-work forecast, not copied estimates.
This script verifies typed records, operation accounting, test evidence, exact
metadata tables and all scientific validators. It writes a candidate authorization
for the separate public authorize-selection command, never that canonical lock.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from pose_embed.artifacts import (
    load_feature_sidecar,
    sample_order_digest,
    sidecar_path_for,
)
from pose_embed.config import load_experiment, load_protocol
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.data.manifest import load_manifest
from pose_embed.dataset_seal import (
    REGISTRY,
    canonical_artifact_root,
    dataset_access,
    registered_roots,
    require_dataset_unopened,
)
from pose_embed.evaluation.analysis import metadata_dependence_table_v3
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.motionbert_reproducibility import parse_project_quota
from pose_embed.protocol import current_code_hashes, protocol_digest
from pose_embed.protocol_v3 import V3SelectionAuthorization, require_v3_design
from pose_embed.protocol_v3_campaign import (
    ANALYSIS_CHECKS,
    CONDITIONS,
    GEOMETRY_CHECKS,
    AllocationCalendar,
    AnalysisReceipt,
    CapacityReceipt,
    CorruptionReceipt,
    ResearcherAvailability,
    SealReceipt,
    SelectionMatrix,
    _validate_authorization,
)
from pose_embed.provenance import sha256_file, write_immutable_json

METHODS = ("contrastive", "contextual", "supcon")
CACHES = (
    "final-train-first",
    "final-train-second",
    "development-train",
    "development-gallery",
    "development-queries",
)
SUPPLEMENTAL_WRAPPER_SHA256 = (
    "14b6799627cd506ae5733c5d84e410b0d8656a3dca6b1d0e05c99e7272ede5cc"
)
GPU_CONTROLLER_SHA256 = (
    "cbf13de9bda43b78bef8d3005bf2ccadb225c0daad5bc27b91e9329ee911e7ac"
)
GPU_DIAGNOSTIC_SHA256 = (
    "751259d69fcd24ca6f36439f304bc59640da80ab8b3356092204cf65ea878d73"
)
GPU_MODES = {"caches", "pilot", "corruptions", "timing"}
OPERATION_MODES = {
    "rehearsal": "rehearsal",
    "additional_checks": "additional-checks",
    "prepare": "prepare",
    "caches": "caches",
    "validate_caches": "validate-caches",
    "geometry": "geometry",
    **{f"pilot_{method}": "pilot" for method in METHODS},
    "validate_pilots": "validate-pilots",
    "corruptions": "corruptions",
    "timing": "timing",
}
# These are checks, not a claim that arbitrary passing tests suffice.
REQUIRED_TESTS = {
    "full_command_rehearsal": ("test_complete_v3_cli_fixture_rehearsal",),
    "exact_180_cells": (
        "test_report_marks_complete_only_for_exact_authorized_180_rows",
    ),
    "missing_duplicate_rejection": (
        "test_report_requires_matrix_metadata_and_rejects_duplicate_cells",
    ),
    "ordered_subset_equality": (
        "test_positive_novel_extraction_primary_export_and_archival_validation",
    ),
    "v3_report_dispatch": (
        "test_exact_final_report_writes_analysis_and_source_bound_curve",
    ),
    "unequal_view_bootstrap": (
        "test_v3_bootstrap_keeps_actions_fixed_and_weights_unequal_camera_counts",
    ),
    "interpretation_identity": (
        "test_v3_interpretation_preserves_absolute_accuracy_and_delta_identity",
        "test_v3_zero_crossing_interval_is_inconclusive_not_equivalence",
    ),
    "tamper_revision_rejection": (
        "test_successor_binds_exact_predecessor_science_and_manifest_bytes",
        "test_final_lock_rejects_each_broken_cross_binding",
    ),
    "preloader_authorization": (
        "test_novel_loader_never_deserializes_before_full_opening",
        "test_dirty_novel_loader_fails_before_recording_opening",
    ),
    "concurrent_crashed_opening_recovery": (
        "test_competing_opening_processes_cannot_publish_two_authorizations",
        "test_crash_after_shared_record_only_recovers_identical_authorization",
    ),
    "cross_version_training_denial": (
        "test_training_stops_after_test_opening",
        "test_new_revision_opening_blocks_all_auxiliary_access",
    ),
}


def capacity_fields():
    common = set(AnalysisReceipt.model_fields) - {
        "checks",
        "development_dependence_table",
        "novel_metadata_dependence_table",
    }
    return (
        set(CapacityReceipt.model_fields)
        - common
        - {
            "allocation_calendar",
            "researcher_availability",
            "filesystem_free_bytes",
            "quota_remaining_bytes",
            "retained_bytes",
        }
    )


def input_template():
    return {
        "inputs": {
            "release_sha": "731938a157be575ee433d6939876f8ca0b95e459",
            "operations": {
                name: {
                    "directory": "REQUIRED absolute retained operation path",
                    "scheduler_accounting": "REQUIRED retained qacct text path",
                }
                for name in OPERATION_MODES
            },
            "capacity_measurements": "REQUIRED JSON path; see capacity_payload_fields",
            "capacity_methodology": (
                "REQUIRED JSON/text path: measured-stage mapping, slower-arm forecast, "
                "full validation/replay multiplicities, unslacked remaining jobs, "
                "storage itemization and researcher-work estimates"
            ),
            "allocation_calendar": "REQUIRED absolute typed AllocationCalendar JSON",
            "researcher_availability": "REQUIRED ResearcherAvailability JSON path",
            "researcher_confirmation": "REQUIRED researcher confirmation path",
            "seal_evidence": [
                "REQUIRED fresh local/remote seal audit paths (preserve privacy)"
            ],
        },
        "capacity_payload_fields": {key: None for key in sorted(capacity_fields())},
        "capacity_mapping_notes": {
            "hashing": "independent cache validation.json caches.*.hashing_seconds",
            "loading": (
                "resident timing.json loading_seconds; extraction "
                "source_verification_load additionally includes source loading"
            ),
            "preprocessing": "extraction.stage_seconds.preprocessing in sidecars",
            "encoding": "stage_seconds.encoder; account for pooling in methodology",
            "projection": "apply-head command wall times include input validation",
            "artifact_validation": (
                "independent validation_telemetry.wall_time_seconds and resident "
                "artifact_validation_seconds; pilot CPU replay is included"
            ),
            "retrieval": "evaluate command wall times include checkpoint replay",
            "serialization": (
                "extraction stage_seconds.serialization; projection serialization "
                "is already inside projection wall time"
            ),
            "final_resident_training": (
                "timing.json methods[*].training_seconds; 95001 resident rows, "
                "80 optimization actions"
            ),
            "remaining_forecast": (
                "avoid summing nested durations twice; account for repeated full "
                "campaign validation at every selection/final launch and every "
                "final cache/evaluation/report consumer"
            ),
        },
    }


def read(path):
    return json.loads(Path(path).read_text())


def bound(root, path):
    path = Path(path).resolve()
    if not path.is_file() or not path.is_relative_to(root):
        raise ValueError(f"evidence must be an existing canonical-root file: {path}")
    return ArtifactBinding(
        relative_path=str(path.relative_to(root)), sha256=sha256_file(path)
    )


def gpu_controller_evidence(root, path, attempt, outcome):
    if (
        attempt.get("parent_cuda_initialized") is not False
        or outcome.get("parent_cuda_initialized") is not False
        or attempt.get("frozen_operations_sha256")
        != sha256_file("scripts/run_v3_execution.py")
    ):
        raise ValueError("GPU controller parent/source evidence differs")
    binding = ArtifactBinding.model_validate(read(path / "diagnostic-binding.json"))
    receipt = (root / binding.relative_path).resolve()
    if bound(root, receipt) != binding:
        raise ValueError("GPU diagnostic receipt changed")
    args = attempt["arguments"]
    if (
        Path(args["diagnostic_receipt"]).resolve() != receipt
        or args["diagnostic_sha256"] != binding.sha256
    ):
        raise ValueError("GPU diagnostic differs from controller invocation")
    summary = read(receipt)
    expected = {
        "kind": "exclusive_process_cuda_diagnostic",
        "status": "passed",
        "scientific_use_allowed": False,
        "parent_cuda_initialized": False,
        "sequential_probe_count": 2,
        "held_context_probe_rejected": True,
        "script_sha256": GPU_DIAGNOSTIC_SHA256,
        "source_release": attempt["release_sha"],
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError("GPU diagnostic has not passed the reviewed reproduction")
    evidence = summary.get("evidence")
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
        raise ValueError("GPU diagnostic lacks its observation chain")
    retained = [bound(root, path / "diagnostic-binding.json"), binding]
    for relative, digest in evidence.items():
        observed = (receipt.parent / relative).resolve()
        if (
            not observed.is_relative_to(receipt.parent)
            or bound(root, observed).sha256 != digest
        ):
            raise ValueError("GPU diagnostic evidence changed or escaped")
        retained.append(bound(root, observed))
    preflights = sorted((path / "gpu-preflights").glob("*.json"))
    declared = []
    for command_path in sorted((path / "commands").glob("[0-9][0-9][0-9].json")):
        command = read(command_path)["argv"]
        if len(command) >= 2 and command[-2] == "--gpu-preflight-output":
            expected = path / "gpu-preflights" / f"{command_path.stem}.json"
            if command[-1] != str(expected):
                raise ValueError("GPU preflight command output escaped its own slot")
            declared.append(expected)
    if not preflights or set(preflights) != set(declared):
        raise ValueError("GPU controller lacks its exact preflight output set")
    for preflight in preflights:
        observed = read(preflight)
        command = read(path / f"commands/{preflight.stem}.json")["argv"]
        if (
            observed.get("status") != "passed"
            or observed.get("scientific_use_allowed") is not False
            or observed.get("controller_sha256") != GPU_CONTROLLER_SHA256
            or observed.get("job_id") != path.name.split("-")[-2]
            or observed.get("name") != "NVIDIA L40S"
            or observed.get("minimum_free_bytes") != 16 * 2**30
            or min(observed.get("free_bytes", 0), observed.get("total_bytes", 0))
            < 16 * 2**30
            or command[-2:] != ["--gpu-preflight-output", str(preflight)]
        ):
            raise ValueError("GPU short-lived preflight binding differs")
        retained.append(bound(root, preflight))
    if read(path / "resources/allocated-gpu.json") != read(preflights[0]):
        raise ValueError("allocated GPU evidence differs from its preflight")
    return retained


def operation(root, record, mode, release):
    if set(record) != {"directory", "scheduler_accounting"}:
        raise ValueError("each operation requires directory and scheduler_accounting")
    path = Path(record["directory"]).resolve()
    if not path.is_relative_to(root / "study-v3/operations"):
        raise ValueError("operation is outside its canonical namespace")
    attempt, outcome = read(path / "attempt.json"), read(path / "outcome.json")
    if (
        attempt["mode"] != mode
        or attempt["release_sha"] != release
        or outcome["status"] != "passed"
    ):
        raise ValueError(f"operation mode/release/completion differs: {path}")
    launcher = (
        SUPPLEMENTAL_WRAPPER_SHA256
        if mode in {"additional-checks", "geometry"}
        else sha256_file("scripts/run_v3_execution.py")
    )
    new_gpu_controller = (
        mode in GPU_MODES and attempt["launcher_sha256"] == GPU_CONTROLLER_SHA256
    )
    if attempt["launcher_sha256"] != launcher and not new_gpu_controller:
        raise ValueError("operation launcher differs from its reviewed code")
    controller_evidence = (
        gpu_controller_evidence(root, path, attempt, outcome)
        if new_gpu_controller
        else []
    )
    if any(
        read(path / name)["status"] != "sealed"
        for name in ("seal-before.json", "seal-after.json")
    ):
        raise ValueError("operation lacks intact before/after seals")
    commands = sorted((path / "commands").glob("[0-9][0-9][0-9].json"))
    if not commands:
        raise ValueError("operation lacks preserved command evidence")
    required_resources = [path / "resources/preflight.json"]
    for command in commands:
        finished = read(command.with_name(command.stem + "-outcome.json"))
        if (
            finished["status"] != "passed"
            or finished["exit_status"] != 0
            or finished["wall_time_seconds"] <= 0
        ):
            raise ValueError("operation contains a failed/incomplete command")
        required_resources.append(path / f"resources/{command.stem}-preflight.json")
        samples = sorted(
            (path / "resources").glob(f"{command.stem}-[0-9][0-9][0-9][0-9].json")
        )
        if not samples:
            raise ValueError("operation command lacks periodic resource evidence")
    if mode in {"caches", "pilot", "corruptions", "timing"}:
        required_resources.append(path / "resources/allocated-gpu.json")
    if not all(resource.is_file() for resource in required_resources):
        raise ValueError("operation lacks required preflight/GPU resource evidence")
    for resource in sorted((path / "resources").glob("*.json")):
        values = read(resource)
        if resource.name == "allocated-gpu.json":
            if min(values["free_bytes"], values["total_bytes"]) < 16 * 2**30:
                raise ValueError("operation lacked required free GPU memory")
        elif (
            any(
                values.get(key) is not True
                for key in ("storage_passed", "host_memory_passed")
            )
            or values.get("gpu_memory_passed", True) is not True
        ):
            raise ValueError("operation resource evidence contains a failed check")
    accounting = Path(record["scheduler_accounting"]).resolve()
    bound(root, accounting)
    text = accounting.read_text()
    job = re.search(r"-(\d+)-" + re.escape(mode) + r"$", path.name)
    if (
        not job
        or re.findall(r"^jobnumber\s+(\d+)\s*$", text, re.M) != [job.group(1)]
        or re.findall(r"^exit_status\s+(\d+)\s*$", text, re.M) != ["0"]
        or re.findall(r"^failed\s+(\d+)(?:\s+.*)?$", text, re.M) != ["0"]
    ):
        raise ValueError("scheduler accounting must identify this one successful job")
    output = Path(attempt["output_directory"]).resolve()
    if not output.is_relative_to(root):
        raise ValueError("operation output escapes canonical root")
    return {
        "path": path,
        "output": output,
        "attempt": attempt,
        "outcome": outcome,
        "accounting": accounting,
        "commands": commands,
        "controller_evidence": controller_evidence,
    }


def test_cases(path):
    cases = ElementTree.parse(path).findall(".//testcase")
    if not cases or any(
        case.find(tag) is not None
        for case in cases
        for tag in ("failure", "error", "skipped")
    ):
        raise ValueError("all claimed software checks must execute and pass")
    return {case.attrib["name"].split("[", 1)[0] for case in cases}


def validate_independent_bindings(operations, cache_validation, pilot_validation):
    """A successful independent check must name this exact successor's bytes."""
    cache = operations["caches"]["output"]
    caches, pilots = read(cache_validation), read(pilot_validation)
    if set(caches["caches"]) != set(CACHES) or set(pilots["pilots"]) != set(METHODS):
        raise ValueError("independent validation requires all five caches/three pilots")
    for name in CACHES:
        source = cache / f"{name}.npz"
        if caches["caches"][name]["artifact_sha256"] != sha256_file(source) or caches[
            "caches"
        ][name]["sidecar_sha256"] != sha256_file(sidecar_path_for(source)):
            raise ValueError("independent cache receipt does not bind these caches")
    for method in METHODS:
        directory = operations[f"pilot_{method}"]["output"]
        for key, path in (
            ("run_manifest_sha256", directory / method / "run-manifest.json"),
            ("metrics_sha256", directory / method / "metrics.json"),
            ("fixture_sha256", directory / "learnable-fixture.json"),
        ):
            if pilots["pilots"][method][key] != sha256_file(path):
                raise ValueError("independent pilot receipt does not bind these pilots")
    for mode, receipt in (("validate_caches", caches), ("validate_pilots", pilots)):
        row = operations[mode]
        arguments = row["attempt"]["arguments"]
        if Path(arguments["cache_dir"]).resolve() != cache:
            raise ValueError("independent validation used a different cache directory")
        argv = read(row["commands"][-1])["argv"]
        manifest_set = Path(argv[argv.index("--manifest-set") + 1])
        if receipt["manifest_set_sha256"] != sha256_file(manifest_set):
            raise ValueError("independent validation metadata binding changed")
    recorded_pilots = operations["validate_pilots"]["attempt"]["arguments"][
        "pilot_dirs"
    ]
    if [Path(path).resolve() for path in recorded_pilots] != [
        operations[f"pilot_{method}"]["output"] / method for method in METHODS
    ]:
        raise ValueError("independent validation used different pilot directories")


def validate_memory_capacity(payload, references, operations):
    """Preserve measured worst-case peaks; forecasts cannot lower observations."""
    host, gpu, host_limits, gpu_limits = [], [], [], []

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"peak_host_bytes", "peak_host_memory_bytes"}:
                    host.append(item)
                elif key in {
                    "peak_gpu_memory_bytes",
                    "peak_gpu_allocated_bytes",
                    "peak_gpu_reserved_bytes",
                }:
                    gpu.append(item)
                visit(item)
            if value.get("peak_memory_source") == "process_max_rss":
                host.append(value["peak_memory_bytes"])
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(references)
    for row in operations.values():
        for path in (row["path"] / "resources").glob("*.json"):
            resource = read(path)
            host.append(resource.get("process_group_rss_bytes", 0))
            if "host_memory_limit_bytes" in resource:
                host_limits.append(resource["host_memory_limit_bytes"])
            if path.name == "allocated-gpu.json":
                gpu_limits.append(resource["total_bytes"])
    if not host or not gpu or not host_limits or not gpu_limits:
        raise ValueError("capacity requires retained host/GPU peaks and allocations")
    if (
        payload["peak_host_bytes"] < max(host)
        or payload["peak_gpu_bytes"] < max(gpu)
        or payload["host_memory_limit_bytes"] > min(host_limits)
        or payload["gpu_memory_limit_bytes"] > min(gpu_limits)
    ):
        raise ValueError(
            "capacity understates measured peaks or overstates allocations"
        )
    return {
        "observed_peak_host_bytes": max(host),
        "observed_peak_gpu_bytes": max(gpu),
        "demonstrated_host_memory_limit_bytes": min(host_limits),
        "demonstrated_gpu_memory_limit_bytes": min(gpu_limits),
    }


def validate_resident_bindings(directory, expected_inputs, protocol_sha256):
    """Retain timing attempt, source, configuration and per-arm identity links."""
    attempt_path, timing_path = directory / "attempt.json", directory / "timing.json"
    attempt, timing, outcome = (
        read(attempt_path),
        read(timing_path),
        read(directory / "outcome.json"),
    )
    if (
        timing["attempt_sha256"] != sha256_file(attempt_path)
        or outcome["status"] != "success"
        or outcome["timing_sha256"] != sha256_file(timing_path)
        or attempt["protocol_sha256"] != protocol_sha256
        or attempt["script_sha256"] != sha256_file("scripts/time_v3_resident.py")
        or attempt["purpose"] != "resource_timing_only"
        or attempt["selection_eligible"] is not False
        or attempt["final_training_eligible"] is not False
        or attempt["inputs"]
        != {str(path): sha256_file(path) for path in expected_inputs}
    ):
        raise ValueError("resident timing attempt/outcome/source binding differs")
    methods = {row["objective"]: row for row in timing["methods"]}
    if len(timing["methods"]) != 3 or set(methods) != set(METHODS):
        raise ValueError("resident timing requires exactly three method records")
    for method, record in methods.items():
        if (
            read(directory / method / "timing.json") != record
            or record["seed"] != 7
            or record["config_sha256"]
            != sha256_file(f"configs/experiments/v3/{method}-lr3e-4-seed7.yaml")
        ):
            raise ValueError("resident timing per-method configuration binding differs")


def assemble(args):
    if not os.environ.get("JOB_ID", "").isdecimal() or not os.environ.get("TMPDIR"):
        raise ValueError(
            "run admission assembly inside a monitored scheduler allocation"
        )
    supplied = read(args.inputs)
    required = {
        "release_sha",
        "operations",
        "capacity_measurements",
        "capacity_methodology",
        "allocation_calendar",
        "researcher_availability",
        "researcher_confirmation",
        "seal_evidence",
    }
    if set(supplied) != required:
        raise ValueError(
            f"input fields must be exactly {sorted(required)}; "
            "save only the template's inputs object"
        )
    release = require_clean_repository()
    if release != supplied["release_sha"]:
        raise ValueError("checkout differs from evidence release")
    root = canonical_artifact_root()
    protocol = load_protocol(
        root / "study-v3/revisions/execution-r1/locks/protocol.v3.json"
    )
    design = require_v3_design(protocol)
    destination = Path(args.output_dir).resolve()
    revision = (
        root / protocol.test_access.resolved_protocol_relative_path
    ).parent.parent
    if not destination.is_relative_to(revision) or destination.exists():
        raise ValueError("use a new immutable output directory inside execution-r1")
    destination.mkdir(parents=True)
    args.created_output_dir = True
    started = datetime.now(UTC)
    write_immutable_json(
        destination / "assembly-attempt.json",
        {
            "started_at": started.isoformat(),
            "release_sha": release,
            "script_sha256": sha256_file(__file__),
            "inputs_sha256": sha256_file(args.inputs),
            "canonical_authorization_written": False,
        },
    )
    with dataset_access():
        require_dataset_unopened(require_registry=True)
        if set(supplied["operations"]) != set(OPERATION_MODES):
            raise ValueError("every required distinct operation must be supplied")
        operations = {
            name: operation(root, supplied["operations"][name], mode, release)
            for name, mode in OPERATION_MODES.items()
        }
        if len({row["path"] for row in operations.values()}) != len(operations):
            raise ValueError("operation identities cannot be reused")
        evidence = []
        for row in operations.values():
            evidence.extend(row["controller_evidence"])
            evidence.extend(
                bound(root, row["path"] / name)
                for name in (
                    "attempt.json",
                    "outcome.json",
                    "seal-before.json",
                    "seal-after.json",
                )
            )
            evidence.append(bound(root, row["accounting"]))
            evidence.extend(bound(root, path) for path in row["commands"])
            evidence.extend(
                bound(root, path.with_name(path.stem + "-outcome.json"))
                for path in row["commands"]
            )
            evidence.extend(
                bound(root, path)
                for path in sorted((row["path"] / "resources").glob("*"))
                if path.is_file()
            )
        digest = protocol_digest(protocol)
        design_sha = sha256_file(root / protocol.test_access.design_lock_relative_path)
        code = current_code_hashes().model_dump()

        def common(extra=()):
            return {
                "schema_version": 1,
                "protocol_sha256": digest,
                "design_lock_sha256": design_sha,
                "recorded_at": datetime.now(UTC),
                "recorded_by": args.recorded_by,
                "scientific_use_allowed": True,
                "status": "passed",
                "evidence": tuple([*evidence, *extra]),
                "code_sha256": code,
            }

        rehearsal = operations["rehearsal"]["path"] / "rehearsal.junit.xml"
        extra = operations["additional_checks"]["path"]
        supplemental = extra / "additional-checks.junit.xml"
        names = test_cases(rehearsal) | test_cases(supplemental)
        for check, tests in REQUIRED_TESTS.items():
            if not set(tests) <= names:
                raise ValueError(f"missing executed test evidence for {check}")
        additional = read(extra / "validation.json")
        if (
            additional["status"] != "passed"
            or additional["protocol_sha256"] != digest
            or additional["code_sha256"] != code
            or additional["junit_sha256"] != sha256_file(supplemental)
            or additional["fixture_roots_isolated"] is not True
            or additional["novel_pose_or_outcome_access"] is not False
        ):
            raise ValueError("supplementary analysis evidence changed")
        tables = {}
        for role, count in (
            ("development_queries", 18929),
            ("novel_query_primary", 18884),
        ):
            entry = additional["tables"][role]
            binding = ArtifactBinding.model_validate(
                {key: entry[key] for key in ("relative_path", "sha256")}
            )
            if bound(root, root / binding.relative_path) != binding or entry[
                "manifest"
            ] != design.manifests[role].model_dump(mode="json"):
                raise ValueError("metadata dependence table/source binding changed")
            ids = tuple(
                row.sample_id
                for row in load_manifest(root / design.manifests[role].relative_path)
            )
            table = read(root / binding.relative_path)
            if (
                len(ids) != count
                or len(table) != 20
                or table != metadata_dependence_table_v3(ids)
            ):
                raise ValueError("metadata dependence table does not reproduce")
            tables[role] = binding
        cache_validation = operations["validate_caches"]["path"] / "validation.json"
        pilot_validation = operations["validate_pilots"]["path"] / "validation.json"
        for path, mode in ((cache_validation, "caches"), (pilot_validation, "pilots")):
            value = read(path)
            if (
                value["status"] != "passed"
                or value["mode"] != mode
                or value["protocol_sha256"] != digest
                or value["validation_telemetry"]["wall_time_seconds"] <= 0
            ):
                raise ValueError("independent successor validation is incomplete")
        validate_independent_bindings(operations, cache_validation, pilot_validation)
        analysis = AnalysisReceipt(
            **common(
                tuple(
                    bound(root, p)
                    for p in (
                        rehearsal,
                        supplemental,
                        extra / "validation.json",
                        cache_validation,
                        pilot_validation,
                    )
                )
            ),
            checks={name: True for name in ANALYSIS_CHECKS},
            development_dependence_table=tables["development_queries"],
            novel_metadata_dependence_table=tables["novel_query_primary"],
        )
        write_immutable_json(
            destination / "analysis.json", analysis.model_dump(mode="json")
        )

        geometry = operations["geometry"]["output"] / "summary.json"
        geometry_validation = operations["geometry"]["path"] / "validation.json"
        if read(geometry_validation)["geometry_summary"] != bound(
            root, geometry
        ).model_dump(mode="json"):
            raise ValueError("geometry archive differs from the verified operation")
        if datetime.fromisoformat(
            operations["geometry"]["outcome"]["ended_at"]
        ) > datetime.fromisoformat(operations["corruptions"]["attempt"]["started_at"]):
            raise ValueError("geometry audit must pass before corruption score work")
        corrupted = operations["corruptions"]["output"]
        encodings = {
            condition: bound(
                root, corrupted / "encodings" / (condition.replace(":", "-") + ".npz")
            )
            for condition in CONDITIONS
        }
        results = tuple(
            bound(
                root,
                corrupted / "results" / f"{method}-{condition.replace(':', '-')}.json",
            )
            for method in METHODS
            for condition in CONDITIONS
        )
        query_ids = tuple(
            row.sample_id
            for row in load_manifest(
                root / design.manifests["development_queries"].relative_path
            )
        )
        if len(query_ids) != 18929:
            raise ValueError("development query count changed")
        corruption = CorruptionReceipt(
            **common((bound(root, geometry), bound(root, geometry_validation))),
            query_count=18929,
            query_sample_order_sha256=sample_order_digest(query_ids),
            checks={name: True for name in GEOMETRY_CHECKS},
            encodings=encodings,
            results=results,
            geometry_panel=bound(root, geometry),
        )
        write_immutable_json(
            destination / "corruption.json", corruption.model_dump(mode="json")
        )

        timing = operations["timing"]["output"] / "timing.json"
        resident = read(timing)
        timing_argv = read(operations["timing"]["commands"][-1])["argv"]
        timing_manifest = Path(timing_argv[timing_argv.index("--manifest-set") + 1])
        if (
            sha256_file(timing_manifest)
            != read(cache_validation)["manifest_set_sha256"]
        ):
            raise ValueError("resident timing used different cache metadata")
        validate_resident_bindings(
            timing.parent,
            (
                root / protocol.test_access.resolved_protocol_relative_path,
                timing_manifest,
                operations["caches"]["output"] / "final-train-first.npz",
                root / design.manifests["final_train"].relative_path,
                root / design.manifests["development_train"].relative_path,
            ),
            digest,
        )
        if (
            resident["status"] != "passed"
            or resident["protocol_sha256"] != digest
            or (
                resident["full_size_resident_rows"],
                resident["timing_optimization_actions"],
                resident["optimization_rows"],
            )
            != (95001, 80, 76013)
            or resident["checkpoint_retained"] is not False
        ):
            raise ValueError("resident timing evidence has wrong identity")
        if {row["objective"] for row in resident["methods"]} != set(METHODS) or any(
            row["updates"] != 59380
            or row["epochs"] != 20
            or row["selection_eligible"]
            or row["final_training_eligible"]
            or row["checkpoint_retained"]
            for row in resident["methods"]
        ):
            raise ValueError(
                "resident timing requires all three complete ineligible arms"
            )
        availability = ResearcherAvailability.model_validate_json(
            Path(supplied["researcher_availability"]).read_text()
        )
        calendar = AllocationCalendar.model_validate_json(
            Path(supplied["allocation_calendar"]).read_text()
        )
        if (
            availability.normal_weekly_hours,
            availability.contingency_weekly_hours,
        ) != (5, 10):
            raise ValueError("availability differs from the confirmed 5/10-hour bounds")
        capacity_payload = read(supplied["capacity_measurements"])
        expected_capacity = capacity_fields()
        if set(capacity_payload) != expected_capacity:
            raise ValueError(
                f"capacity_measurements requires exactly {sorted(expected_capacity)}"
            )
        quota_text = subprocess.check_output(
            ["pquota", "textconv"],
            text=True,
            env=os.environ | {"LC_ALL": "C"},
            timeout=30,
        )
        quota_path = destination / "current-project-quota.txt"
        with quota_path.open("x") as stream:
            stream.write(quota_text)
        quota = parse_project_quota(quota_text, root)
        roots = registered_roots(required=True)
        retained = sum(
            path.stat().st_size for path in root.rglob("*") if path.is_file()
        )
        resources = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "filesystem_free_bytes": shutil.disk_usage(root).free,
            "quota_remaining_bytes": quota["free_bytes"],
            "retained_bytes": retained,
            "retained_scope": "all canonical artifact-root files, logical byte size",
            "registered_roots": [str(path) for path in roots],
        }
        write_immutable_json(destination / "current-storage.json", resources)
        supporting = tuple(
            bound(root, path)
            for path in (
                supplied["capacity_measurements"],
                supplied["capacity_methodology"],
                supplied["researcher_confirmation"],
                timing,
                quota_path,
                destination / "current-storage.json",
            )
        )
        supporting += tuple(
            bound(root, path)
            for path in sorted(timing.parent.rglob("*"))
            if path.is_file() and path != timing
        )
        capacity = CapacityReceipt(
            **common(supporting),
            **capacity_payload,
            allocation_calendar=bound(root, supplied["allocation_calendar"]),
            researcher_availability=bound(root, supplied["researcher_availability"]),
            filesystem_free_bytes=resources["filesystem_free_bytes"],
            quota_remaining_bytes=resources["quota_remaining_bytes"],
            retained_bytes=retained,
        )
        if (
            calendar.recorded_at > capacity.recorded_at
            or availability.recorded_at > capacity.recorded_at
        ):
            raise ValueError("capacity inputs have invalid chronology")
        # The metrics have different scopes: the methodology must explain these
        # measured references; do not sum nested inclusive durations as a forecast.
        references = {
            "independent_cache_validation": read(cache_validation),
            "independent_pilot_validation": read(pilot_validation),
            "resident_timing": resident,
            "clean_extractions": {
                name: load_feature_sidecar(
                    operations["caches"]["output"] / f"{name}.npz"
                ).provenance["extraction"]
                for name in CACHES
            },
            "corrupt_extractions": {
                condition: load_feature_sidecar(
                    root / binding.relative_path
                ).provenance["extraction"]
                for condition, binding in encodings.items()
            },
        }
        references["memory_bound_check"] = validate_memory_capacity(
            capacity_payload, references, operations
        )
        write_immutable_json(destination / "measurement-references.json", references)
        capacity = capacity.model_copy(
            update={
                "evidence": (
                    *capacity.evidence,
                    bound(root, destination / "measurement-references.json"),
                )
            }
        )
        write_immutable_json(
            destination / "capacity.json", capacity.model_dump(mode="json")
        )

        require_dataset_unopened(require_registry=True)
        registry_sha = sha256_file(Path(os.environ["POSE_EMBED_DATA_ROOT"]) / REGISTRY)
        if (
            registry_sha != design.artifact_root_registry_sha256
            or not supplied["seal_evidence"]
        ):
            raise ValueError("fresh seal evidence and unchanged registry required")
        write_immutable_json(
            destination / "current-seal.json",
            {
                "status": "sealed",
                "recorded_at": datetime.now(UTC).isoformat(),
                "registered_roots": [str(path) for path in roots],
                "registry_sha256": registry_sha,
            },
        )
        seal = SealReceipt(
            **common(
                tuple(
                    bound(root, p)
                    for p in [
                        *supplied["seal_evidence"],
                        destination / "current-seal.json",
                    ]
                )
            ),
            artifact_root_registry_sha256=registry_sha,
            opening_records_absent=True,
            unresolved_roots=(),
        )
        write_immutable_json(destination / "seal.json", seal.model_dump(mode="json"))
        slots = []
        for source in sorted(Path("configs/experiments/v3").glob("*.yaml")):
            target = destination / "configs" / source.name
            target.parent.mkdir(exist_ok=True)
            with target.open("xb") as stream:
                stream.write(source.read_bytes())
            config = load_experiment(target)
            slots.append(
                {
                    "method": config.objective,
                    "learning_rate": config.learning_rate,
                    "seed": config.seed,
                    "config": bound(root, target),
                }
            )
        matrix = SelectionMatrix(schema_version=1, protocol_sha256=digest, slots=slots)
        write_immutable_json(
            destination / "run-matrix.json", matrix.model_dump(mode="json")
        )
        authorization = V3SelectionAuthorization(
            schema_version=3,
            kind="v3_selection_authorization",
            protocol_sha256=digest,
            design_lock_sha256=design_sha,
            recorded_at=datetime.now(UTC),
            recorded_by=args.recorded_by,
            pilot_records={
                method: bound(
                    root,
                    operations[f"pilot_{method}"]["output"] / method / "metrics.json",
                )
                for method in METHODS
            },
            corruption_verification=bound(root, destination / "corruption.json"),
            analysis_verification=bound(root, destination / "analysis.json"),
            capacity_report=bound(root, destination / "capacity.json"),
            seal_audit=bound(root, destination / "seal.json"),
            run_matrix=bound(root, destination / "run-matrix.json"),
            capacity_passed=True,
            novel_access_authorized=False,
        )
        started_validation = time.perf_counter()
        _validate_authorization(protocol, authorization)
        validation_seconds = time.perf_counter() - started_validation
        if (
            require_clean_repository() != release
            or current_code_hashes().model_dump() != code
        ):
            raise ValueError("release changed during assembly")
        require_dataset_unopened(require_registry=True)
        candidate = destination / "selection-authorization.candidate.json"
        write_immutable_json(candidate, authorization.model_dump(mode="json"))
        write_immutable_json(
            destination / "assembly-outcome.json",
            {
                "status": "passed",
                "ended_at": datetime.now(UTC).isoformat(),
                "complete_authorization_validation_seconds": validation_seconds,
                "candidate": bound(root, candidate).model_dump(),
                "canonical_authorization_written": False,
            },
        )
        print(
            json.dumps(
                {
                    "candidate": str(candidate),
                    "next_command": [
                        ".venv/bin/pose-embed",
                        "study-v3",
                        "authorize-selection",
                        "--protocol-config",
                        str(
                            root / protocol.test_access.resolved_protocol_relative_path
                        ),
                        "--authorization",
                        str(candidate),
                    ],
                }
            )
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--recorded-by", required=True)
    args = parser.parse_args()
    args.created_output_dir = False
    try:
        assemble(args)
    except BaseException as error:
        output = Path(args.output_dir) / "assembly-outcome.json"
        if args.created_output_dir and not output.exists():
            write_immutable_json(
                output,
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
    if sys.argv[1:] == ["--input-template"]:
        print(json.dumps(input_template(), indent=2))
    else:
        main()
