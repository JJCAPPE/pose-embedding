from __future__ import annotations

import copy

import pytest
import torch
from pydantic import ValidationError
from torch import nn
from torch.nn import functional as F

from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.model import MaskedMaxHead, MotionRetrievalModel
from pose_embed.benchmark.proxy_nca_plus import (
    ProxyNCAPlusLoss,
    ProxyNCAPlusParameters,
)
from pose_embed.benchmark.training import (
    build_optimizer,
    phase_for_step,
    resolve_recipe,
)


def test_all_proxy_probability_matches_squared_distance_oracle_and_gradients():
    values = torch.tensor(
        [[1.0, 0.3, -0.2], [0.8, -0.1, 0.4], [-0.2, 0.3, 1.0], [0.1, 0.5, 0.7]],
        dtype=torch.float64,
        requires_grad=True,
    )
    proxies = torch.tensor(
        [[1.0, 0.4, -0.2], [-0.3, 1.0, 0.5], [0.2, -0.4, 1.0]],
        dtype=torch.float64,
    )
    labels = torch.tensor([0, 0, 2, 2])
    criterion = ProxyNCAPlusLoss(embedding_dimension=3, num_classes=3).double()
    with torch.no_grad():
        criterion.proxies.copy_(proxies)
    oracle_values = values.detach().clone().requires_grad_()
    oracle_proxies = proxies.clone().requires_grad_()
    distances = (
        (
            F.normalize(oracle_values, dim=1)[:, None]
            - F.normalize(oracle_proxies, dim=1)[None]
        )
        .square()
        .sum(dim=-1)
    )
    logits = -distances / (1 / 9)
    expected = (logits.logsumexp(dim=1) - logits[torch.arange(4), labels]).mean()
    actual = criterion(values, labels)
    torch.testing.assert_close(actual, expected)
    expected_gradients = torch.autograd.grad(expected, (oracle_values, oracle_proxies))
    actual_gradients = torch.autograd.grad(actual, (values, criterion.proxies))
    for actual_gradient, expected_gradient in zip(
        actual_gradients, expected_gradients, strict=True
    ):
        torch.testing.assert_close(actual_gradient, expected_gradient)
    # Class 1 is absent from this batch but remains in the global denominator.
    assert actual_gradients[1][1].norm() > 0
    with torch.no_grad():
        criterion.proxies.mul_(7)
    torch.testing.assert_close(criterion(values * 3, labels), actual)


def test_proxy_initialization_has_declared_scale_and_registered_state():
    torch.manual_seed(17)
    criterion = ProxyNCAPlusLoss(embedding_dimension=128, num_classes=512)
    assert isinstance(criterion.proxies, nn.Parameter)
    assert criterion.proxies.shape == (512, 128)
    assert abs(criterion.proxies.mean().item()) < 0.002
    assert criterion.proxies.std().item() == pytest.approx(0.125, rel=0.02)
    assert "proxies" in criterion.state_dict()


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_proxy_parameters_reject_invalid_temperature(value):
    with pytest.raises(ValidationError):
        ProxyNCAPlusParameters(temperature=value)


