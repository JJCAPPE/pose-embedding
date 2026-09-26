from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from pose_embed.benchmark import runner, runtime
from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.data.manifest import ManifestRecord
from pose_embed.provenance import sha256_file


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 4)
        self.head = nn.Linear(4, 3)
        self.dropout = nn.Dropout(0.2)

    def get_representation(self, poses):
        return self.dropout(self.linear(poses))


@pytest.mark.parametrize("train_encoder", [True, False])
def test_actual_step_updates_head_and_only_requested_encoder(train_encoder):
    torch.manual_seed(7)
    model = MotionRetrievalModel(
        TinyEncoder(),
        representation_dimension=4,
        joints=2,
        embedding_dimension=8,
        train_encoder=train_encoder,
    )
    before = copy.deepcopy(model.state_dict())
    criterion = nn.CosineEmbeddingLoss()

    class Pairs(nn.Module):
        def forward(self, values, labels):
            return criterion(values[:2], values[2:], labels[:2])

    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    value = runner.optimizer_step(
        model,
        Pairs(),
        optimizer,
        torch.randn(4, 2, 3, 2, 3),
        torch.tensor([1, -1, 1, -1]),
    )
    assert np.isfinite(value)
    assert not torch.equal(
        before["head.projection.weight"], model.head.projection.weight
    )
    assert torch.equal(before["encoder.head.weight"], model.encoder.head.weight)
    assert (
        torch.equal(before["encoder.linear.weight"], model.encoder.linear.weight)
        != train_encoder
    )
    assert model.encoder.training == train_encoder
    model.eval()
    model.train()
    assert model.encoder.training == train_encoder
    embeddings = model(torch.randn(4, 2, 3, 2, 3))
    torch.testing.assert_close(embeddings.norm(dim=-1), torch.ones(4))


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    config = load_benchmark().model_dump()
    config["training"].update(steps=2, validation_every=1, classes_per_batch=2)
    import yaml

    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    records = [
        ManifestRecord(
            sample_id=f"S001C001P{person:03d}R001A{action:03d}",
            split="development_train",
        )
        for action in [1, 2]
        for person in range(1, 5)
    ]
    inputs = SimpleNamespace(
        protocol=object(),
        data_root=tmp_path,
        manifests={
            "development-train.jsonl": records,
            "development-validation.jsonl": records,
        },
        annotations=[
            {"frame_dir": r.sample_id, "index": i} for i, r in enumerate(records)
        ],
    )
    monkeypatch.setattr(runner, "load_motionbert_inputs", lambda *args: inputs)
    monkeypatch.setattr(runner, "verify_motionbert_assets", lambda *args: {})
    monkeypatch.setattr(
        runner, "build_motionbert_bindings", lambda *args: {"fixture": "test"}
    )
    monkeypatch.setattr(runner, "validate_parity_report", lambda *args: {})
    monkeypatch.setattr(
        runner, "protocol_digest", lambda *args: config["input_protocol_sha256"]
    )
    monkeypatch.setattr(
        runner, "load_frozen_encoder", lambda *args: (TinyEncoder(), {})
    )
    monkeypatch.setattr(
        runtime, "_verified_training_records", lambda identity, config: records
    )

    def fixture_model_state(identity, config):
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(identity["seed"])
            encoder = TinyEncoder()
        state = encoder.state_dict()
        dimension = identity["method_specification"]["embedding_dimension"]
        return {
            "initialization_sha256": runtime.state_digest(encoder),
            "unused_head_sha256": runtime._state_digest(
                {key: value for key, value in state.items() if key.startswith("head.")}
            ),
            "model_shapes": {
                **{
                    f"encoder.{key}": tuple(value.shape) for key, value in state.items()
                },
                "head.projection.weight": (dimension, 8),
                "head.projection.bias": (dimension,),
            },
        }

    monkeypatch.setattr(runtime, "_expected_model_state", fixture_model_state)
    real_model = MotionRetrievalModel
    monkeypatch.setattr(
        runner,
        "MotionRetrievalModel",
        lambda encoder, **kwargs: real_model(
            encoder, representation_dimension=4, joints=2, **kwargs
        ),
    )
    monkeypatch.setattr(
        runner,
        "preprocess_annotation",
        lambda annotation, protocol: (
            np.random.default_rng(annotation["index"])
            .normal(size=(2, 3, 2, 3))
            .astype(np.float32)
        ),
    )
    parity = tmp_path / "parity.json"
    parity.write_text("{}")
    return dict(
        config_path=path,
        manifest_set_path=tmp_path / "manifest.json",
        parity_evidence_path=parity,
        seed=7,
        device="cpu",
    )


