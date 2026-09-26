"""Analytical HIST graphs, supervision, state and warmup transitions."""

import copy

import pytest
import torch
import torch.nn.functional as F
from torch import nn

from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.hist import (
    HISTHead,
    HISTParameters,
    HypergraphSemanticTupletLoss,
    SemanticDistributions,
    hypergraph_propagation,
)
from pose_embed.benchmark.losses import build_loss
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import _checkpoint_state, optimizer_step
from pose_embed.benchmark.runtime import _verify_proxy_optimizer
from pose_embed.benchmark.training import (
    advance_optimizer,
    build_optimizer,
    hist_learning_rates,
    resolve_recipe,
    set_step_learning_rates,
)


def test_mahalanobis_and_present_class_semantic_weights():
    distributions = SemanticDistributions(2, 3).double()
    with torch.no_grad():
        distributions.means.copy_(torch.tensor([[1.0, 0], [0, 1], [-1, 0]]))
        distributions.log_variances.copy_(torch.tensor([[0.0, 0], [0, 0], [1, 1]]))
    features = torch.tensor([[1.0, 0], [-1, 0]], dtype=torch.float64)
    labels = torch.tensor([0, 2])
    expected_distances = torch.tensor(
        [[0.0, 2, 4 / torch.e], [4, 2, 0]], dtype=torch.float64
    )
    torch.testing.assert_close(
        distributions.squared_distances(features), expected_distances
    )
    loss, incidence = distributions(features, labels, 32, 1.1)
    torch.testing.assert_close(loss, F.cross_entropy(-32 * expected_distances, labels))
    expected = (-1.1 * expected_distances[:, [0, 2]]).exp()
    expected[0, 0] = expected[1, 1] = 1
    torch.testing.assert_close(incidence, expected)


def test_hypergraph_normalization_matches_explicit_degree_matrices():
    incidence = torch.tensor(
        [[1.0, 0.2], [0.5, 1], [1, 0.4]], dtype=torch.float64, requires_grad=True
    )
    dv = torch.diag(incidence.sum(1).rsqrt())
    de = torch.diag(1 / incidence.sum(0))
    expected = dv @ incidence @ de @ incidence.T @ dv
    actual = hypergraph_propagation(incidence)
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(actual, actual.T)
    degree_vector = incidence.sum(1).sqrt()
    torch.testing.assert_close(actual @ degree_vector, degree_vector)
    assert torch.autograd.grad(actual[0, 1], incidence)[0].abs().sum() > 0
    with pytest.raises(ValueError, match="positive"):
        hypergraph_propagation(torch.zeros(2, 2))


@pytest.mark.parametrize("component", ["distribution", "graph"])
def test_both_losses_train_features_and_distributions(component):
    torch.manual_seed(7)
    criterion = HypergraphSemanticTupletLoss(
        HISTParameters(embedding_dimension=4, hidden_dimension=8), 3
    ).double()
    nodes = torch.randn(12, 4, dtype=torch.float64, requires_grad=True)
    labels = torch.arange(3).repeat_interleave(4)
    criterion.loss_components(nodes, labels)[component].backward()
    assert nodes.grad.abs().sum() > 0
    assert criterion.distributions.means.grad.abs().sum() > 0
    assert criterion.distributions.log_variances.grad.abs().sum() > 0
    if component == "graph":
        assert criterion.graph.hidden.weight.grad.abs().sum() > 0
        assert criterion.graph.output.weight.grad.abs().sum() > 0


def test_hypergraph_permutation_equivariance_and_raw_feature_scale():
    torch.manual_seed(23)
    criterion = (
        HypergraphSemanticTupletLoss(
            HISTParameters(embedding_dimension=4, hidden_dimension=8), 3
        )
        .double()
        .eval()
    )
    nodes = torch.randn(12, 4, dtype=torch.float64)
    labels = torch.arange(3).repeat_interleave(4)
    permutation = torch.randperm(12)
    torch.testing.assert_close(
        criterion(nodes, labels), criterion(nodes[permutation], labels[permutation])
    )
    a, b = (
        criterion.loss_components(nodes, labels),
        criterion.loss_components(nodes * 3, labels),
    )
    torch.testing.assert_close(a["distribution"], b["distribution"])
    assert not torch.isclose(a["graph"], b["graph"])


