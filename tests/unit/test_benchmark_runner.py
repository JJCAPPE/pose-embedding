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
from pose_embed.benchmark.losses import build_loss
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
def test_ibc_uses_one_raw_forward_updates_all_paths_and_retrieves_without_graph(
    train_encoder,
):
    torch.manual_seed(7)
    encoder = TinyEncoder()
    encoder.dropout.p = 0
    model = MotionRetrievalModel(
        encoder,
        representation_dimension=4,
        joints=2,
        embedding_dimension=8,
        train_encoder=train_encoder,
    )
    criterion = build_loss("ibc", {"embedding_dimension": 8, "dropout": 0.0}, 2)
    before = copy.deepcopy(model.state_dict())
    poses, labels = torch.randn(8, 2, 3, 2, 3), torch.arange(2).repeat_interleave(4)
    optimizer = torch.optim.AdamW(
        [*model.parameters(), *criterion.parameters()], lr=0.01
    )
    observed = []
    hook = criterion.loss.auxiliary_classifier.register_forward_pre_hook(
        lambda module, args: observed.append(args[0].detach().clone())
    )
    expected_raw = model.forward_raw(poses).detach().clone()
    encoder_calls = []
    encoder_hook = encoder.linear.register_forward_hook(
        lambda module, args, output: encoder_calls.append(True)
    )
    runner.optimizer_step(model, criterion, optimizer, poses, labels)
    hook.remove()
    encoder_hook.remove()
    assert len(encoder_calls) == 1
    assert len(observed) == 1
    torch.testing.assert_close(observed[0], expected_raw)
    assert not torch.equal(
        before["head.projection.weight"], model.head.projection.weight
    )
    assert (
        torch.equal(before["encoder.linear.weight"], encoder.linear.weight)
        != train_encoder
    )
    model.eval()
    embeddings = model(poses)
    torch.testing.assert_close(
        embeddings, torch.nn.functional.normalize(model.forward_raw(poses), dim=-1)
    )
    # Retrieval does not use criterion BatchNorm or messages from companion clips.
    torch.testing.assert_close(embeddings[:1], model(poses[:1]), atol=1e-6, rtol=1e-5)


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


