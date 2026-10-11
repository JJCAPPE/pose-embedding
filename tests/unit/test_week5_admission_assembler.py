"""Offline assembler checks only: no scientific roots, inputs, or receipts."""

import ast
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def assembler():
    spec = importlib.util.spec_from_file_location(
        "admission_template",
        os.environ.get(
            "POSE_EMBED_TEST_ADMISSION_ASSEMBLER",
            str(Path.cwd() / "scripts/operations/week5_admission_assembler.py"),
        ),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def test_template_requires_actual_measurements_and_named_tests_exist(assembler):
    template = assembler.input_template()
    assert set(template["inputs"]["operations"]) == set(assembler.OPERATION_MODES)
    assert set(template["capacity_payload_fields"]) == assembler.capacity_fields()
    assert all(value is None for value in template["capacity_payload_fields"].values())
    names = {
        node.name
        for file in Path("tests").rglob("test_*.py")
        for node in ast.walk(ast.parse(file.read_text()))
        if isinstance(node, ast.FunctionDef)
    }
    for check, required in assembler.REQUIRED_TESTS.items():
        assert check in assembler.ANALYSIS_CHECKS
        assert set(required) <= names


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "release",
        "launcher",
        "job",
        "exit",
        "failed",
        "preflight",
        "sample",
        "empty_resource",
        "failed_resource",
    ],
)
def test_operation_binds_release_launcher_and_scheduler(assembler, tmp_path, fault):
    path = tmp_path / "study-v3/operations/20261011T120000Z-123-rehearsal"
    save(
        path / "attempt.json",
        {
            "mode": "rehearsal",
            "release_sha": "a" * 40,
            "launcher_sha256": assembler.sha256_file("scripts/run_v3_execution.py"),
            "output_directory": str(path / "fixture-data"),
        },
    )
    save(path / "outcome.json", {"status": "passed"})
    for name in ("seal-before", "seal-after"):
        save(path / f"{name}.json", {"status": "sealed"})
    save(path / "commands/000.json", {"argv": ["fixture-command"]})
    save(
        path / "commands/000-outcome.json",
        {
            "status": "passed",
            "exit_status": 0,
            "wall_time_seconds": 1,
        },
    )
    for name in ("preflight", "000-preflight", "000-0000"):
        save(
            path / f"resources/{name}.json",
            {
                "storage_passed": True,
                "host_memory_passed": True,
            },
        )
    accounting = path / "qacct.txt"
    accounting.write_text("jobnumber 123\nexit_status 0\nfailed 0\n")
    if fault in {"release", "launcher"}:
        record = assembler.read(path / "attempt.json")
        record["release_sha" if fault == "release" else "launcher_sha256"] = "b" * 64
        save(path / "attempt.json", record)
    elif fault in {"preflight", "sample"}:
        (
            path
            / "resources"
            / ("preflight.json" if fault == "preflight" else "000-0000.json")
        ).unlink()
    elif fault in {"empty_resource", "failed_resource"}:
        save(
            path / "resources/000-0000.json",
            {}
            if fault == "empty_resource"
            else {
                "storage_passed": False,
                "host_memory_passed": True,
            },
        )
    elif fault:
        key = {"job": "jobnumber 123", "exit": "exit_status 0", "failed": "failed 0"}[
            fault
        ]
        accounting.write_text(
            accounting.read_text().replace(key, key.split()[0] + " 9")
        )
    record = {"directory": str(path), "scheduler_accounting": str(accounting)}
    if fault:
        with pytest.raises(ValueError):
            assembler.operation(tmp_path, record, "rehearsal", "a" * 40)
    else:
        assert (
            assembler.operation(tmp_path, record, "rehearsal", "a" * 40)["path"] == path
        )


@pytest.mark.parametrize("tag", [None, "failure", "error", "skipped"])
def test_junit_requires_executed_passing_checks(assembler, tmp_path, tag):
    path = tmp_path / "fixture.junit.xml"
    inside = f"<{tag} />" if tag else ""
    path.write_text(
        '<testsuite><testcase name="test_example[param]">'
        f"{inside}</testcase></testsuite>"
    )
    if tag:
        with pytest.raises(ValueError):
            assembler.test_cases(path)
    else:
        assert assembler.test_cases(path) == {"test_example"}


