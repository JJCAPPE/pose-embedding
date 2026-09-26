from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from pose_embed.benchmark import runner, runtime
from pose_embed.benchmark.config import load_benchmark, load_methods
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
def experiment(tmp_path, monkeypatch, request):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    config = load_benchmark().model_dump()
    classes = 3 if getattr(request, "param", None) == "diva" else 2
    config["training"].update(steps=2, validation_every=1, classes_per_batch=classes)
    import yaml

    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    records = [
        ManifestRecord(
            sample_id=f"S001C001P{person:03d}R001A{action:03d}",
            split="development_train",
        )
        for action in range(1, classes + 1)
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
        head_shapes = {
            "head.projection.weight": (
                dimension,
                4
                if identity["method"]
                in {
                    "proxy_nca_pp",
                    "hist",
                    "diml",
                    "proxy_nca_metrix",
                    "proxy_anchor_metrix",
                    "multi_similarity_metrix",
                }
                else 8,
            ),
            "head.projection.bias": (dimension,),
        }
        if identity["method"] == "drml":
            from pose_embed.benchmark.drml import DRMLHead

            with torch.random.fork_rng(devices=[]):
                head_shapes = {
                    "head." + key: tuple(value.shape)
                    for key, value in DRMLHead(4, dimension // 4).state_dict().items()
                }
        if identity["method"] == "diva":
            shapes = {
                **{
                    f"{prefix}.{key}": tuple(value.shape)
                    for prefix in ("encoder", "momentum_encoder")
                    for key, value in state.items()
                },
                **{
                    f"head.projections.{task}.{part}": shape
                    for task in ("discriminative", "shared", "intra", "sample")
                    for part, shape in (
                        ("weight", (dimension // 4, 8)),
                        ("bias", (dimension // 4,)),
                    )
                },
                "momentum_projection.weight": (dimension // 4, 8),
                "momentum_projection.bias": (dimension // 4,),
                "momentum_updates": (),
            }
            return {
                "encoder_parameters": tuple(
                    name for name, _ in encoder.named_parameters()
                ),
                "initialization_sha256": runtime.state_digest(encoder),
                "unused_head_sha256": runtime._state_digest(
                    {
                        key: value
                        for key, value in state.items()
                        if key.startswith("head.")
                    }
                ),
                "model_shapes": shapes,
            }
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
                **head_shapes,
            },
        }

    monkeypatch.setattr(
        runtime, "_verified_profile_records", lambda identity, config: records
    )
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
    with pytest.raises(ValueError, match="complete declared warmup"):
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


@pytest.mark.parametrize("profile", [False, True])
def test_hist_full_runner_warmup_and_checkpoint_validation(
    experiment, tmp_path, profile
):
    _proxy_config(experiment, steps=3)
    path = tmp_path / "benchmark-v2/hist"
    runner.run_experiment(
        **experiment,
        method="hist",
        output_dir=path,
        profile_steps=2 if profile else None,
    )
    manifest = runtime.verify_run(path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    assert checkpoint["training_state"]["warmup_updates"] == (0 if profile else 1)
    assert checkpoint["training_state"]["main_updates"] > 0
    assert (
        manifest["identity"]["head_recipe"]
        == "confidence_valid_token_mean_plus_max_project_nonaffine_ln"
    )
    checkpoint["criterion"].pop("loss.graph.normalization.running_mean")
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(ValueError, match="criterion"):
        runtime.verify_run(path)


@pytest.mark.parametrize(
    "method", ["multi_similarity_metrix", "proxy_anchor_metrix", "proxy_nca_metrix"]
)
def test_metrix_factory_runner_and_checkpoint_roundtrip(experiment, tmp_path, method):
    _proxy_config(experiment, steps=6)
    path = tmp_path / "benchmark-v2/metrix"
    runner.run_experiment(**experiment, method=method, output_dir=path)
    manifest = runtime.verify_run(path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    assert manifest["identity"]["method"] == method
    assert checkpoint["model"]["head.projection.weight"].shape == (512, 4)
    criterion = build_loss(
        method, manifest["identity"]["method_specification"]["parameters"], 2
    )
    assert criterion.requires_feature_training
    criterion.load_state_dict(checkpoint["criterion"], strict=True)
    if method == "proxy_nca_metrix":
        assert checkpoint["training_state"]["warmup_updates"] == 5
        assert checkpoint["training_state"]["main_updates"] == 1
        checkpoint["optimizer"]["param_groups"][2]["lr"] = 1
    else:
        checkpoint["model"]["head.projection.weight"] = torch.ones(512, 8)
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(ValueError, match="optimizer|shape"):
        runtime.verify_run(path)


@pytest.mark.parametrize("track", ["frozen", "finetune"])
def test_drml_runner_executes_full_objective_and_restores_checkpoint(
    experiment, tmp_path, track
):
    import yaml

    from pose_embed.benchmark.config import load_methods
    from pose_embed.benchmark.losses import build_loss
    from pose_embed.benchmark.training import build_optimizer

    config = yaml.safe_load(experiment["config_path"].read_text())
    config["training"]["encoder_mode"] = track
    experiment["config_path"].write_text(yaml.safe_dump(config))
    path = tmp_path / "benchmark-v2/drml"
    manifest = runner.run_experiment(**experiment, method="drml", output_dir=path)
    runtime.verify_run(path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    model = MotionRetrievalModel(
        TinyEncoder(), method_id="drml", representation_dimension=4, joints=2
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    criterion = build_loss("drml", load_methods()["drml"].parameters, 2)
    criterion.load_state_dict(checkpoint["criterion"], strict=True)
    recipe = manifest["identity"]["training_recipe"]
    optimizer = build_optimizer(model, criterion, recipe, "main")
    optimizer.load_state_dict(checkpoint["optimizer"])
    assert optimizer.param_groups[0]["lr"] == (1e-5 if track == "finetune" else 0)
    assert [group["lr"] for group in optimizer.param_groups[1:]] == [1e-4, 1e-4]
    assert criterion.training_steps.item() == checkpoint["selected_step"]
    for row in runtime.read_json(path / "history.json")["steps"]:
        assert sum(row["drml_assignment_counts"]) == 8
        assert (row["encoder_gradient_parameters"] > 0) == (track == "finetune")
    model.eval()
    poses = torch.randn(2, 2, 3, 2, 3)
    poses[..., 2] = 1
    assert model(poses).shape == (2, 512)
    reference = MotionRetrievalModel(
        TinyEncoder(), method_id="drml", representation_dimension=4, joints=2
    ).eval()
    reference.load_state_dict(checkpoint["model"])
    torch.testing.assert_close(model(poses), reference(poses))


@pytest.mark.parametrize(
    "change",
    ["decoder", "proxy", "mapping", "moment", "counter", "history", "learning_rate"],
)
def test_rehashed_drml_auxiliary_checkpoint_tampering_is_rejected(
    experiment, tmp_path, change
):
    path = tmp_path / "benchmark-v2/drml-corrupt"
    runner.run_experiment(**experiment, method="drml", output_dir=path)
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    if change == "decoder":
        checkpoint["model"]["head.decoders.0.weight"] = torch.ones(1, 1)
    elif change == "proxy":
        del checkpoint["criterion"]["embedding_loss.proxies"]
    elif change == "mapping":
        group = checkpoint["optimizer"]["param_groups"][0]
        del group["params"][0]
        del group["param_names"][0]
    elif change == "moment":
        index = checkpoint["optimizer"]["param_groups"][1]["params"][-1]
        del checkpoint["optimizer"]["state"][index]
    elif change == "counter":
        checkpoint["criterion"]["branch_steps"][0] += 1
    elif change == "learning_rate":
        checkpoint["optimizer"]["param_groups"][2]["lr"] = 1
    else:
        history = runtime.read_json(path / "history.json")
        history["steps"][0]["drml_assignment_counts"] = [0, 0, 0, 0]
        (path / "history.json").write_text(json.dumps(history))
        _rehash_output(path, "history.json")
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(ValueError, match="DRML|keys or shapes|criterion/proxy"):
        runtime.verify_run(path)


def test_drml_profile_measures_real_finetuning_step(experiment, tmp_path):
    import yaml

    config = yaml.safe_load(experiment["config_path"].read_text())
    config["training"]["encoder_mode"] = "finetune"
    experiment["config_path"].write_text(yaml.safe_dump(config))
    path = tmp_path / "benchmark-v2/drml-profile"
    manifest = runner.run_experiment(
        **experiment, method="drml", output_dir=path, profile_steps=2
    )
    runtime.verify_run(path)
    assert manifest["identity"]["scientific_use_allowed"] is False
    assert runtime.read_json(path / "telemetry.json")["encoder_backward_steps"] == 2


@pytest.mark.parametrize(
    "fault",
    [
        "counter",
        "rng",
        "teacher",
        "boundary",
        "optimizer_missing",
        "optimizer_mapping",
        "optimizer_step",
    ],
)
def test_s2sd_run_rejects_rehashed_training_state(
    experiment, tmp_path, monkeypatch, fault
):
    methods = load_methods()
    original = methods["s2sd"]
    # All dimensions here are deliberately synthetic; production registry stays fixed.
    methods["s2sd"] = original.model_copy(
        update={
            "embedding_dimension": 8,
            "parameters": original.parameters
            | {
                "embedding_dimension": 8,
                "feature_dimension": 8,
                "target_dimensions": [8, 12, 16, 20],
                "feature_delay": 1,
            },
        }
    )
    monkeypatch.setattr(runner, "load_methods", lambda: methods)
    monkeypatch.setattr(runtime, "load_methods", lambda: methods)
    path = tmp_path / "benchmark-v2/s2sd"
    runner.run_experiment(**experiment, method="s2sd", output_dir=path)
    assert runtime.verify_run(path)["identity"]["method"] == "s2sd"
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    assert checkpoint["selected_step"] == 2
    assert checkpoint["criterion"]["completed_steps"].item() == 2
    if fault == "counter":
        checkpoint["criterion"]["completed_steps"].fill_(1)
    elif fault == "rng":
        checkpoint["criterion"]["student_objective.rng_state"].fill_(0)
    elif fault == "teacher":
        del checkpoint["criterion"]["teachers.0.0.weight"]
    elif fault == "boundary":
        checkpoint["criterion"]["teacher_objectives.0.beta"] = torch.ones(1)
    elif fault == "optimizer_missing":
        del checkpoint["optimizer"]
    elif fault == "optimizer_mapping":
        checkpoint["optimizer"]["param_groups"][2]["param_names"].pop()
    else:
        next(iter(checkpoint["optimizer"]["state"].values()))["step"].add_(1)
    torch.save(checkpoint, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    with pytest.raises(
        ValueError, match="counter|sampling state|criterion/proxy|optimizer"
    ):
        runtime.verify_run(path)


def test_s2sd_profiles_active_delayed_path_and_rejects_short_scientific_run(
    experiment, tmp_path, monkeypatch
):
    methods = load_methods()
    methods["s2sd"] = methods["s2sd"].model_copy(
        update={
            "embedding_dimension": 8,
            "parameters": methods["s2sd"].parameters
            | {
                "embedding_dimension": 8,
                "feature_dimension": 8,
                "target_dimensions": [8, 12, 16, 20],
                "feature_delay": 2,
            },
        }
    )
    monkeypatch.setattr(runner, "load_methods", lambda: methods)
    monkeypatch.setattr(runtime, "load_methods", lambda: methods)
    path = tmp_path / "benchmark-v2/s2sd-profile"
    runner.run_experiment(**experiment, method="s2sd", output_dir=path, profile_steps=1)
    manifest = runtime.verify_run(path)
    recipe = manifest["identity"]["training_recipe"]
    assert recipe["profile_phase"] == "post_feature_delay_capacity"
    assert recipe["profile_counter_offset"] == 2
    state = torch.load(path / "checkpoint.pt", weights_only=True)
    assert state["criterion"]["completed_steps"].item() == 3
    assert state["selected_step"] == 1
    with pytest.raises(ValueError, match="scientific step budget"):
        runner.run_experiment(
            **experiment, method="s2sd", output_dir=tmp_path / "short"
        )


def test_diml_full_runner_uses_structural_validation_and_checks_head(
    experiment, tmp_path, monkeypatch
):
    def poses(annotation, protocol):
        values = (
            np.random.default_rng(annotation["index"])
            .normal(size=(2, 4, 17, 3))
            .astype(np.float32)
        )
        values[..., 2] = 1
        return values

    monkeypatch.setattr(runner, "preprocess_annotation", poses)
    path = tmp_path / "benchmark-v2/diml"
    runner.run_experiment(**experiment, method="diml", output_dir=path)
    checked = runtime.verify_run(path)
    assert checked["identity"]["method"] == "diml"
    result = runtime.read_json(path / "development-result.json")
    assert (
        result["policy"]["similarity"] == "diml_cross_correlation_transport_multiscale"
    )
    history = runtime.read_json(path / "history.json")["steps"]
    assert history[-1]["descriptor_storage"]["bytes_per_sample"] == 17 * 512 * 4 + 16
    assert history[-1]["retrieval_timing"]["scoring_seconds"] > 0
    state = torch.load(path / "checkpoint.pt", weights_only=True)
    state["model"]["head.projection.weight"] = torch.ones(512, 8)
    torch.save(state, path / "checkpoint.pt")
    manifest = runtime.read_json(path / "run-manifest.json")
    manifest["outputs"]["checkpoint.pt"] = sha256_file(path / "checkpoint.pt")
    (path / "run-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="keys or shapes"):
        runtime.verify_run(path)


@pytest.mark.parametrize("experiment", ["diva"], indirect=True)
@pytest.mark.parametrize("profile", [False, True])
def test_diva_runner_memory_state_and_tamper_rejection(
    experiment, tmp_path, monkeypatch, profile
):
    methods = runner.load_methods()
    methods["diva"] = methods["diva"].model_copy(
        update={
            "embedding_dimension": 16,
            "parameters": methods["diva"].parameters
            | {
                "feature_dimension": 8,
                "physical_batch_size": 12,
                "queue_batches": 2,
                "decorrelation_hidden": 8,
            },
        }
    )
    monkeypatch.setattr(runner, "load_methods", lambda *args: methods)
    monkeypatch.setattr(runtime, "load_methods", lambda *args: methods)
    path = tmp_path / "benchmark-v2/diva"
    runner.run_experiment(
        **experiment,
        method="diva",
        output_dir=path,
        profile_steps=2 if profile else None,
    )
    manifest = runtime.verify_run(path)
    assert manifest["identity"]["stage"] == ("profile" if profile else "development")
    checkpoint = torch.load(path / "checkpoint.pt", weights_only=True)
    assert checkpoint["criterion"]["queue"].shape == (24, 4)
    assert checkpoint["model"]["momentum_updates"].item() == checkpoint["selected_step"]
    assert checkpoint["criterion"]["queue_indices"].max() < 12
    telemetry = runtime.read_json(path / "telemetry.json")
    assert telemetry["memory_items"] == 24
    assert telemetry["memory_bootstrap_seconds"] > 0
    assert telemetry["momentum_parameters"] > 0
    memory = runtime.read_json(path / "memory-plan.json")
    assert memory["partition"] == "development_train"
    original = copy.deepcopy(checkpoint)
    for change in ("identity", "counter", "queue", "optimizer"):
        changed = copy.deepcopy(original)
        if change == "identity":
            changed["criterion"]["training_identity"][0] ^= 1
        elif change == "counter":
            changed["model"]["momentum_updates"].add_(1)
        elif change == "queue":
            changed["criterion"]["queue_indices"][0] = 100
        else:
            changed["optimizer"]["param_groups"][-1]["lr"] = 1
        torch.save(changed, path / "checkpoint.pt")
        _rehash_output(path, "checkpoint.pt")
        with pytest.raises(ValueError, match="DiVA|optimizer"):
            runtime.verify_run(path)
    torch.save(original, path / "checkpoint.pt")
    _rehash_output(path, "checkpoint.pt")
    memory["partition"] = "novel"
    (path / "memory-plan.json").write_text(json.dumps(memory))
    _rehash_output(path, "memory-plan.json")
    with pytest.raises(ValueError, match="memory plan"):
        runtime.verify_run(path)


@pytest.mark.parametrize("segmented", [False, True])
def test_candidate_runner_persists_effective_config_and_final_adopts_winner(
    experiment, tmp_path, monkeypatch, segmented
):
    import yaml

    from pose_embed.benchmark import campaign, locks
    from pose_embed.benchmark.config import benchmark_digest

    path = experiment["config_path"]
    values = yaml.safe_load(path.read_text())
    values["training"]["encoder_mode"] = "finetune"
    path.write_text(yaml.safe_dump(values))
    base = load_benchmark(path)
    half = campaign.candidate_config(base, "half")
    binding = {
        "candidate": "half",
        "campaign_sha256": "fixture-campaign",
        "campaign_base_config_path": str(path),
    }
    # Complete campaign eligibility is exercised by the 468-cell integration
    # tests; this fixture tests actual optimization and effective-config I/O.
    monkeypatch.setattr(campaign, "training_binding", lambda *_: (half, binding))
    observed = []

    def validate(identity, config, directory):
        assert identity["candidate"] == "half"
        assert config == half
        assert runtime.read_json(
            directory / "effective-configuration.json"
        ) == half.model_dump(mode="json")
        observed.append(identity["stage"])

    monkeypatch.setattr(campaign, "validate_run_binding", validate)
    development = tmp_path / "benchmark-v2/candidate-half"
    arguments = dict(
        **experiment, method="contrastive", candidate="half", output_dir=development
    )
    run = runner.run_experiment(
        **arguments, **({"segment_steps": 1} if segmented else {})
    )
    if segmented:
        assert run["status"] == "resumable"
        command = run["next_resume_command"]
        assert "--candidate half" in command and str(path) in command
        assert "effective-configuration.json" not in command
        saved_config = sha256_file(development / "effective-configuration.json")
        run = runner.run_experiment(**arguments, resume_from=run["segment_manifest"])
        assert saved_config == sha256_file(development / "effective-configuration.json")
    assert run["identity"]["benchmark_sha256"] == benchmark_digest(half)
    assert (
        run["identity"]["training_recipe"]["learning_rate"]
        == base.training.learning_rate * 0.5
    )
    assert "effective-configuration.json" in run["outputs"]
    selection = {
        "campaign_sha256": binding["campaign_sha256"],
        "campaign_base_config_path": str(path),
        "methods": {
            "contrastive": {
                "candidate": "half",
                "configuration_sha256": runtime.digest(half.model_dump(mode="json")),
                "selected_steps": 2,
            }
        },
    }
    lock_path = tmp_path / "benchmark-v2/locks/selection.json"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps(selection))
    monkeypatch.setattr(locks, "validate_selection", lambda **_: selection)
    final_arguments = dict(
        **experiment,
        method="contrastive",
        stage="final",
        output_dir=tmp_path / "benchmark-v2/selected-final",
    )
    final = runner.run_experiment(
        **final_arguments, **({"segment_steps": 1} if segmented else {})
    )
    if segmented:
        assert final["status"] == "resumable"
        command = final["next_resume_command"]
        assert "--candidate" not in command and str(path) in command
        assert "--phase final" in command
        final = runner.run_experiment(
            **final_arguments, resume_from=final["segment_manifest"]
        )
    assert final["identity"]["candidate"] == "half"
    assert final["identity"]["configuration"] == half.model_dump(mode="json")
    assert final["identity"]["steps"] == 2
    runtime.verify_run(development)
    runtime.verify_run(tmp_path / "benchmark-v2/selected-final")
    assert {"development", "final"} <= set(observed)


def test_profile_measures_real_retrieval_and_rejects_rehashed_metadata(
    experiment, tmp_path
):
    directory = tmp_path / "benchmark-v2/retrieval-profile"
    manifest = runner.run_experiment(
        **experiment, method="contextual", profile_steps=3, output_dir=directory
    )
    profile = runtime.read_json(directory / "telemetry.json")["retrieval_profile"]
    assert profile["sample_count"] == 8
    assert profile["descriptor_storage"]["bytes_per_sample"] == 512 * 4
    assert profile["encoding_seconds"] > 0 and profile["scoring_seconds"] > 0
    assert "metrics" not in profile and "per_query" not in profile
    assert manifest["identity"]["profile_retrieval"]["prefix_size"] == 128
    telemetry = runtime.read_json(directory / "telemetry.json")
    telemetry["retrieval_profile"]["sample_ids"] = list(reversed(profile["sample_ids"]))
    (directory / "telemetry.json").write_text(json.dumps(telemetry))
    manifest["outputs"]["telemetry.json"] = sha256_file(directory / "telemetry.json")
    (directory / "run-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="validation prefix"):
        runtime.verify_run(directory)
