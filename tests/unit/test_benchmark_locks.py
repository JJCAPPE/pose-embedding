from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import torch

from pose_embed.benchmark import locks
from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.runtime import (
    artifact_root,
    code_digest,
    digest,
    now,
    read_json,
)
from pose_embed.provenance import sha256_file, write_immutable_json


@pytest.fixture
def lock_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    original = load_benchmark()
    config = original.model_copy(
        update={
            "training": original.training.model_copy(
                update={"encoder_mode": "finetune", "steps": 2, "validation_every": 1}
            )
        }
    )
    methods = {
        key: value.model_copy(update={"status": "implemented", "blocker": None})
        for key, value in load_methods().items()
    }
    monkeypatch.setattr(locks, "load_benchmark", lambda _: config)
    monkeypatch.setattr(locks, "load_methods", lambda: methods)
    monkeypatch.setattr(locks, "supports", lambda _: True)

    # Run validation has its own end-to-end tests. Here small, hashed checkpoint
    # states let us exercise all 156 cells without allocating real MotionBERTs.
    def verify_fixture(directory):
        directory = Path(directory)
        manifest = read_json(directory / "run-manifest.json")
        for filename, expected in manifest["outputs"].items():
            if sha256_file(directory / filename) != expected:
                raise ValueError("run evidence changed")
        checkpoint = torch.load(directory / "checkpoint.pt", weights_only=True)
        if any(
            not torch.isfinite(value).all() for value in checkpoint["model"].values()
        ):
            raise ValueError("checkpoint contains invalid parameters")
        return manifest

    monkeypatch.setattr(locks, "verify_run", verify_fixture)
    return config, methods