def test_head_mean_plus_max_then_projection_then_layer_norm():
    head = HISTHead(3, 3).double()
    with torch.no_grad():
        head.projection.weight.copy_(torch.diag(torch.tensor([1.0, 2, 3])))
        head.projection.bias.copy_(torch.tensor([1.0, 0, -1]))
    features = torch.tensor(
        [[[[[1.0, 2, 3], [3, 1, -2], [1e9, 1e9, 1e9]]]]],
        dtype=torch.float64,
        requires_grad=True,
    )
    valid = torch.tensor([[[[True, True, False]]]])
    pooled = torch.tensor([[5.0, 3.5, 3.5]], dtype=torch.float64)
    expected = F.layer_norm(
        F.linear(pooled, head.projection.weight, head.projection.bias), (3,)
    )
    torch.testing.assert_close(head.forward_raw(features, valid), expected)
    head(features, valid)[0, 0].backward()
    assert torch.equal(
        features.grad[..., 2, :], torch.zeros_like(features.grad[..., 2, :])
    )
    assert torch.isfinite(head(features, torch.zeros_like(valid))).all()


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 4)
        self.head = nn.Linear(4, 3)

    def get_representation(self, poses):
        return self.linear(poses)


def test_warmup_preserves_adam_moments_schedule_and_full_checkpoint():
    torch.manual_seed(7)
    model = MotionRetrievalModel(
        TinyEncoder(),
        method_id="hist",
        representation_dimension=4,
        embedding_dimension=8,
    )
    criterion = build_loss("hist", {"embedding_dimension": 8, "hidden_dimension": 8}, 2)
    training = load_benchmark().training.model_copy(update={"encoder_mode": "finetune"})
    recipe = resolve_recipe("hist", {}, training, 32, selection_num_records=64)
    assert recipe["warmup_steps"] == 1 and recipe["minimum_selected_step"] == 3
    optimizer = build_optimizer(model, criterion, recipe, "warmup")
    poses = torch.randn(8, 2, 3, 2, 3)
    poses[..., 2] = 1
    labels = torch.arange(2).repeat_interleave(4)
    initial_encoder = copy.deepcopy(model.encoder.state_dict())
    optimizer_step(model, criterion, optimizer, poses, labels)
    assert all(
        torch.equal(v, initial_encoder[k])
        for k, v in model.encoder.state_dict().items()
    )
    assert optimizer.state[model.head.projection.weight]["step"] == 1
    assert advance_optimizer(model, criterion, optimizer, recipe, "main") is optimizer
    set_step_learning_rates(optimizer, recipe, 2)
    optimizer_step(model, criterion, optimizer, poses, labels)
    assert optimizer.state[model.head.projection.weight]["step"] == 2
    assert optimizer.state[model.encoder.linear.weight]["step"] == 1
    assert not torch.equal(
        model.encoder.linear.weight, initial_encoder["linear.weight"]
    )
    assert hist_learning_rates(recipe, 6)["head"] == recipe["head_learning_rate"]
    assert hist_learning_rates(recipe, 7)["head"] == recipe["head_learning_rate"] / 2
    checkpoint = _checkpoint_state(model, criterion, optimizer, recipe, 2, "main")
    checkpoint["selected_step"] = 2
    encoder_parameters = tuple(name for name, _ in model.encoder.named_parameters())
    _verify_proxy_optimizer(checkpoint, recipe, encoder_parameters)
    corrupt = copy.deepcopy(checkpoint)
    del corrupt["optimizer"]["state"][
        corrupt["optimizer"]["param_groups"][3]["params"][0]
    ]
    with pytest.raises(ValueError, match="missing required"):
        _verify_proxy_optimizer(corrupt, recipe, encoder_parameters)
    restored = build_loss("hist", {"embedding_dimension": 8, "hidden_dimension": 8}, 2)
    restored.load_state_dict(checkpoint["criterion"], strict=True)
    criterion.eval()
    restored.eval()
    model.eval()
    torch.testing.assert_close(
        criterion(model.forward_raw(poses), labels),
        restored(model.forward_raw(poses), labels),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(model(poses)[:1], model(poses[:1]), atol=1e-6, rtol=1e-5)
