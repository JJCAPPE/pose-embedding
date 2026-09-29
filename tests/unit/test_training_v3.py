from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from pose_embed.config import ExperimentConfig
from pose_embed.data import ManifestRecord
from pose_embed.features import extract_fixture_features
from pose_embed.provenance import sha256_file
from pose_embed.training.runner import (
    NormalizedLinearHead,
    _embedding_health,
    _require_v3_runtime,
    check_learnable_fixture,
    train_head,
    validate_engineering_pilot,
)


def _config(objective: str = "contrastive") -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {
            "schema_version": 1,
            "name": "small-pilot-fixture",
            "objective": objective,
            "seed": 7,
            "input_dimension": 32,
            "embedding_dimension": 16,
            "epochs": 20,
            "learning_rate": 3e-4,
            "weight_decay": 1e-4,
            "classes_per_batch": 8,
            "samples_per_class": 4,
            "temperature": 0.07,
            "positive_margin": 0.75 if objective == "contextual" else 0.9,
            "negative_margin": 0.6,
            **(
                {
                    "contextual": {
                        "epsilon": 0.05,
                        "straight_through_alpha": 10,
                        "contextual_weight": 0.4,
                        "regularizer_weight": 0.1,
                        "target_mean_similarity": 0.25,
                    }
                }
                if objective == "contextual"
                else {}
            ),
        }
    )


def _cache(
    tmp_path: Path,
    protocol_path: Path,
    name: str,
    actions: list[int],
    role: str,
    setup: int,
) -> tuple[Path, Path]:
    ids = [
        f"S{setup:03d}C001P{index + 1:03d}R001A{action:03d}"
        for index, action in enumerate(actions)
    ]
    poses = tmp_path / f"{name}-poses.npz"
    features = tmp_path / f"{name}.npz"
    manifest = tmp_path / f"{name}.jsonl"
    split = "development_train" if role == "training" else "development_validation"
    rng = np.random.default_rng(setup)
    np.savez(
        poses,
        poses=rng.normal(size=(len(ids), 1, 6, 17, 3)).astype(np.float32),
        labels=actions,
        sample_ids=ids,
    )
    manifest.write_text(
        "\n".join(
            ManifestRecord(sample_id=value, split=split).model_dump_json()
            for value in ids
        )
        + "\n"
    )
    extract_fixture_features(
        poses,
        features,
        protocol_path=protocol_path,
        manifest_path=manifest,
        role=role,
        split=split,
        embedding_dimension=32,
    )
    return features, manifest


def _inputs(tmp_path: Path, protocol_path: Path) -> dict:
    train, manifest = _cache(
        tmp_path,
        protocol_path,
        "train",
        [action for action in [3, 4, 5, 6, 9, 10, 11, 12] for _ in range(4)],
        "training",
        1,
    )
    gallery, gallery_manifest = _cache(
        tmp_path, protocol_path, "gallery", [2, 8], "gallery_clean", 2
    )
    queries, query_manifest = _cache(
        tmp_path, protocol_path, "queries", [2, 8, 2, 8], "query_clean", 3
    )
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(_config().model_dump(mode="json")))
    return {
        "config_path": config,
        "input_path": train,
        "manifest_path": manifest,
        "protocol_path": protocol_path,
        "allow_fixture": True,
        "stage": "engineering_pilot",
        "development_gallery_path": gallery,
        "development_query_path": queries,
        "development_gallery_manifest_path": gallery_manifest,
        "development_query_manifest_path": query_manifest,
    }


def test_pilot_has_full_epoch_evidence_and_remains_selection_ineligible(
    tmp_path, protocol_path
):
    inputs = _inputs(tmp_path, protocol_path)
    root = tmp_path / "pilot"
    summary = train_head(**inputs, output_dir=root)
    assert summary["updates"] == 20
    assert summary["selection_eligible"] is False
    assert summary["final_eligible"] is False
    assert len(summary["diagnostics"]) == 20
    assert set(summary["epoch_records"]) == {
        f"epoch-{epoch:03d}.json" for epoch in [0, 5, 10, 15, 20]
    }
    assert len(list(root.rglob("*.pt"))) == 4
    assert not (root / "epochs/020/head.pt").exists()
    zero = json.loads((root / "epoch-000.json").read_text())
    assert "scores" not in zero and "projections" not in zero
    for epoch in (5, 10, 15, 20):
        record = json.loads((root / f"epoch-{epoch:03d}.json").read_text())
        assert len(record["scores"]["per_query"]) == 4
        assert record["health"]["max_normalization_error"] <= 1e-5
        assert record["health"]["embedding_variance"] > 1e-6
        assert record["selection_eligible"] is False
    assert (
        validate_engineering_pilot(root)["checkpoint_sha256"]
        == summary["checkpoint_sha256"]
    )
    (root / "epochs/005/head.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checkpoint changed"):
        validate_engineering_pilot(root)