@pytest.mark.parametrize("method", ["contrastive", "proxy_nca_pp"])
def test_raw_and_feature_interfaces_preserve_retrieval_projection(method):
    model = MotionRetrievalModel(
        TinyEncoder(),
        method_id=method,
        representation_dimension=4,
        joints=2,
        embedding_dimension=8,
    ).eval()
    poses = torch.randn(4, 2, 3, 2, 3)
    poses[..., 2] = 1
    features = model.forward_features(poses)
    projected = model.project_features(features, poses[..., 2] > 0)
    torch.testing.assert_close(projected, model(poses))
    torch.testing.assert_close(
        torch.nn.functional.normalize(model.forward_raw(poses), dim=-1), projected
    )
    if method == "proxy_nca_pp":
        with pytest.raises(ValueError, match="requires a valid token mask"):
            model.project_features(features)


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
            "final-train.jsonl": records,
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
            "encoder_parameters": tuple(name for name, _ in encoder.named_parameters()),
            "initialization_sha256": runtime.state_digest(encoder),
            "unused_head_sha256": runtime._state_digest(
                {key: value for key, value in state.items() if key.startswith("head.")}
            ),
            "model_shapes": {
                **{
                    f"encoder.{key}": tuple(value.shape) for key, value in state.items()
                },
                "head.projection.weight": (
                    dimension,
                    4 if identity["method"] == "proxy_nca_pp" else 8,
                ),
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


@pytest.mark.parametrize("change", ["head_shape", "encoder", "proxy", "ibc"])
def test_rehashed_invalid_checkpoint_state_is_rejected(experiment, tmp_path, change):
    path = tmp_path / "benchmark-v2/state"
    method = {"proxy": "proxy_anchor", "ibc": "ibc"}.get(change, "contrastive")
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


def _proxy_config(experiment, *, steps=6):
    import yaml

    path = experiment["config_path"]
    config = yaml.safe_load(path.read_text())
    config["training"].update(steps=steps, validation_every=1, encoder_mode="finetune")
    path.write_text(yaml.safe_dump(config))


def test_proxy_full_run_verifies_and_pairs_with_common_head(experiment, tmp_path):
    _proxy_config(experiment)
    paths = []
    for method in ("contrastive", "proxy_nca_pp"):
        path = tmp_path / "benchmark-v2" / method
        runner.run_experiment(**experiment, method=method, output_dir=path)
        runtime.verify_run(path)
        paths.append(path)
    proxy = paths[1]
    checkpoint = torch.load(proxy / "checkpoint.pt", weights_only=True)
    history = runtime.read_json(proxy / "history.json")
    assert [row["phase"] for row in history["steps"]] == ["warmup"] * 5 + ["main"]
    assert all(row["encoder_gradient_parameters"] == 0 for row in history["steps"][:5])
    assert history["steps"][5]["encoder_gradient_parameters"] > 0
    assert checkpoint["training_state"]["main_updates"] == 1
    assert checkpoint["selected_step"] == 6
    assert checkpoint["model"]["head.projection.weight"].shape == (512, 4)
    reloaded = MotionRetrievalModel(
        TinyEncoder(),
        embedding_dimension=512,
        representation_dimension=4,
        joints=2,
        method_id="proxy_nca_pp",
    )
    reloaded.load_state_dict(checkpoint["model"], strict=True)
    assert runtime.state_digest(reloaded) == runtime._state_digest(checkpoint["model"])
    compared = runner.compare_development(
        paths, tmp_path / "benchmark-v2/comparison.json"
    )
    assert compared["methods"] == ["contrastive", "proxy_nca_pp"]


def test_proxy_profile_executes_encoder_backward_without_claiming_warmup(
    experiment, tmp_path
):
    _proxy_config(experiment, steps=2)
    path = tmp_path / "benchmark-v2/profile-proxy"
    runner.run_experiment(
        **experiment, method="proxy_nca_pp", output_dir=path, profile_steps=2
    )
    manifest = runtime.verify_run(path)
    assert manifest["identity"]["scientific_use_allowed"] is False
    assert (
        manifest["identity"]["training_recipe"]["profile_phase"]
        == "post_warmup_capacity"
    )
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    assert checkpoint["training_state"]["warmup_updates"] == 0
    assert checkpoint["training_state"]["main_updates"] == 2
    assert runtime.read_json(path / "telemetry.json")["encoder_backward_steps"] == 2


def test_proxy_short_scientific_budget_is_rejected_before_model_load(
    experiment, tmp_path, monkeypatch
):
    _proxy_config(experiment, steps=5)
    monkeypatch.setattr(
        runner,
        "load_frozen_encoder",
        lambda *_: pytest.fail("must reject before loading GPU model"),
    )
    with pytest.raises(ValueError, match="complete five-epoch warmup"):
        runner.run_experiment(
            **experiment,
            method="proxy_nca_pp",
            output_dir=tmp_path / "benchmark-v2/short",
        )


@pytest.mark.parametrize(
    "change",
    [
        "head",
        "proxy",
        "optimizer_shape",
        "optimizer_lr",
        "phase",
        "encoder_parameter",
        "encoder_all_moments",
        "encoder_one_moment",
    ],
)
def test_proxy_checkpoint_auxiliary_state_cannot_be_rehashed_into_validity(
    experiment, tmp_path, change
):
    _proxy_config(experiment)
    path = tmp_path / "benchmark-v2/corrupt"
    runner.run_experiment(**experiment, method="proxy_nca_pp", output_dir=path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    if change == "head":
        checkpoint["model"]["head.projection.weight"] = torch.ones(512, 8)
    elif change == "proxy":
        checkpoint["criterion"] = {}
    elif change == "optimizer_shape":
        next(iter(checkpoint["optimizer"]["state"].values()))["exp_avg"] = torch.ones(1)
    elif change == "optimizer_lr":
        checkpoint["optimizer"]["param_groups"][2]["lr"] = 0.004
    elif change.startswith("encoder_"):
        group = checkpoint["optimizer"]["param_groups"][0]
        indices = group["params"][:]
        if change == "encoder_parameter":
            del group["param_names"][0]
            del group["params"][0]
        if change != "encoder_all_moments":
            indices = indices[:1]
        for index in indices:
            checkpoint["optimizer"]["state"].pop(index)
    else:
        checkpoint["training_state"]["warmup_updates"] = 1
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(ValueError, match="optimizer|warmup|shape"):
        runtime.verify_run(path)