@pytest.mark.parametrize("fault", [None, "cache", "sidecar", "pilot", "fixture"])
def test_independent_receipts_bind_current_artifact_bytes(assembler, tmp_path, fault):
    cache = tmp_path / "cache"
    operations = {"caches": {"output": cache}}
    caches, pilots = {"caches": {}}, {"pilots": {}}
    metadata = save(tmp_path / "manifest-set.json", {"fixture": True})
    caches["manifest_set_sha256"] = pilots["manifest_set_sha256"] = (
        assembler.sha256_file(metadata)
    )
    targets = {}
    for name in assembler.CACHES:
        source = save(cache / f"{name}.npz", {"synthetic": name})
        sidecar = save(assembler.sidecar_path_for(source), {"fixture": name})
        caches["caches"][name] = {
            "artifact_sha256": assembler.sha256_file(source),
            "sidecar_sha256": assembler.sha256_file(sidecar),
        }
        targets.update(cache=source, sidecar=sidecar)
    for method in assembler.METHODS:
        directory = tmp_path / method
        operations[f"pilot_{method}"] = {"output": directory}
        pilots["pilots"][method] = {}
        for key, target in (
            ("run_manifest_sha256", directory / method / "run-manifest.json"),
            ("metrics_sha256", directory / method / "metrics.json"),
            ("fixture_sha256", directory / "learnable-fixture.json"),
        ):
            save(target, {"synthetic": method, "key": key})
            pilots["pilots"][method][key] = assembler.sha256_file(target)
            targets["fixture" if key == "fixture_sha256" else "pilot"] = target
    for name in ("validate_caches", "validate_pilots"):
        command = save(
            tmp_path / name / "command.json",
            {
                "argv": ["--manifest-set", str(metadata)],
            },
        )
        operations[name] = {
            "attempt": {
                "arguments": {
                    "cache_dir": str(cache),
                    "pilot_dirs": [
                        str(tmp_path / method / method) for method in assembler.METHODS
                    ],
                }
            },
            "commands": [command],
        }
    cache_receipt = save(tmp_path / "caches.json", caches)
    pilot_receipt = save(tmp_path / "pilots.json", pilots)
    if fault:
        targets[fault].write_text("changed bytes")
        with pytest.raises(ValueError, match="does not bind"):
            assembler.validate_independent_bindings(
                operations, cache_receipt, pilot_receipt
            )
    else:
        assembler.validate_independent_bindings(
            operations, cache_receipt, pilot_receipt
        )


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "peak_host_bytes",
        "peak_gpu_bytes",
        "host_memory_limit_bytes",
        "gpu_memory_limit_bytes",
    ],
)
def test_capacity_cannot_hide_measured_memory_peaks(assembler, tmp_path, fault):
    path = tmp_path / "operation"
    save(
        path / "resources/000.json",
        {
            "host_memory_limit_bytes": 100,
            "process_group_rss_bytes": 50,
        },
    )
    save(path / "resources/allocated-gpu.json", {"total_bytes": 200})
    references = {"peak_host_memory_bytes": 40, "peak_gpu_reserved_bytes": 150}
    payload = {
        "peak_host_bytes": 50,
        "peak_gpu_bytes": 150,
        "host_memory_limit_bytes": 100,
        "gpu_memory_limit_bytes": 200,
    }
    if fault:
        payload[fault] += -1 if fault.startswith("peak_") else 1
        with pytest.raises(ValueError, match="understates"):
            assembler.validate_memory_capacity(
                payload, references, {"operation": {"path": path}}
            )
    else:
        checked = assembler.validate_memory_capacity(
            payload, references, {"operation": {"path": path}}
        )
        assert checked["observed_peak_host_bytes"] == 50


def test_rejected_preexisting_destination_is_not_modified(
    assembler, tmp_path, monkeypatch
):
    sentinel = tmp_path / "preserved.txt"
    sentinel.write_text("existing evidence")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "assembler",
            "--inputs",
            "unused",
            "--output-dir",
            str(tmp_path),
            "--recorded-by",
            "fixture",
        ],
    )

    def rejected(args):
        raise ValueError("preexisting directory")

    monkeypatch.setattr(assembler, "assemble", rejected)
    with pytest.raises(ValueError, match="preexisting"):
        assembler.main()
    assert list(tmp_path.iterdir()) == [sentinel]