def test_pilot_pairing_across_objectives(tmp_path, protocol_path):
    inputs = _inputs(tmp_path, protocol_path)
    summaries = []
    for objective in ("contrastive", "supcon", "contextual"):
        config_path = tmp_path / f"{objective}.yaml"
        config_path.write_text(
            yaml.safe_dump(_config(objective).model_dump(mode="json"))
        )
        summaries.append(
            train_head(
                **{**inputs, "config_path": config_path},
                output_dir=tmp_path / objective,
            )
        )
    assert len({value["initialization_sha256"] for value in summaries}) == 1
    assert len({value["batch_plan_sha256"] for value in summaries}) == 1
    assert len({value["checkpoint_sha256"] for value in summaries}) == 3
    assert all(value["updates"] == 20 for value in summaries)
    assert "reciprocal_counts" in summaries[2]["diagnostics"][0]
    assert "empty_complement_count" in summaries[2]["diagnostics"][0]


@pytest.mark.parametrize(
    "field,value", [("epochs", 19), ("seed", 17), ("learning_rate", 1e-3)]
)
def test_pilot_rejects_changed_fixed_budget(tmp_path, protocol_path, field, value):
    inputs = _inputs(tmp_path, protocol_path)
    config = _config().model_dump(mode="json")
    config[field] = value
    inputs["config_path"].write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="20 epochs, seed 7"):
        train_head(**inputs, output_dir=tmp_path / "bad-pilot")


def test_pilot_rejects_missing_development_cache(tmp_path, protocol_path):
    inputs = _inputs(tmp_path, protocol_path)
    inputs["development_gallery_path"] = None
    with pytest.raises(ValueError, match="requires clean development"):
        train_head(**inputs, output_dir=tmp_path / "bad-pilot")


def test_pilot_failure_preserves_initial_diagnostics_and_attempt(
    tmp_path, protocol_path, monkeypatch
):
    inputs = _inputs(tmp_path, protocol_path)
    root = tmp_path / "failed-pilot"
    original_step = torch.optim.AdamW.step

    def break_step(self, *args, **kwargs):
        result = original_step(self, *args, **kwargs)
        with torch.no_grad():
            self.param_groups[0]["params"][0].fill_(torch.inf)
        return result

    monkeypatch.setattr(torch.optim.AdamW, "step", break_step)
    with pytest.raises(RuntimeError, match="non-finite updated parameters"):
        train_head(**inputs, output_dir=root)
    outcome = json.loads((root / "outcome.json").read_text())
    assert outcome["status"] == "failed"
    assert "epoch-000.json" in outcome["artifacts_written"]
    assert "batch-plan.json" in outcome["artifacts_written"]
    assert (root / "attempt.json").exists()
    assert not (root / "run-manifest.json").exists()
    with pytest.raises(ValueError, match="reuse non-empty"):
        train_head(**inputs, output_dir=root)


def test_health_rejects_zero_vectors_and_total_collapse():
    with pytest.raises(RuntimeError, match="collapse"):
        _embedding_health(torch.ones(6, 4) / 2)
    with pytest.raises(RuntimeError, match="unit-norm"):
        _embedding_health(torch.zeros(6, 4))


def test_head_has_declared_bias_and_parameter_count():
    head = NormalizedLinearHead(8704, 2048)
    assert head.projection.bias is not None
    assert sum(value.numel() for value in head.parameters()) == 17827840
    assert all(value.dtype == torch.float32 for value in head.parameters())


@pytest.mark.parametrize("objective", ["contrastive", "supcon", "contextual"])
def test_constructed_32_row_fixture_memorizes_in_1000_paired_updates(objective):
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        result = check_learnable_fixture(_config(objective))
    finally:
        torch.set_num_threads(previous_threads)
    assert result["updates"] == 1000
    assert result["top1"] == 1.0
    assert result["scientific_use_allowed"] is False


def test_inactive_gradients_are_allowed_but_nonfinite_gradients_fail():
    from pose_embed.training.runner import _gradient_health

    head = NormalizedLinearHead(3, 2)
    for parameter in head.parameters():
        parameter.grad = torch.zeros_like(parameter)
    assert _gradient_health(head) == 0
    head.projection.weight.grad[0, 0] = torch.inf
    with pytest.raises(RuntimeError, match="non-finite or missing gradients"):
        _gradient_health(head)