def test_masked_max_precedes_non_affine_norm_and_projection_with_zero_fallback():
    head = MaskedMaxHead(embedding_dimension=3, representation_dimension=3).double()
    with torch.no_grad():
        head.projection.weight.copy_(torch.eye(3, dtype=torch.float64))
        head.projection.bias.copy_(torch.tensor([1.0, -1.0, 0.5]))
    features = torch.full((2, 2, 2, 2, 3), 10000.0, dtype=torch.float64)
    features[0, 0, 0, 0] = torch.tensor([-3.0, -1.0, -4.0])
    features[0, 0, 1, 1] = torch.tensor([-2.0, -5.0, -6.0])
    features.requires_grad_()
    valid = torch.zeros(features.shape[:-1], dtype=torch.bool)
    valid[0, 0, 0, 0] = valid[0, 0, 1, 1] = True
    pooled = torch.tensor([[-2.0, -1.0, -4.0], [0.0, 0.0, 0.0]], dtype=torch.float64)
    normalized = F.layer_norm(pooled, (3,), eps=head.normalization.eps)
    expected = F.normalize(
        F.linear(normalized, head.projection.weight, head.projection.bias), dim=-1
    )
    actual = head(features, valid)
    torch.testing.assert_close(actual, expected)
    assert head.normalization.elementwise_affine is False
    assert not list(head.normalization.parameters())
    assert torch.isfinite(actual).all()
    torch.testing.assert_close(actual.norm(dim=-1), torch.ones(2, dtype=torch.float64))
    (actual * torch.tensor([1.0, 2.0, 3.0])).sum().backward()
    assert torch.equal(features.grad[~valid], torch.zeros_like(features.grad[~valid]))
    assert features.grad[valid].norm() > 0


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 4)
        self.head = nn.Linear(4, 3)

    def get_representation(self, poses):
        return self.linear(poses)


def _model():
    return MotionRetrievalModel(
        TinyEncoder(),
        embedding_dimension=8,
        representation_dimension=4,
        joints=2,
        method_id="proxy_nca_pp",
    )


def _recipe(encoder_mode="finetune", **kwargs):
    training = load_benchmark().training.model_copy(
        update={"encoder_mode": encoder_mode}
    )
    return resolve_recipe(
        "proxy_nca_pp",
        ProxyNCAPlusParameters().model_dump(),
        training,
        num_records=64,
        **kwargs,
    )


def _batch():
    poses = torch.randn(4, 2, 3, 2, 3)
    poses[..., 2] = 1
    return poses, torch.tensor([0, 0, 1, 1])


def _step(model, criterion, optimizer, batch):
    optimizer.zero_grad(set_to_none=True)
    value = criterion(model(batch[0]), batch[1])
    value.backward()
    optimizer.step()


def test_motion_model_masks_confidence_and_preserves_unused_pose_head_freeze():
    model = _model()
    poses, _ = _batch()
    poses[:, 1, ..., 2] = 0
    poses[0, 0, 0, 0, 2] = -1
    represented = model.encoder.get_representation(poses.reshape(8, 3, 2, 3))
    expected = model.head(represented.reshape(4, 2, 3, 2, 4), poses[..., 2] > 0)
    torch.testing.assert_close(model(poses), expected)
    model.set_encoder_trainable(False)
    model.train()
    assert model.encoder.training is False
    assert not any(p.requires_grad for p in model.encoder.parameters())
    model.set_encoder_trainable(True)
    model.train()
    assert model.encoder.training is True
    assert all(p.requires_grad for p in model.encoder.linear.parameters())
    assert not any(p.requires_grad for p in model.encoder.head.parameters())


def test_fast_proxy_optimizer_groups_update_and_state_restore():
    torch.manual_seed(7)
    model = _model()
    criterion = ProxyNCAPlusLoss(embedding_dimension=8, num_classes=2)
    recipe = _recipe()
    optimizer = build_optimizer(model, criterion, recipe, "main")
    assert type(optimizer) is torch.optim.Adam
    assert recipe["head_learning_rate"] == 0.004
    assert recipe["proxy_learning_rate"] == 400
    assert recipe["optimizer_epsilon"] == 1
    members = [p for group in optimizer.param_groups for p in group["params"]]
    assert len({id(p) for p in members}) == len(members)
    assert {id(p) for p in members} == {
        id(p) for p in [*model.parameters(), *criterion.parameters()] if p.requires_grad
    }
    proxy_group = next(
        g
        for g in optimizer.param_groups
        if any(p is criterion.proxies for p in g["params"])
    )
    assert proxy_group["lr"] == 400
    for group in optimizer.param_groups:
        assert group["eps"] == 1
        assert group["weight_decay"] == 0
        if group is not proxy_group:
            assert group["lr"] == 0.004
    batch = _batch()
    old_proxies = criterion.proxies.detach().clone()
    old_head = model.head.projection.weight.detach().clone()
    _step(model, criterion, optimizer, batch)
    assert not torch.equal(criterion.proxies, old_proxies)
    assert not torch.equal(model.head.projection.weight, old_head)
    restored_model, restored_criterion = copy.deepcopy(model), copy.deepcopy(criterion)
    restored_optimizer = build_optimizer(
        restored_model, restored_criterion, recipe, "main"
    )
    restored_optimizer.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    _step(model, criterion, optimizer, batch)
    _step(restored_model, restored_criterion, restored_optimizer, batch)
    for current, restored in zip(
        model.parameters(), restored_model.parameters(), strict=True
    ):
        torch.testing.assert_close(current, restored, rtol=0, atol=0)
    torch.testing.assert_close(
        criterion.proxies, restored_criterion.proxies, rtol=0, atol=0
    )