@pytest.mark.parametrize(
    "fault", [None, "script", "source", "config", "per_method", "outcome"]
)
def test_resident_timing_binds_source_attempt_outcome_and_recipes(
    assembler, tmp_path, fault
):
    inputs = [save(tmp_path / f"input-{i}.json", {"fixture": i}) for i in range(5)]
    directory = tmp_path / "timing"
    attempt = {
        "protocol_sha256": "a" * 64,
        "script_sha256": assembler.sha256_file("scripts/time_v3_resident.py"),
        "purpose": "resource_timing_only",
        "selection_eligible": False,
        "final_training_eligible": False,
        "inputs": {str(path): assembler.sha256_file(path) for path in inputs},
    }
    if fault == "script":
        attempt["script_sha256"] = "f" * 64
    attempt_path = save(directory / "attempt.json", attempt)
    methods = []
    for method in assembler.METHODS:
        record = {
            "objective": method,
            "seed": 7,
            "config_sha256": assembler.sha256_file(
                f"configs/experiments/v3/{method}-lr3e-4-seed7.yaml"
            ),
        }
        if fault == "config":
            record["config_sha256"] = "f" * 64
        save(directory / method / "timing.json", record)
        methods.append(record)
    timing_path = save(
        directory / "timing.json",
        {
            "attempt_sha256": assembler.sha256_file(attempt_path),
            "methods": methods,
        },
    )
    save(
        directory / "outcome.json",
        {
            "status": "success",
            "timing_sha256": assembler.sha256_file(timing_path),
        },
    )
    if fault == "source":
        inputs[0].write_text("changed source")
    elif fault == "per_method":
        save(directory / "contextual/timing.json", {"wrong": "record"})
    elif fault == "outcome":
        save(
            directory / "outcome.json", {"status": "failed", "timing_sha256": "f" * 64}
        )
    if fault:
        with pytest.raises(ValueError, match="binding differs"):
            assembler.validate_resident_bindings(directory, inputs, "a" * 64)
    else:
        assembler.validate_resident_bindings(directory, inputs, "a" * 64)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "parent",
        "frozen_source",
        "receipt",
        "evidence",
        "invocation",
        "preflight",
        "command",
        "allocated_gpu",
        "missing_second_preflight",
    ],
)
def test_new_gpu_controller_requires_diagnostic_and_child_preflight_chain(
    assembler, tmp_path, fault
):
    root = tmp_path.resolve()
    path = root / "study-v3/operations/fixture-123-caches"
    diagnostic = root / "study-v3/operations/fixture-122-gpu-diagnostic"
    files = {
        name: save(diagnostic / name, {"fixture": True})
        for name in (
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
        )
    }
    receipt = save(
        diagnostic / "summary.json",
        {
            "kind": "exclusive_process_cuda_diagnostic",
            "status": "passed",
            "scientific_use_allowed": False,
            "parent_cuda_initialized": False,
            "sequential_probe_count": 2,
            "held_context_probe_rejected": True,
            "script_sha256": assembler.GPU_DIAGNOSTIC_SHA256,
            "source_release": "a" * 40,
            "evidence": {
                name: assembler.sha256_file(file) for name, file in files.items()
            },
        },
    )
    binding = assembler.bound(root, receipt)
    save(path / "diagnostic-binding.json", binding.model_dump())
    attempt = {
        "release_sha": "a" * 40,
        "parent_cuda_initialized": False,
        "frozen_operations_sha256": assembler.sha256_file(
            "scripts/run_v3_execution.py"
        ),
        "arguments": {
            "diagnostic_receipt": str(receipt),
            "diagnostic_sha256": binding.sha256,
        },
    }
    outcome = {"parent_cuda_initialized": False}
    preflight = save(
        path / "gpu-preflights/000.json",
        {
            "status": "passed",
            "scientific_use_allowed": False,
            "controller_sha256": assembler.GPU_CONTROLLER_SHA256,
            "job_id": "123",
            "name": "NVIDIA L40S",
            "minimum_free_bytes": 16 * 2**30,
            "free_bytes": 24 * 2**30,
            "total_bytes": 48 * 2**30,
        },
    )
    save(path / "resources/allocated-gpu.json", assembler.read(preflight))
    save(
        path / "commands/000.json",
        {
            "argv": [
                ".venv/bin/python3.11",
                "fixture-controller",
                "--gpu-preflight-output",
                str(preflight),
            ]
        },
    )
    if fault == "parent":
        outcome["parent_cuda_initialized"] = True
    elif fault == "frozen_source":
        attempt["frozen_operations_sha256"] = "b" * 64
    elif fault in {"receipt", "evidence"}:
        (
            receipt if fault == "receipt" else files["held-probe-outcome.json"]
        ).write_text("changed")
    elif fault == "invocation":
        attempt["arguments"]["diagnostic_sha256"] = "b" * 64
    elif fault == "preflight":
        save(preflight, assembler.read(preflight) | {"job_id": "124"})
    elif fault == "command":
        save(path / "commands/000.json", {"argv": ["fixture-command"]})
    elif fault == "missing_second_preflight":
        save(
            path / "commands/002.json",
            {
                "argv": [
                    ".venv/bin/python3.11",
                    "fixture-controller",
                    "--gpu-preflight-output",
                    str(path / "gpu-preflights/002.json"),
                ]
            },
        )
    elif fault == "allocated_gpu":
        save(
            path / "resources/allocated-gpu.json",
            assembler.read(preflight) | {"free_bytes": 23 * 2**30},
        )
    if fault:
        with pytest.raises(ValueError):
            assembler.gpu_controller_evidence(root, path, attempt, outcome)
    else:
        retained = assembler.gpu_controller_evidence(root, path, attempt, outcome)
        assert len(retained) == 13
        assert assembler.bound(root, preflight) in retained
        assert binding in retained
