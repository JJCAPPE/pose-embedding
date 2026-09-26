"""Analytical DiVA checks and training-only memory invariants on synthetic poses."""

from __future__ import annotations

import copy
import math

import pytest
import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.benchmark.config import load_benchmark, load_methods
from pose_embed.benchmark.diva import (
    TASKS,
    DiVAHead,
    DiVALoss,
    DiVAParameters,
    corrected_dance_weights,
    dance_loss,
    margin_loss,
    motion_views,
    reverse_gradient,
    task_triplets,
)
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import encode, optimizer_step
from pose_embed.benchmark.training import build_optimizer, resolve_recipe
from pose_embed.data.manifest import ManifestRecord


def config(**overrides):
    return DiVAParameters(
        **{
            "embedding_dimension": 16,
            "feature_dimension": 6,
            "physical_batch_size": 12,
            "queue_batches": 2,
            "decorrelation_hidden": 8,
            **overrides,
        }
    )


def batch():
    generator = torch.Generator().manual_seed(54)
    poses = torch.randn(12, 2, 3, 2, 3, generator=generator)
    poses[..., 2] = 1
    return poses, torch.arange(3).repeat_interleave(4)


def records(split="development_train"):
    return [
        ManifestRecord(sample_id=f"S001C001P{person:03d}R001A{action:03d}", split=split)
        for action in (2, 3, 4)
        for person in range(1, 5)
    ]


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(3, 3)
        self.head = nn.Linear(3, 3)
        self.calls = 0

    def get_representation(self, poses):
        self.calls += 1
        return self.projection(poses)


def configured(fine_tune=True):
    torch.manual_seed(11)
    model = MotionRetrievalModel(
        Encoder(),
        embedding_dimension=16,
        representation_dimension=3,
        joints=2,
        method_id="diva",
        train_encoder=fine_tune,
    )
    criterion = DiVALoss(config(), 3)
    poses, labels = batch()
    criterion.configure_training(records(), labels.tolist(), "development")
    for _ in range(2):
        criterion.bootstrap(model, poses, list(range(12)))
    training = load_benchmark().training.model_copy(
        update={
            "classes_per_batch": 3,
            "encoder_mode": "finetune" if fine_tune else "frozen",
        }
    )
    recipe = resolve_recipe("diva", config().model_dump(), training, 12)
    optimizer = build_optimizer(model, criterion, recipe, "main")
    return model, criterion, optimizer, poses, labels, recipe


@pytest.mark.parametrize("task", TASKS[:3])
def test_task_sampling_obeys_published_class_relations_and_distinct_items(task):
    values = torch.randn(12, 4, generator=torch.Generator().manual_seed(4))
    labels = torch.arange(3).repeat_interleave(4)
    result = task_triplets(values, labels, task, torch.Generator().manual_seed(1), 0.5)
    anchor, positive, negative = result.unbind(1)
    assert (
        (anchor != positive).all()
        and (anchor != negative).all()
        and (positive != negative).all()
    )
    if task == "discriminative":
        assert (labels[anchor] == labels[positive]).all()
        assert (labels[anchor] != labels[negative]).all()
    elif task == "shared":
        assert (labels[anchor] != labels[positive]).all()
        assert (labels[anchor] != labels[negative]).all()
        assert (labels[positive] != labels[negative]).all()
    else:
        assert (labels[anchor] == labels[positive]).all()
        assert (labels[anchor] == labels[negative]).all()
    assert torch.equal(
        result,
        task_triplets(values, labels, task, torch.Generator().manual_seed(1), 0.5),
    )


def test_task_sampling_refuses_insufficient_class_or_within_class_coverage():
    with pytest.raises(ValueError, match="three"):
        task_triplets(
            torch.randn(8, 4),
            torch.arange(2).repeat_interleave(4),
            "shared",
            torch.Generator(),
            0.5,
        )


