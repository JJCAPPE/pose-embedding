"""Synthetic analytical checks for R-Margin/MSDFA and resumable training."""

from __future__ import annotations

import copy
import math

import pytest
import torch
from torch import nn

from pose_embed.benchmark.config import load_methods
from pose_embed.benchmark.losses import build_loss
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import optimizer_step
from pose_embed.benchmark.s2sd import (
    RegularizedMarginLoss,
    S2SDLoss,
    S2SDParameters,
    auxiliary_features,
    distance_weighted_probabilities,
    similarity_distillation,
)


def recipe(**overrides) -> S2SDParameters:
    return S2SDParameters(
        **{
            "embedding_dimension": 4,
            "feature_dimension": 6,
            "target_dimensions": (4, 6, 8, 10),
            **overrides,
        }
    )


def batch():
    generator = torch.Generator().manual_seed(34)
    return (
        torch.randn(8, 4, generator=generator, dtype=torch.float64),
        torch.arange(2).repeat_interleave(4),
        torch.randn(8, 6, generator=generator, dtype=torch.float64),
    )


def test_inverse_density_matches_equation_without_upper_cutoff():
    embeddings = torch.tensor(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.6, 0.8, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-0.8, 0.6, 0.0, 0.0],
        ],
        dtype=torch.float64,
    )
    labels = torch.tensor([0, 0, 1, 1])
    actual = distance_weighted_probabilities(embeddings, labels)
    distances = [math.sqrt(2), math.sqrt(3.6)]
    weights = [d**-2 * (1 - d * d / 4) ** -0.5 for d in distances]
    torch.testing.assert_close(
        actual[0, 2:], torch.tensor(weights, dtype=torch.float64) / sum(weights)
    )
    assert actual[0, 3] > 0  # Beyond the commented-out 1.4 cutoff.
    assert torch.equal(
        actual[labels[:, None] == labels[None, :]], torch.zeros(8, dtype=torch.float64)
    )
    torch.testing.assert_close(actual.sum(1), torch.ones(4, dtype=torch.float64))
    # Exact antipodes do not create inf/NaN probabilities.
    embeddings[-1] = -embeddings[0]
    assert torch.isfinite(distance_weighted_probabilities(embeddings, labels)).all()


@pytest.mark.parametrize("probability", [0.0, 1.0])
def test_random_switch_is_same_class_push_and_preserves_global_rng(probability):
    embeddings, labels, _ = batch()
    loss = RegularizedMarginLoss(recipe(switch_probability=probability), 2, 3)
    global_state = torch.get_rng_state().clone()
    before = loss.rng_state.clone()
    triplets = loss.sample_triplets(embeddings, labels)
    assert torch.equal(global_state, torch.get_rng_state())
    assert not torch.equal(before, loss.rng_state)
    anchor, positive, negative = triplets.unbind(1)
    if probability == 1:
        assert torch.equal(anchor, positive)
        assert (anchor != negative).all()
        assert torch.equal(labels[anchor], labels[negative])
    else:
        assert (anchor != positive).all()
        assert torch.equal(labels[anchor], labels[positive])
        assert (labels[anchor] != labels[negative]).all()
    loss.rng_state.copy_(before)
    assert torch.equal(triplets, loss.sample_triplets(embeddings, labels))
    loss.eval()
    assert torch.equal(
        loss.sample_triplets(embeddings, labels),
        loss.sample_triplets(embeddings, labels),
    )


def test_both_active_hinges_use_historical_source_union_denominator():
    loss = RegularizedMarginLoss(recipe(), 2, 3).double()
    values = torch.tensor(
        [[0.0, 0.0], [1.1, 0.0], [1.0, 0.0]], dtype=torch.float64, requires_grad=True
    )
    labels = torch.tensor([0, 0, 1])
    actual = loss.sampled_loss(values, labels, torch.tensor([[0, 1, 2]]))
    expected = math.sqrt(1.21 + 1e-8) - 1.2 + 0.2 + 1.2 - math.sqrt(1 + 1e-8) + 0.2
    assert actual.item() == pytest.approx(expected)
    assert actual.item() == pytest.approx(0.5)
    actual.backward()
    assert values.grad.abs().sum() > 0
    # The two active hinge derivatives cancel at this boundary.
    assert loss.beta.grad[0] == 0


def test_trainable_boundary_receives_only_active_hinge_gradient():
    loss = RegularizedMarginLoss(recipe(), 2, 3).double()
    values = torch.tensor([[0.0, 0.0], [1.8, 0.0], [2.0, 0.0]], dtype=torch.float64)
    loss.sampled_loss(
        values, torch.tensor([0, 0, 1]), torch.tensor([[0, 1, 2]])
    ).backward()
    torch.testing.assert_close(
        loss.beta.grad, torch.tensor([-1.0, 0.0], dtype=torch.float64)
    )