def test_deterministic_configuration_precedes_provenance_probes(
    tmp_path, protocol_path, monkeypatch
):
    import pose_embed.training.runner as runner
    from pose_embed.models import motionbert

    inputs = _inputs(tmp_path, protocol_path)
    calls = []
    configure = motionbert.configure_deterministic_inference
    capture = runner.capture_provenance

    def configured():
        calls.append("configure")
        configure()

    def captured(**kwargs):
        assert calls and calls[0] == "configure"
        calls.append("provenance")
        return capture(**kwargs)

    monkeypatch.setattr(motionbert, "configure_deterministic_inference", configured)
    monkeypatch.setattr(runner, "capture_provenance", captured)
    train_head(**inputs, output_dir=tmp_path / "pilot")
    assert calls == ["configure", "provenance", "provenance"]


def test_real_legacy_training_cannot_bypass_registry_with_two_new_roots(
    tmp_path, protocol_path, monkeypatch
):
    from types import SimpleNamespace

    import pose_embed.training.runner as runner

    inputs = _inputs(tmp_path, protocol_path)
    # Simulate discovery of a scientific sidecar: authorization must be checked
    # before its feature arrays or cached provenance are consumed.
    monkeypatch.setattr(
        runner,
        "load_feature_sidecar",
        lambda _: SimpleNamespace(scientific_use_allowed=True),
    )
    data = tmp_path / "replacement-data"
    artifacts = tmp_path / "replacement-artifacts"
    data.mkdir()
    artifacts.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(artifacts))
    inputs["stage"] = None
    with pytest.raises(ValueError, match="historical artifact-root registry"):
        train_head(**inputs, output_dir=artifacts / "blocked")
    assert not (artifacts / "blocked").exists()


def test_real_v3_pilot_rejects_dirty_training_code_before_loading_arrays(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    import pose_embed.training.runner as runner

    monkeypatch.delenv("POSE_EMBED_ARTIFACT_ROOT", raising=False)
    monkeypatch.setattr(
        "pose_embed.dataset_seal.require_dataset_unopened", lambda **_: None
    )
    monkeypatch.setattr(
        runner,
        "load_feature_sidecar",
        lambda _: SimpleNamespace(scientific_use_allowed=True),
    )

    def dirty():
        raise ValueError("scientific training requires a clean committed checkout")

    monkeypatch.setattr("pose_embed.motionbert_inputs.require_clean_repository", dirty)
    monkeypatch.setattr(
        runner,
        "validate_feature_artifact",
        lambda *_, **__: pytest.fail("dirty training read scientific features"),
    )
    with pytest.raises(ValueError, match="clean committed"):
        train_head(
            "configs/experiments/v3/contrastive-lr3e-4-seed7.yaml",
            tmp_path / "features.npz",
            tmp_path / "pilot",
            protocol_path="configs/protocol.v3.yaml",
            manifest_path=tmp_path / "manifest.jsonl",
            stage="engineering_pilot",
        )
    assert not (tmp_path / "pilot").exists()


def test_v3_runtime_rejects_unpinned_pytorch(monkeypatch):
    from pose_embed.config import load_protocol

    monkeypatch.setattr(torch, "__version__", "2.8.0")
    with pytest.raises(ValueError, match="pinned Python/Torch/NumPy"):
        _require_v3_runtime(load_protocol("configs/protocol.v3.yaml"))


def test_pilot_validator_rejects_truncated_scores_even_if_all_hashes_are_updated(
    tmp_path, protocol_path
):
    inputs = _inputs(tmp_path, protocol_path)
    root = tmp_path / "pilot"
    train_head(**inputs, output_dir=root)
    record_path = root / "epoch-005.json"
    record = json.loads(record_path.read_text())
    scores = record["scores"]
    scores["per_query"].pop()
    ranks = [row["rank"] for row in scores["per_query"]]
    scores.update(
        query_count=len(ranks),
        top1=sum(rank == 1 for rank in ranks) / len(ranks),
        mrr=sum(1 / rank for rank in ranks) / len(ranks),
        r_at_5=sum(rank <= 5 for rank in ranks) / len(ranks),
    )
    record_path.write_text(json.dumps(record))
    metrics = json.loads((root / "metrics.json").read_text())
    metrics["epoch_records"][record_path.name] = sha256_file(record_path)
    (root / "metrics.json").write_text(json.dumps(metrics))
    manifest = json.loads((root / "run-manifest.json").read_text())
    manifest["epoch_records"] = metrics["epoch_records"]
    manifest["outputs"]["metrics"] = sha256_file(root / "metrics.json")
    manifest["outputs"]["pilot_artifacts"][record_path.name] = sha256_file(record_path)
    (root / "run-manifest.json").write_text(json.dumps(manifest))
    outcome = json.loads((root / "outcome.json").read_text())
    outcome["run_manifest_sha256"] = sha256_file(root / "run-manifest.json")
    outcome["metrics_sha256"] = sha256_file(root / "metrics.json")
    (root / "outcome.json").write_text(json.dumps(outcome))
    with pytest.raises(ValueError, match="complete scores differ"):
        validate_engineering_pilot(root)
