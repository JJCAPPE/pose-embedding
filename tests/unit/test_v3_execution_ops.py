from __future__ import annotations

import importlib.util
import signal
from pathlib import Path
from types import SimpleNamespace

import pytest

from pose_embed.cli import _parser


def load_script(repository_root, name):
    spec = importlib.util.spec_from_file_location(
        name, repository_root / "scripts" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rehearsal_unsets_real_roots_and_retains_fresh_fixtures(
    repository_root, tmp_path
):
    operations = load_script(repository_root, "run_v3_execution")
    command = operations.rehearsal_command(tmp_path)
    assert command[:5] == [
        "env",
        "-u",
        "POSE_EMBED_DATA_ROOT",
        "-u",
        "POSE_EMBED_ARTIFACT_ROOT",
    ]
    assert command[command.index("--basetemp") + 1] == str(tmp_path / "fixture-data")
    assert command[command.index("--junitxml") + 1] == str(
        tmp_path / "rehearsal.junit.xml"
    )
    assert {item for item in command if item.endswith(".py")} == {
        "tests/unit/test_rehearsal_v3.py",
        "tests/unit/test_final_bindings_v3.py",
        "tests/unit/test_opening_faults_v3.py",
        "tests/unit/test_novel_pipeline_v3.py",
        "tests/unit/test_opening_capacity_v3.py",
        "tests/unit/test_test_access.py",
    }


def test_corruptions_encode_nine_times_and_reuse_across_exact_pilot_matrix(
    repository_root, monkeypatch
):
    operations = load_script(repository_root, "run_v3_execution")
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", "/data")
    commands = list(
        operations.corruption_commands(
            Path("protocol"),
            Path("bundle"),
            Path("cache"),
            [Path(method) for method in operations.METHODS],
            Path("output"),
        )
    )
    parsed = [_parser().parse_args(command[1:]) for command in commands]
    encodings = [
        args
        for args in parsed
        if args.area == "features" and args.operation == "extract"
    ]
    projections = [
        args
        for args in parsed
        if args.area == "features" and args.operation == "apply-head"
    ]
    results = [args for args in parsed if args.area == "evaluate"]
    assert len(encodings) == 9
    assert len(projections) == 30  # three clean galleries, 27 corrupted queries
    assert len(results) == 27
    assert {row.condition for row in results} == {
        f"{family}:{severity}" for family, severity in operations.CONDITIONS
    }
    for encoded in encodings:
        consumers = [row for row in projections if row.input == encoded.output]
        assert {Path(row.checkpoint).parent.name for row in consumers} == set(
            operations.METHODS
        )
    assert all(
        row.mode == "engineering"
        and row.seed == 7
        and row.query_definition == "development"
        for row in results
    )
    assert not any("--allow-fixture" in command for command in commands)


def test_timing_maps_training_order_without_exposing_validation_rows(repository_root):
    timing = load_script(repository_root, "time_v3_resident")
    full = [f"sample{action:03d}" for action in (1, 2, 3, 4)]
    assert timing.eligible_indices(full, [full[3], full[0]], {2, 3}) == [3, 0]
    with pytest.raises(ValueError, match="validation or novel"):
        timing.eligible_indices(full, [full[1]], {2})
    with pytest.raises(ValueError, match="duplicates"):
        timing.eligible_indices(full, [full[0], full[0]], set())
    with pytest.raises(ValueError, match="subset"):
        timing.eligible_indices(full, ["other005"], set())


def test_resource_admission_uses_minimum_quota_and_filesystem_and_allocation_rss(
    repository_root, tmp_path, monkeypatch
):
    operations = load_script(repository_root, "run_v3_execution")
    monkeypatch.setenv("NSLOTS", "4")
    monkeypatch.setattr(operations.Path, "read_text", lambda _: "MemAvailable: 999 kB")
    monkeypatch.setattr(operations.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        operations.shutil, "disk_usage", lambda _: SimpleNamespace(free=10**12)
    )

    def output(command, **kwargs):
        if command[0] == "pquota":
            return f"{tmp_path} 1000 0 700 0\n"
        return "123 1024\n456 999999\n123 2048\n"

    monkeypatch.setattr(operations.subprocess, "check_output", output)
    record = operations.resource_snapshot(tmp_path, 20_000_000_000, process_group=123)
    assert record["storage_passed"] is True
    assert record["process_group_rss_bytes"] == 3072 * 1024
    assert record["host_memory_limit_bytes"] == 32 * 2**30
    monkeypatch.setattr(
        operations.shutil, "disk_usage", lambda _: SimpleNamespace(free=220 * 2**30)
    )
    assert (
        operations.resource_snapshot(tmp_path, 20_000_000_000)["storage_passed"]
        is False
    )


def test_monitor_failure_terminates_whole_child_group_and_preserves_evidence(
    repository_root, tmp_path, monkeypatch
):
    operations = load_script(repository_root, "run_v3_execution")
    calls = []
    process = SimpleNamespace(
        pid=123, poll=lambda: None, wait=lambda **kwargs: calls.append("wait")
    )
    monkeypatch.setattr(operations.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(
        operations.os, "killpg", lambda pid, sig: calls.append((pid, sig))
    )
    monkeypatch.setattr(
        operations,
        "resource_snapshot",
        lambda *args, **kwargs: {
            "storage_passed": kwargs.get("process_group") is None,
            "host_memory_passed": True,
        },
    )
    with pytest.raises(RuntimeError, match="resource reserve"):
        operations.run_command(["scientific-command"], tmp_path, 0, tmp_path, 1000, {})
    assert calls == [(123, signal.SIGTERM), "wait"]
    assert (tmp_path / "commands/000.json").is_file()
    assert (tmp_path / "resources/000-0000.json").is_file()
    assert (tmp_path / "command-000.log").is_file()
    assert (tmp_path / "commands/000-outcome.json").is_file()