def test_kl_matches_teacher_to_student_including_self_and_stops_target_gradient():
    student = torch.tensor(
        [[1.0, 0.0], [0.0, 1.0]], dtype=torch.float64, requires_grad=True
    )
    teacher = torch.tensor(
        [[1.0, 0.0, 0.0], [0.6, 0.8, 0.0]], dtype=torch.float64, requires_grad=True
    )
    temperature = 2.0
    student_diagonal = math.exp(1 / temperature) / (math.exp(1 / temperature) + 1)
    teacher_diagonal = math.exp(1 / temperature) / (
        math.exp(1 / temperature) + math.exp(0.6 / temperature)
    )
    expected = temperature**2 * (
        teacher_diagonal * math.log(teacher_diagonal / student_diagonal)
        + (1 - teacher_diagonal)
        * math.log((1 - teacher_diagonal) / (1 - student_diagonal))
    )
    actual = similarity_distillation(student, teacher, temperature)
    assert actual.item() == pytest.approx(expected)
    actual.backward()
    assert student.grad.abs().sum() > 0
    assert teacher.grad is None


def test_motion_pooling_is_sum_of_valid_mean_and_max_preserving_joint_order():
    features = torch.tensor(
        [
            [
                [[[1.0, 2.0], [9.0, 9.0]], [[3.0, 6.0], [8.0, 8.0]]],
                [[[5.0, 10.0], [7.0, 7.0]], [[99.0, 99.0], [6.0, 6.0]]],
            ]
        ]
    )
    valid = torch.tensor(
        [[[[True, False], [True, False]], [[True, False], [False, False]]]]
    )
    torch.testing.assert_close(
        auxiliary_features(features, valid), torch.tensor([[8.0, 16.0, 0.0, 0.0]])
    )


def test_total_objective_and_delayed_feature_signal_exactly_follow_recipe():
    student, labels, pooled = batch()
    criterion = S2SDLoss(recipe(feature_delay=2), 2).double()
    criterion.eval()
    student.requires_grad_()
    pooled.requires_grad_()
    parts = criterion.loss_components(student, labels, pooled)
    expected = (
        0.5 * (parts["student_margin"] + parts["teacher_margin"])
        + 50 * parts["teacher_distillation"]
    )
    torch.testing.assert_close(criterion(student, labels, pooled), expected)
    assert parts["feature_distillation"] == 0
    criterion.completed_steps.fill_(2)
    active = criterion.loss_components(student, labels, pooled)
    assert active["feature_distillation"] > 0
    torch.testing.assert_close(
        criterion(student, labels, pooled),
        expected + 50 * active["feature_distillation"],
    )
    active["teacher_distillation"].backward(retain_graph=True)
    assert student.grad.abs().sum() > 0
    assert pooled.grad is None
    assert all(
        parameter.grad is None
        for net in criterion.teachers
        for parameter in net.parameters()
    )
    active["teacher_margin"].backward()
    assert pooled.grad.abs().sum() > 0
    assert all(
        any(parameter.grad.abs().sum() > 0 for parameter in net.parameters())
        for net in criterion.teachers
    )


def test_feature_distillation_first_active_update_is_delay_plus_one():
    criterion = S2SDLoss(recipe(feature_delay=2), 2).double()
    student, labels, pooled = batch()
    for completed in range(3):
        assert criterion.completed_steps.item() == completed
        # Component inspection does not change the distillation counter.
        parts = criterion.loss_components(student, labels, pooled)
        assert (parts["feature_distillation"] > 0).item() == (completed >= 2)
        criterion(student, labels, pooled)
    assert criterion.completed_steps.item() == 3


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(3, 3)
        self.calls = 0

    def get_representation(self, poses):
        self.calls += 1
        return self.projection(poses)


def optimizer(model, criterion):
    return torch.optim.AdamW(
        [
            {"params": [p for p in model.parameters() if p.requires_grad], "lr": 0.01},
            *criterion.parameter_groups(0.01, 0.001),
        ]
    )