def test_margin_analytical_both_active_case_and_beta_gradient():
    embeddings = torch.tensor([[0.0, 0.0], [1.1, 0.0], [1.0, 0.0]], requires_grad=True)
    beta = torch.tensor([1.2, 1.2], requires_grad=True)
    loss = margin_loss(
        embeddings, torch.tensor([0, 0, 1]), torch.tensor([[0, 1, 2]]), beta, 0.2
    )
    assert loss.item() == pytest.approx(0.5)
    loss.backward()
    assert beta.grad[0] == 0
    assert embeddings.grad.abs().sum() > 0


def test_corrected_dance_weights_normalize_each_query_independently():
    query = functional.normalize(
        torch.tensor([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype=torch.float64),
        dim=-1,
    )
    memory = functional.normalize(
        torch.tensor(
            [[0.8, 0.6, 0.0, 0.0], [0.2, 0.98, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0]],
            dtype=torch.float64,
        ),
        dim=-1,
    )
    actual = corrected_dance_weights(query, memory, 0.5, 1.4)
    torch.testing.assert_close(actual.sum(1), torch.ones(2, dtype=torch.float64))
    torch.testing.assert_close(
        actual[:1], corrected_dance_weights(query[:1], memory, 0.5, 1.4)
    )
    distance = math.sqrt(2 - 2 * 0.8)
    d2 = math.sqrt(2 - 2 * (0.2 / math.sqrt(0.2**2 + 0.98**2)))
    first = distance**-2 * (1 - distance**2 / 4) ** -0.5
    second = d2**-2 * (1 - d2**2 / 4) ** -0.5
    assert actual[0, 0].item() == pytest.approx(first / (first + second))
    assert actual[0, 2] < 1e-35
    # When no memory item is inside support, the explicit tiny-floor convention
    # produces a defined uniform row, rather than a NaN or discarded anchor.
    torch.testing.assert_close(
        corrected_dance_weights(query[:1], -query[:1].repeat(3, 1), 0.5, 1.4),
        torch.full((1, 3), 1 / 3, dtype=torch.float64),
    )


def test_dance_matches_positive_inclusive_softmax_and_stops_key_gradients():
    query = torch.tensor(
        [[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64, requires_grad=True
    )
    positive = torch.tensor(
        [[0.8, 0.6, 0.0, 0.0]], dtype=torch.float64, requires_grad=True
    )
    memory = torch.tensor(
        [[0.0, 1.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    actual = dance_loss(query, positive, memory, config(temperature=0.5))
    # Both distances exceed1.4, so weights are each1/2; logits=[1.6,0,-1].
    expected = math.log(math.exp(1.6) + 1 + math.exp(-1)) - 1.6
    assert actual.item() == pytest.approx(expected)
    actual.backward()
    assert query.grad.abs().sum() > 0
    assert positive.grad is None and memory.grad is None


def test_gradient_reversal_flips_only_embedding_gradients():
    source = torch.tensor([[0.6, 0.8]], requires_grad=True)
    target = torch.tensor([[0.8, 0.6]], requires_grad=True)
    predictor = nn.Linear(2, 2, bias=False)
    reference = copy.deepcopy(predictor)
    normal_source = source.detach().clone().requires_grad_()
    normal_target = target.detach().clone().requires_grad_()
    value = (
        -(
            reverse_gradient(target)
            * functional.normalize(predictor(reverse_gradient(source)), dim=1)
        )
        .square()
        .mean()
    )
    direct = (
        -(normal_target * functional.normalize(reference(normal_source), dim=1))
        .square()
        .mean()
    )
    value.backward()
    direct.backward()
    torch.testing.assert_close(source.grad, -normal_source.grad)
    torch.testing.assert_close(target.grad, -normal_target.grad)
    torch.testing.assert_close(predictor.weight.grad, reference.weight.grad)


def test_head_concatenates_four_unit_branches_with_fixed_auxiliary_emphasis():
    head = DiVAHead(16, 3, 2)
    features = torch.randn(5, 2, 3, 2, 3)
    branches = head.branches(features)
    expected = functional.normalize(
        torch.cat(
            [branches[t] * (0.5 if t == "discriminative" else 1) for t in TASKS], dim=1
        ),
        dim=1,
    )
    torch.testing.assert_close(head(features), expected)
    torch.testing.assert_close(head(features).norm(dim=1), torch.ones(5))
    assert head(features).shape == (5, 16)


def test_motion_views_preserve_identity_confidence_temporal_order_and_absent_tokens():
    poses, _ = batch()
    poses[:, 1] = 0
    generator = torch.Generator().manual_seed(2)
    state = torch.get_rng_state().clone()
    first, second = motion_views(poses, generator, config())
    assert torch.equal(state, torch.get_rng_state())
    assert not torch.equal(first, second)
    for view in (first, second):
        assert torch.equal(view[..., 2], poses[..., 2])
        assert torch.equal(view[:, 1], poses[:, 1])
        # One common affine transform per sequence preserves trajectory displacements
        # up to the same bounded global scale for every frame/joint/person.
        ratio = (view[:, 0, 1, 0, :2] - view[:, 0, 0, 0, :2]).norm(dim=1) / (
            poses[:, 0, 1, 0, :2] - poses[:, 0, 0, 0, :2]
        ).norm(dim=1)
        assert ((ratio >= 0.9 - 1e-6) & (ratio <= 1.1 + 1e-6)).all()
    repeat = motion_views(poses, torch.Generator().manual_seed(2), config())
    assert torch.equal(first, repeat[0]) and torch.equal(second, repeat[1])


@pytest.mark.parametrize("fine_tune", [False, True])
def test_real_update_trains_all_heads_and_criteria_and_commits_ema_queue(fine_tune):
    model, criterion, optimizer, poses, labels, _ = configured(fine_tune)
    before_model = copy.deepcopy(model.state_dict())
    before_loss = copy.deepcopy(criterion.state_dict())
    model.encoder.calls = model.momentum_encoder.calls = 0
    criterion.set_training_batch(list(range(12)))
    value = optimizer_step(model, criterion, optimizer, poses, labels)
    assert math.isfinite(value)
    assert model.encoder.calls == model.momentum_encoder.calls == 1
    for task in TASKS:
        assert not torch.equal(
            before_model[f"head.projections.{task}.weight"],
            model.state_dict()[f"head.projections.{task}.weight"],
        )
    assert any(
        not torch.equal(before_loss[key], value)
        for key, value in criterion.state_dict().items()
        if key.startswith("decorators.")
    )
    assert any(
        not torch.equal(before_loss[key], value)
        for key, value in criterion.state_dict().items()
        if key.startswith("boundaries.")
    )
    assert (
        not torch.equal(
            before_model["encoder.projection.weight"], model.encoder.projection.weight
        )
    ) == fine_tune
    torch.testing.assert_close(
        model.momentum_projection.weight,
        before_model["momentum_projection.weight"] * 0.9
        + model.head.projections["sample"].weight * 0.1,
    )
    assert model.momentum_updates.item() == criterion.completed_steps.item() == 1
    assert criterion.queue_position.item() == 12
    assert all(
        parameter.grad is None for parameter in model.momentum_encoder.parameters()
    )
    assert all(
        parameter.grad is None for parameter in model.momentum_projection.parameters()
    )
    criterion.validate_checkpoint_state(criterion.state_dict(), 1)


def test_queue_rejects_validation_novel_and_changed_training_partitions():
    criterion = DiVALoss(config(), 3)
    _, labels = batch()
    for split in ("development_validation", "novel_query_official"):
        with pytest.raises(ValueError, match="training partition"):
            criterion.configure_training(records(split), labels.tolist(), "development")
    criterion.configure_training(records(), labels.tolist(), "development")
    with pytest.raises(ValueError, match="cannot change"):
        criterion.configure_training(records("final_train"), labels.tolist(), "final")


def test_retrieval_does_not_change_queue_ema_or_rng_and_training_in_eval_is_rejected():
    model, criterion, _, poses, labels, _ = configured()
    before_model = copy.deepcopy(model.state_dict())
    before_loss = copy.deepcopy(criterion.state_dict())
    dataset = list(zip(poses, labels, strict=True))
    values = encode(model, dataset, "cpu", 4)
    assert values.shape == (12, 16)
    assert all(
        torch.equal(value, model.state_dict()[key])
        for key, value in before_model.items()
    )
    assert all(
        torch.equal(value, criterion.state_dict()[key])
        for key, value in before_loss.items()
    )
    model.eval()
    torch.testing.assert_close(model(poses)[:1], model(poses[:1]))
    criterion.set_training_batch(list(range(12)))
    with pytest.raises(ValueError, match="evaluation"):
        criterion.training_loss(model, poses, labels)


def test_checkpoint_optimizer_and_all_random_memory_state_resume_exactly():
    model, criterion, optimizer, poses, labels, recipe = configured()
    criterion.set_training_batch(list(range(12)))
    optimizer_step(model, criterion, optimizer, poses, labels)
    resumed_model = copy.deepcopy(model)
    resumed_loss = DiVALoss(config(), 3)
    resumed_loss.load_state_dict(copy.deepcopy(criterion.state_dict()))
    resumed_loss.configure_training(records(), labels.tolist(), "development")
    resumed_optimizer = build_optimizer(resumed_model, resumed_loss, recipe, "main")
    resumed_optimizer.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    losses = []
    for current_model, current_loss, current_optimizer in (
        (model, criterion, optimizer),
        (resumed_model, resumed_loss, resumed_optimizer),
    ):
        current_loss.set_training_batch(list(range(12)))
        losses.append(
            optimizer_step(
                current_model, current_loss, current_optimizer, poses, labels
            )
        )
    assert losses[0] == losses[1]
    assert all(
        torch.equal(value, resumed_model.state_dict()[key])
        for key, value in model.state_dict().items()
    )
    assert all(
        torch.equal(value, resumed_loss.state_dict()[key])
        for key, value in criterion.state_dict().items()
    )


def test_queue_bootstrap_and_step_boundaries_are_immutable():
    model, criterion, _, poses, labels, _ = configured()
    with pytest.raises(ValueError, match="immutable"):
        criterion.bootstrap(model, poses, list(range(12)))
    with pytest.raises(ValueError, match="physical training batch"):
        criterion.set_training_batch([0] * 12)
    criterion.set_training_batch(list(range(12)))
    with pytest.raises(ValueError, match="labels"):
        criterion.training_loss(model, poses, labels.flip(0))
    criterion.training_loss(model, poses, labels)
    with pytest.raises(ValueError, match="not completed"):
        criterion.set_training_batch(list(range(12)))


def test_registry_and_optimizer_capture_complete_recipe():
    spec = load_methods()["diva"]
    assert spec.status == "implemented"
    actual = DiVAParameters.model_validate(spec.parameters)
    assert actual.queue_size == 960 and actual.temperature == 0.1
    assert actual.branch_dimension == 128 and actual.momentum == 0.9
    _, _, optimizer, _, _, recipe = configured()
    assert recipe["optimizer"] == "Adam"
    assert [group["name"] for group in optimizer.param_groups] == [
        "encoder",
        "head",
        "diva_decorrelation",
        "diva_boundaries",
    ]
    assert optimizer.param_groups[-1]["lr"] == 0.0005
    assert optimizer.param_groups[-1]["weight_decay"] == 0


@pytest.mark.parametrize("scale", [0.5, 2.0])
def test_candidate_scale_reaches_learned_boundary_optimizer_group(scale):
    model, criterion, _, _, _, recipe = configured()
    scaled = {
        key: value * scale if key.endswith("learning_rate") else value
        for key, value in recipe.items()
    }
    optimizer = build_optimizer(model, criterion, scaled, "main")
    for group in optimizer.param_groups:
        expected = (
            scaled["beta_learning_rate"]
            if group["name"] == "diva_boundaries"
            else scaled["learning_rate"]
        )
        assert group["lr"] == expected