def _runs(lock_context, stage: str, *, selection=None) -> list[Path]:
    config, methods = lock_context
    directories = []
    timestamp = (
        now()
        if stage == "final"
        else (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    )
    shared_inputs = {
        "manifest_set_sha256": "a" * 64,
        "source_inventory_sha256": "b" * 64,
    }
    current_code = code_digest()
    for method in config.final_methods:
        for seed in config.training.seeds:
            directory = artifact_root() / stage / method / str(seed)
            directory.mkdir(parents=True)
            steps = (
                config.training.steps
                if selection is None
                else selection["methods"][method]["selected_steps"]
            )
            identity = {
                "method": method,
                "method_specification": methods[method].model_dump(mode="json"),
                "seed": seed,
                "stage": stage,
                "track": "finetune",
                "scientific_use_allowed": True,
                "benchmark_sha256": benchmark_digest(config),
                "code_sha256": current_code,
                "configuration": config.model_dump(mode="json"),
                "steps": steps,
                "selection_sha256": None
                if selection is None
                else sha256_file(artifact_root() / "locks/selection.json"),
                "inputs": shared_inputs,
            }
            write_immutable_json(
                directory / "attempt.json",
                {"identity": identity, "started_at": timestamp},
            )
            write_immutable_json(
                directory / "outcome.json",
                {"status": "succeeded", "completed_at": timestamp},
            )
            write_immutable_json(
                directory / "initialization.json",
                {
                    "encoder": digest(["encoder", seed]),
                    "head": digest(["head", seed, methods[method].embedding_dimension]),
                },
            )
            write_immutable_json(
                directory / "batch-plan.json",
                {
                    "sample_ids": ["S001C001P001R001A003"],
                    "steps": [[0]] * steps,
                },
            )
            # Contrastive selects step 2; every other method ties and selects 1.
            history = [
                {
                    "step": step,
                    "validation": {
                        "r_at_1": 0.6 if method == "contrastive" and step == 2 else 0.5
                    },
                }
                for step in range(1, steps + 1)
            ]
            write_immutable_json(directory / "history.json", {"steps": history})
            torch.save(
                {
                    "identity": identity,
                    "selected_step": steps,
                    "model": {"weight": torch.ones(1)},
                    "criterion": {},
                },
                directory / "checkpoint.pt",
            )
            names = [
                "attempt.json",
                "outcome.json",
                "checkpoint.pt",
                "initialization.json",
                "batch-plan.json",
                "history.json",
            ]
            if stage == "development":
                write_immutable_json(
                    directory / "development-result.json",
                    {
                        "identity": identity,
                        "query_order_sha256": "c" * 64,
                        "gallery_order_sha256": "c" * 64,
                        "exclusion_sha256": "d" * 64,
                        "policy": {
                            "exclusion": "self_and_all_synchronized_performance_views"
                        },
                    },
                )
                names.append("development-result.json")
            write_immutable_json(
                directory / "run-manifest.json",
                {
                    "schema_version": 2,
                    "identity": identity,
                    "outputs": {name: sha256_file(directory / name) for name in names},
                    "completed_at": timestamp,
                },
            )
            directories.append(directory)
    return directories


def _change_json(directory: Path, filename: str, mutate) -> None:
    document = read_json(directory / filename)
    mutate(document)
    (directory / filename).write_text(json.dumps(document))
    if filename != "run-manifest.json":
        manifest = read_json(directory / "run-manifest.json")
        manifest["outputs"][filename] = sha256_file(directory / filename)
        (directory / "run-manifest.json").write_text(json.dumps(manifest))


def test_complete_selection_uses_six_seed_means_and_earliest_tie(lock_context) -> None:
    directories = _runs(lock_context, "development")
    selection = locks.create_selection(directories)
    assert len(selection["runs"]) == 156
    assert selection["methods"]["contrastive"]["selected_steps"] == 2
    assert selection["methods"]["contextual"]["selected_steps"] == 1
    assert selection["methods"]["contextual_1536"]["embedding_dimension"] == 1536
    assert locks.validate_selection() == selection
    with pytest.raises(ValueError, match="overwrite"):
        locks.create_selection(directories)


def test_changed_analysis_plan_invalidates_selection(lock_context, monkeypatch):
    selection = locks.create_selection(_runs(lock_context, "development"))
    assert selection["analysis_plan_sha256"] == locks.analysis_plan_sha256()
    monkeypatch.setattr(locks, "analysis_plan_sha256", lambda: "0" * 64)
    with pytest.raises(ValueError, match="selection lock differs"):
        locks.validate_selection()


def test_incomplete_roster_and_blocked_method_cannot_create_selection(
    lock_context, monkeypatch
) -> None:
    directories = _runs(lock_context, "development")
    with pytest.raises(ValueError, match="complete 26-method"):
        locks.create_selection(directories[:-1])
    methods = dict(lock_context[1])
    methods["drml"] = methods["drml"].model_copy(
        update={"status": "blocked", "blocker": "unavailable"}
    )
    monkeypatch.setattr(locks, "load_methods", lambda: methods)
    with pytest.raises(ValueError, match="not implemented"):
        locks.create_selection(directories)
    assert not (artifact_root() / "locks/selection.json").exists()


@pytest.mark.parametrize(
    "change", ["profile", "frozen", "wrong_dimension", "wrong_batch"]
)
def test_unscientific_or_unpaired_runs_are_rejected(lock_context, change: str) -> None:
    directories = _runs(lock_context, "development")
    directory = directories[0]
    if change == "wrong_batch":
        _change_json(
            directory, "batch-plan.json", lambda value: value.update(steps=[[1], [0]])
        )
    else:

        def mutate(value):
            if change == "profile":
                value["identity"]["stage"] = "profile"
            elif change == "frozen":
                value["identity"]["track"] = "frozen"
            else:
                value["identity"]["method_specification"]["embedding_dimension"] = 1536

        _change_json(directory, "run-manifest.json", mutate)
    with pytest.raises(ValueError, match="fine-tuning|paired physical"):
        locks.create_selection(directories)


def test_altered_checkpoint_and_selected_step_fail_revalidation(lock_context) -> None:
    directories = _runs(lock_context, "development")
    locks.create_selection(directories)
    path = artifact_root() / "locks/selection.json"
    selected = read_json(path)
    selected["methods"]["contextual"]["selected_steps"] = 2
    path.write_text(json.dumps(selected))
    with pytest.raises(ValueError, match="selection lock differs"):
        locks.validate_selection()
    (directories[0] / "checkpoint.pt").write_bytes(b"changed checkpoint")
    with pytest.raises(ValueError, match="evidence changed"):
        locks.validate_selection()


def test_final_runs_must_follow_selection_and_match_selected_steps(
    lock_context,
) -> None:
    development = _runs(lock_context, "development")
    selection = locks.create_selection(development)
    final = _runs(lock_context, "final", selection=selection)
    _change_json(
        final[0],
        "attempt.json",
        lambda value: value.update(
            started_at=(datetime.now(UTC) - timedelta(days=1)).isoformat()
        ),
    )
    with pytest.raises(ValueError, match="after selection"):
        locks.lock_final_runs(final)


def test_opening_requires_complete_final_set_and_binds_both_locks(
    lock_context, monkeypatch, tmp_path
) -> None:
    development = _runs(lock_context, "development")
    selection = locks.create_selection(development)
    final = _runs(lock_context, "final", selection=selection)
    with pytest.raises(ValueError, match="complete 26-method"):
        locks.lock_final_runs(final[:-1])
    assert not (artifact_root() / "locks/test-opening.json").exists()
    locked = locks.lock_final_runs(final)
    assert locked["analysis_plan_sha256"] == selection["analysis_plan_sha256"]
    assert locks.validate_final_runs() == locked
    config = lock_context[0]
    monkeypatch.setattr(
        locks,
        "load_episode",
        lambda *args: {
            "metadata": {
                "manifest_set_sha256": "a" * 64,
                "source_inventory_sha256": "b" * 64,
                "parent_protocol_sha256": config.input_protocol_sha256,
                "sample_order_sha256": "f" * 64,
            }
        },
    )
    opening = locks.open_test(manifest_set_path=tmp_path / "manifest-set.json")
    assert opening["analysis_plan_sha256"] == locked["analysis_plan_sha256"]
    assert opening["selection_sha256"] == sha256_file(
        artifact_root() / "locks/selection.json"
    )
    assert opening["final_run_set_sha256"] == sha256_file(
        artifact_root() / "locks/final-runs.json"
    )
    assert locks.open_test(manifest_set_path=tmp_path / "manifest-set.json") == opening
    with pytest.raises(ValueError, match="forbidden after test opening"):
        locks.lock_final_runs(final)
    monkeypatch.setattr(
        locks,
        "load_episode",
        lambda *args: {
            "metadata": {
                "manifest_set_sha256": "0" * 64,
                "source_inventory_sha256": "b" * 64,
                "parent_protocol_sha256": config.input_protocol_sha256,
            }
        },
    )
    with pytest.raises(ValueError, match="novel episode differs"):
        locks.validate_opening(manifest_set_path=tmp_path / "manifest-set.json")


def test_future_selection_timestamp_and_legacy_opening_are_rejected(
    lock_context,
) -> None:
    directories = _runs(lock_context, "development")
    locks.create_selection(directories)
    path = artifact_root() / "locks/selection.json"
    selection = read_json(path)
    selection["created_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps(selection))
    with pytest.raises(ValueError, match="future"):
        locks.validate_selection()
    legacy = artifact_root().parent / "locks/test-opening.v1.json"
    write_immutable_json(legacy, {})
    with pytest.raises(ValueError, match="forbidden after test opening"):
        locks.create_selection(directories)