def test_five_complete_warmup_epochs_then_encoder_updates():
    torch.manual_seed(29)
    recipe = _recipe()
    assert recipe["warmup_steps"] == 10
    assert recipe["minimum_selected_step"] == 11
    assert phase_for_step(recipe, 1) == "warmup"
    assert phase_for_step(recipe, 10) == "warmup"
    assert phase_for_step(recipe, 11) == "main"
    model = _model()
    criterion = ProxyNCAPlusLoss(embedding_dimension=8, num_classes=2)
    before = copy.deepcopy(model.encoder.state_dict())
    warmup = build_optimizer(model, criterion, recipe, "warmup")
    batch = _batch()
    for _ in range(recipe["warmup_steps"]):
        _step(model, criterion, warmup, batch)
    for name, value in model.encoder.state_dict().items():
        torch.testing.assert_close(value, before[name], rtol=0, atol=0)
    main = build_optimizer(model, criterion, recipe, "main")
    assert not main.state
    _step(model, criterion, main, batch)
    assert not torch.equal(model.encoder.linear.weight, before["linear.weight"])
    torch.testing.assert_close(
        model.encoder.head.weight, before["head.weight"], rtol=0, atol=0
    )


def test_frozen_track_does_not_enable_encoder_in_main_phase():
    model = _model()
    criterion = ProxyNCAPlusLoss(embedding_dimension=8, num_classes=2)
    optimizer = build_optimizer(model, criterion, _recipe("frozen"), "main")
    before = copy.deepcopy(model.encoder.state_dict())
    _step(model, criterion, optimizer, _batch())
    assert model.encoder.training is False
    for name, value in model.encoder.state_dict().items():
        torch.testing.assert_close(value, before[name], rtol=0, atol=0)


def test_recipe_preserves_full_warmup_and_covers_larger_final_population():
    training = load_benchmark().training.model_copy(
        update={"encoder_mode": "finetune", "steps": 2, "validation_every": 1}
    )
    recipe = resolve_recipe(
        "proxy_nca_pp",
        ProxyNCAPlusParameters().model_dump(),
        training,
        num_records=65,
        selection_num_records=129,
    )
    assert recipe["warmup_steps"] == 15
    assert recipe["minimum_selected_step"] == 26
    assert phase_for_step(recipe, 15) == "warmup"
    assert phase_for_step(recipe, 16) == "main"


def test_profile_uses_explicit_post_warmup_phase_and_encoder_backward():
    torch.manual_seed(43)
    recipe = _recipe(profile=True)
    assert recipe["profile_phase"] == "post_warmup_capacity"
    assert recipe["profile_executes_warmup"] is False
    assert recipe["warmup_steps"] == 10
    assert phase_for_step(recipe, 1) == "main"
    model = _model()
    criterion = ProxyNCAPlusLoss(embedding_dimension=8, num_classes=2)
    optimizer = build_optimizer(model, criterion, recipe, phase_for_step(recipe, 1))
    before = model.encoder.linear.weight.detach().clone()
    _step(model, criterion, optimizer, _batch())
    assert model.encoder.linear.weight.grad is not None
    assert model.encoder.linear.weight.grad.norm() > 0
    assert not torch.equal(model.encoder.linear.weight, before)