def test_paired_run_roundtrip_and_changed_evidence_rejected(experiment, tmp_path):
    paths = [
        tmp_path / "benchmark-v2" / method for method in ["contrastive", "contextual"]
    ]
    for method, path in zip(["contrastive", "contextual"], paths, strict=True):
        runner.run_experiment(**experiment, method=method, output_dir=path)
        assert runtime.verify_run(path)["identity"]["stage"] == "development"
    comparison = runner.compare_development(
        paths, tmp_path / "benchmark-v2/paired.json"
    )
    assert len(comparison["paired_effects"]) == 1
    assert comparison["seeds"] == [7]
    with pytest.raises(FileExistsError):
        runner.run_experiment(**experiment, method="contrastive", output_dir=paths[0])
    (paths[0] / "history.json").write_text("{}")
    with pytest.raises(ValueError, match="evidence changed"):
        runtime.verify_run(paths[0])


def test_profile_never_counts_as_scientific_and_opening_prevents_training(
    experiment, tmp_path
):
    path = tmp_path / "benchmark-v2/profile"
    runner.run_experiment(
        **experiment, method="contrastive", output_dir=path, profile_steps=1
    )
    manifest = runtime.verify_run(path)
    assert manifest["identity"]["scientific_use_allowed"] is False
    with pytest.raises(ValueError, match="development runs"):
        runner.compare_development([path], tmp_path / "benchmark-v2/comparison.json")
    ledger = tmp_path / "benchmark-v2/locks/test-opening.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="after test opening"):
        runner.run_experiment(**experiment, method="contrastive", output_dir=path)


def test_failure_is_preserved_without_success_manifest(
    experiment, tmp_path, monkeypatch
):
    path = tmp_path / "benchmark-v2/failure"

    def fail(*args):
        raise RuntimeError("synthetic optimizer failure")

    monkeypatch.setattr(runner, "optimizer_step", fail)
    with pytest.raises(RuntimeError, match="synthetic"):
        runner.run_experiment(**experiment, method="contrastive", output_dir=path)
    assert runtime.read_json(path / "outcome.json")["status"] == "failed"
    assert (path / "attempt.json").exists()
    assert not (path / "run-manifest.json").exists()


def test_track_cannot_override_hash_bound_configuration(experiment, tmp_path):
    with pytest.raises(ValueError, match="encoder_mode"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            track="finetune",
            output_dir=tmp_path / "benchmark-v2/mismatch",
        )


def test_checkpoint_publish_is_immutable_and_path_is_contained(tmp_path, monkeypatch):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="inside"):
        runtime.artifact_path(tmp_path / "outside")
    path = tmp_path / "checkpoint.pt"
    runtime.save_checkpoint(path, {"value": torch.ones(2)})
    with pytest.raises(FileExistsError):
        runtime.save_checkpoint(path, {"value": torch.zeros(2)})
    assert torch.load(path, weights_only=True)["value"].sum() == 2


def _rehash_output(directory, name):
    manifest = runtime.read_json(directory / "run-manifest.json")
    manifest["outputs"][name] = sha256_file(directory / name)
    (directory / "run-manifest.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize("change", ["batch", "labels", "partition"])
def test_rehashed_noncanonical_batches_are_rejected(experiment, tmp_path, change):
    path = tmp_path / "benchmark-v2/batches"
    runner.run_experiment(**experiment, method="contrastive", output_dir=path)
    batch = runtime.read_json(path / "batch-plan.json")
    if change == "batch":
        batch["steps"][0][0] = batch["steps"][0][1]
    elif change == "labels":
        batch["label_mapping"] = {"1": 1, "2": 0}
    else:
        batch["sample_ids"][0] = "S001C001P001R001A120"
    (path / "batch-plan.json").write_text(json.dumps(batch))
    _rehash_output(path, "batch-plan.json")
    with pytest.raises(ValueError, match="batch|action mapping|training partition"):
        runtime.verify_run(path)


@pytest.mark.parametrize("change", ["head_shape", "encoder", "proxy"])
def test_rehashed_invalid_checkpoint_state_is_rejected(experiment, tmp_path, change):
    path = tmp_path / "benchmark-v2/state"
    method = "proxy_anchor" if change == "proxy" else "contrastive"
    runner.run_experiment(**experiment, method=method, output_dir=path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    if change == "head_shape":
        checkpoint["model"]["head.projection.weight"] = torch.ones(1, 8)
        expected = "keys or shapes"
    elif change == "encoder":
        checkpoint["model"]["encoder.linear.weight"][0, 0] += 0.1
        expected = "frozen encoder state changed"
    else:
        checkpoint["criterion"] = {}
        expected = "criterion/proxy"
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(ValueError, match=expected):
        runtime.verify_run(path)