@pytest.mark.parametrize("fine_tune", [False, True])
def test_single_encoder_pass_updates_components_and_retrieves_student_only(
    fine_tune,
):
    torch.manual_seed(73)
    model = MotionRetrievalModel(
        TinyEncoder(),
        embedding_dimension=4,
        representation_dimension=3,
        joints=2,
        train_encoder=fine_tune,
    ).double()
    criterion = build_loss("s2sd", recipe(feature_delay=0).model_dump(), 2).double()
    optim = optimizer(model, criterion)
    assert [group["lr"] for group in optim.param_groups] == [0.01, 0.01, 0.0005]
    assert optim.param_groups[-1]["weight_decay"] == 0
    assert {id(p) for group in optim.param_groups for p in group["params"]} == {
        id(p) for p in [*model.parameters(), *criterion.parameters()] if p.requires_grad
    }
    poses = torch.randn(8, 2, 3, 2, 3, dtype=torch.float64)
    poses[..., 2] = 1
    labels = torch.arange(2).repeat_interleave(4)
    encoder_before = copy.deepcopy(model.encoder.state_dict())
    before = copy.deepcopy(criterion.state_dict())
    head_before = copy.deepcopy(model.head.state_dict())
    assert math.isfinite(optimizer_step(model, criterion, optim, poses, labels))
    assert model.encoder.calls == 1
    assert (
        any(
            not torch.equal(encoder_before[k], v)
            for k, v in model.encoder.state_dict().items()
        )
        == fine_tune
    )
    assert any(
        not torch.equal(head_before[k], v) for k, v in model.head.state_dict().items()
    )
    assert all(
        not torch.equal(
            before[f"teachers.{index}.0.weight"],
            criterion.state_dict()[f"teachers.{index}.0.weight"],
        )
        for index in range(4)
    )
    assert any(
        not torch.equal(before[name], value)
        for name, value in criterion.state_dict().items()
        if name.endswith("beta")
    )
    assert criterion.completed_steps.item() == 1
    model.eval()
    torch.testing.assert_close(model(poses)[:1], model(poses[:1]))
    torch.testing.assert_close(
        model(poses).norm(dim=1), torch.ones(8, dtype=torch.float64)
    )
    assert not any("teacher" in key for key in model.state_dict())


def test_checkpoint_restores_next_sampling_objective_and_optimizer_update():
    torch.manual_seed(13)
    original = S2SDLoss(recipe(feature_delay=1), 2).double()
    student, labels, pooled = batch()
    optim = torch.optim.AdamW(original.parameter_groups(0.01, 0.001))
    original(student, labels, pooled).backward()
    optim.step()
    state = copy.deepcopy(original.state_dict())
    original.validate_checkpoint_state(state, 1)
    restored = S2SDLoss(recipe(feature_delay=1), 2).double()
    restored.load_state_dict(state)
    resumed_optim = torch.optim.AdamW(restored.parameter_groups(0.01, 0.001))
    resumed_optim.load_state_dict(copy.deepcopy(optim.state_dict()))
    values = []
    for module, optimizer in [(original, optim), (restored, resumed_optim)]:
        optimizer.zero_grad(set_to_none=True)
        value = module(student, labels, pooled)
        value.backward()
        optimizer.step()
        values.append(value)
    assert torch.equal(*values)
    assert all(
        torch.equal(value, restored.state_dict()[key])
        for key, value in original.state_dict().items()
    )
    with pytest.raises(ValueError, match="counter"):
        original.validate_checkpoint_state(state, 2)
    state["student_objective.rng_state"] = torch.zeros(1, dtype=torch.uint8)
    with pytest.raises(ValueError, match="sampling state"):
        original.validate_checkpoint_state(state, 1)


def test_registry_declares_paper_variant_and_teacher_shapes():
    spec = load_methods()["s2sd"]
    assert spec.status == "implemented" and spec.family == "architecture"
    config = S2SDParameters.model_validate(spec.parameters)
    assert config.target_dimensions == (512, 1024, 1536, 2048)
    assert config.feature_delay == 1000
    assert config.switch_probability == 0.4
    assert config.distillation_weight == config.feature_weight == 50
    criterion = S2SDLoss(recipe(), 2)
    for dimension, teacher in zip((4, 6, 8, 10), criterion.teachers, strict=True):
        assert teacher[0].weight.shape == (dimension, 6)
        assert isinstance(teacher[1], nn.ReLU)
        assert teacher[2].weight.shape == (dimension, dimension)
    assert (
        len(
            {
                bytes(loss.rng_state.tolist())
                for loss in [criterion.student_objective, *criterion.teacher_objectives]
            }
        )
        == 5
    )


@pytest.mark.parametrize(
    "fault", ["labels", "features", "student", "nan", "singletons"]
)
def test_invalid_training_inputs_fail_closed(fault):
    criterion = S2SDLoss(recipe(), 2).double()
    student, labels, pooled = batch()
    if fault == "labels":
        labels += 100
    elif fault == "features":
        pooled = pooled[:, :-1]
    elif fault == "student":
        student = student[:, :-1]
    elif fault == "nan":
        student[0, 0] = torch.nan
    else:
        labels[:] = 0
        labels[0] = 1
    with pytest.raises(ValueError):
        criterion(student, labels, pooled)
