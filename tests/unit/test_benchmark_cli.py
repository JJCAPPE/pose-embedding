"""CLI routing preserves explicit experiment identity and the final-test seal."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import pytest

from pose_embed.benchmark import cli
from pose_embed.benchmark.config import REPOSITORY_ROOT, load_benchmark


def parse(*arguments: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    cli.add_parser(parser.add_subparsers(dest="area", required=True))
    return parser.parse_args(["benchmark", *arguments])


def experiment_arguments(operation: str) -> list[str]:
    return [
        operation,
        "--method",
        "contextual",
        "--seed",
        "7",
        "--manifest-set",
        "/external/manifest-set.json",
        "--parity-evidence",
        "/external/parity.json",
        "--output-dir",
        "/external/benchmark-v2/run",
    ]


def test_coverage_exposes_all_methods_without_granting_test_access() -> None:
    result = cli.run(parse("coverage"))
    assert result["required_method_count"] == len(result["methods"]) == 26
    assert result["implemented_method_count"] == 25
    assert result["blocked_method_count"] == 1
    assert result["required_final_run_count"] == 156
    assert result["priority_methods"] == ["contrastive", "contextual"]
    assert result["paired_seeds"] == [7, 17, 29, 43, 59, 71]
    assert result["final_test_authorized"] is False
    assert all(
        row["blocker"] for row in result["methods"] if row["status"] == "blocked"
    )


def test_coverage_can_be_saved_only_as_immutable_v2_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    path = tmp_path / "benchmark-v2" / "coverage.json"
    cli.run(parse("coverage", "--output", str(path)))
    assert json.loads(path.read_text())["final_test_authorized"] is False
    with pytest.raises(ValueError, match="refusing to overwrite"):
        cli.run(parse("coverage", "--output", str(path)))
    with pytest.raises(ValueError, match="v2 artifacts"):
        cli.run(parse("coverage", "--output", str(tmp_path / "outside.json")))


@pytest.mark.parametrize("operation", ["train", "profile"])
@pytest.mark.parametrize("missing", ["--method", "--seed"])
def test_training_and_profiling_require_explicit_method_and_seed(
    operation: str, missing: str
) -> None:
    arguments = experiment_arguments(operation)
    position = arguments.index(missing)
    del arguments[position : position + 2]
    with pytest.raises(SystemExit) as error:
        parse(*arguments)
    assert error.value.code == 2


def test_profile_routes_three_actual_steps_and_inherits_config_track(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        cli,
        "run_experiment",
        lambda **arguments: calls.append(arguments) or {"profile": True},
    )
    result = cli.run(parse(*experiment_arguments("profile")))
    assert result == {"profile": True}
    assert calls[0]["profile_steps"] == 3
    assert calls[0]["stage"] == "development"
    assert calls[0]["track"] is None
    assert calls[0]["method"] == "contextual"
    assert calls[0]["seed"] == 7


@pytest.mark.parametrize("steps", ["0", "101", "-1"])
def test_profile_rejects_unbounded_or_zero_steps(steps: str) -> None:
    with pytest.raises(SystemExit):
        parse(*experiment_arguments("profile"), "--steps", steps)


def test_final_training_routes_to_runner_gate_without_a_profile_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        cli, "run_experiment", lambda **arguments: calls.append(arguments) or {}
    )
    cli.run(parse(*experiment_arguments("train"), "--phase", "final"))
    assert calls[0]["stage"] == "final"
    assert calls[0]["profile_steps"] is None


def test_blocked_methods_invalid_seeds_and_track_mismatch_never_start_a_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        cli, "run_experiment", lambda **arguments: calls.append(arguments) or {}
    )
    arguments = parse(*experiment_arguments("train"))
    methods = cli.load_methods()
    methods["diml"] = methods["diml"].model_copy(
        update={"status": "blocked", "blocker": "synthetic adapter unavailable"}
    )
    monkeypatch.setattr(cli, "load_methods", lambda: methods)
    arguments.method = "diml"
    with pytest.raises(ValueError, match="blocked"):
        cli.run(arguments)
    arguments.method = "contextual"
    arguments.seed = 999
    with pytest.raises(ValueError, match="six declared"):
        cli.run(arguments)
    arguments.seed = 7
    arguments.track = (
        "finetune" if load_benchmark().training.encoder_mode == "frozen" else "frozen"
    )
    with pytest.raises(ValueError, match="encoder_mode"):
        cli.run(arguments)
    assert calls == []


def test_compare_routes_only_explicit_run_directories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        cli,
        "compare_development",
        lambda paths, output: calls.append((paths, output)) or {"stage": "development"},
    )
    result = cli.run(
        parse(
            "compare", "--runs", "/runs/a", "/runs/b", "--output", "/reports/pair.json"
        )
    )
    assert result == {"stage": "development"}
    assert calls == [(["/runs/a", "/runs/b"], "/reports/pair.json")]


def test_scheduler_script_is_valid_and_refuses_login_node_execution() -> None:
    script = REPOSITORY_ROOT / "scripts/benchmark_v2.qsub"
    checked = subprocess.run(
        ["bash", "-n", str(script)], capture_output=True, text=True, check=False
    )
    assert checked.returncode == 0, checked.stderr
    environment = {key: value for key, value in os.environ.items() if key != "JOB_ID"}
    attempt = subprocess.run(
        ["bash", str(script)],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert attempt.returncode != 0
    assert "Submit this script through Grid Engine" in attempt.stderr


@pytest.mark.parametrize("operation", ["select", "lock-final"])
def test_final_cli_cannot_seal_a_partial_implementation(
    operation, tmp_path, monkeypatch
):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    config = REPOSITORY_ROOT / "configs/benchmark.finetune.v2.yaml"
    with pytest.raises(ValueError, match="not implemented"):
        cli.run(parse(operation, "--config", str(config), "--runs", "/does/not/exist"))
    assert not (tmp_path / "benchmark-v2/locks").exists()


def test_evaluate_cli_runs_the_complete_suite_gate_before_loading_data(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    config = REPOSITORY_ROOT / "configs/benchmark.finetune.v2.yaml"
    with pytest.raises(ValueError, match="not implemented"):
        cli.run(
            parse(
                "evaluate",
                "--config",
                str(config),
                "--run",
                "/does/not/exist",
                "--manifest-set",
                "/missing",
                "--parity-evidence",
                "/missing",
                "--output-dir",
                str(tmp_path / "benchmark-v2/result"),
            )
        )
    assert not (tmp_path / "benchmark-v2/locks").exists()
