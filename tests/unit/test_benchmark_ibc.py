"""IBC graph equations, both supervision paths, and checkpoint state."""

from __future__ import annotations

import math

import pytest
import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.benchmark.ibc import (
    IBCMessageLayer,
    IBCParameters,
    IntraBatchAttention,
    IntraBatchConnectionsLoss,
)
from pose_embed.benchmark.losses import build_loss


def test_messages_match_complete_graph_with_self_and_null_message():
    attention = IntraBatchAttention(4, 2, dropout=0).double()
    with torch.no_grad():
        for layer in (
            attention.query,
            attention.key,
            attention.value,
            attention.output,
        ):
            layer.weight.copy_(torch.eye(4))
            layer.bias.zero_()
    values = torch.tensor([[1.0, 0, 2, 0], [0, 1, 0, 3]], dtype=torch.float64)
    heads, matrices = [], []
    for start in (0, 2):
        nodes = values[:, start : start + 2]
        weights = torch.empty(2, 2, dtype=torch.float64)
        for receiver in range(2):
            scores = torch.stack(
                [
                    torch.dot(nodes[receiver], nodes[sender]) / math.sqrt(2)
                    for sender in range(2)
                ]
            ).exp()
            weights[receiver] = scores / (1 + scores.sum())
        matrices.append(weights)
        heads.append(weights @ nodes)
    torch.testing.assert_close(
        attention.attention_weights(values), torch.stack(matrices)
    )
    torch.testing.assert_close(attention(values), torch.cat(heads, dim=1))
    assert (torch.diagonal(torch.stack(matrices), dim1=1, dim2=2) > 0).all()
    assert (torch.stack(matrices).sum(-1) < 1).all()


def test_zero_attention_keeps_explicit_null_probability_and_is_finite():
    attention = IntraBatchAttention(4, 2, dropout=0).double()
    nodes = torch.zeros(3, 4, dtype=torch.float64)
    torch.testing.assert_close(
        attention.attention_weights(nodes), torch.full((2, 3, 3), 0.25).double()
    )
    huge = torch.full((3, 4), 1e10, dtype=torch.float64)
    assert torch.isfinite(attention(huge)).all()


def test_message_block_preserves_both_residual_layernorm_steps():
    block = IBCMessageLayer(IBCParameters(embedding_dimension=4, dropout=0)).double()
    with torch.no_grad():
        for parameter in block.attention.parameters():
            parameter.zero_()
        for parameter in block.feedforward.parameters():
            parameter.zero_()
        block.feedforward[-1].bias.copy_(torch.tensor([1.0, -1.0, 0.0, 2.0]))
    nodes = torch.tensor([[1.0, 0, 2, -1], [0, 3, -2, 1]], dtype=torch.float64)
    first = functional.layer_norm(nodes, (4,), eps=1e-5)
    expected = functional.layer_norm(
        first + torch.tensor([1.0, -1.0, 0.0, 2.0]), (4,), eps=1e-5
    )
    torch.testing.assert_close(block(nodes), expected)


def test_graph_and_loss_are_permutation_equivariant_with_dropout_disabled():
    torch.manual_seed(17)
    loss = IntraBatchConnectionsLoss(
        IBCParameters(embedding_dimension=8, dropout=0), 3
    ).double()
    nodes = torch.randn(12, 8, dtype=torch.float64)
    labels = torch.arange(3).repeat_interleave(4)
    permutation = torch.randperm(12)
    torch.testing.assert_close(
        loss.refine(nodes)[permutation], loss.refine(nodes[permutation])
    )
    torch.testing.assert_close(
        loss(nodes, labels), loss(nodes[permutation], labels[permutation])
    )


def test_classifier_components_match_smoothed_temperature_cross_entropy():
    loss = (
        IntraBatchConnectionsLoss(IBCParameters(embedding_dimension=4, dropout=0), 2)
        .double()
        .eval()
    )
    nodes = torch.tensor([[1.0, 0, 2, -1], [0, 3, -2, 1]], dtype=torch.float64)
    labels = torch.tensor([0, 1])
    components = loss.loss_components(nodes, labels)
    targets = 0.9 * functional.one_hot(labels, 2) + 0.1 / 2
    for name, logits in (
        ("refined", loss.refined_classifier(loss.refined_neck(loss.refine(nodes)))),
        ("auxiliary", loss.auxiliary_classifier(nodes)),
    ):
        expected = (
            -(targets * functional.log_softmax(logits / 0.2, dim=1)).sum(1).mean()
        )
        torch.testing.assert_close(components[name], expected)
    torch.testing.assert_close(loss(nodes, labels), sum(components.values()))
    # Only the graph branch uses unit vectors; raw auxiliary CE retains scale.
    torch.testing.assert_close(loss.refine(nodes), loss.refine(nodes * 3))
    assert not torch.isclose(
        components["auxiliary"], loss.loss_components(nodes * 3, labels)["auxiliary"]
    )


@pytest.mark.parametrize("component", ["refined", "auxiliary"])
def test_each_supervision_path_reaches_backbone_inputs_and_its_classifier(component):
    torch.manual_seed(23)
    loss = IntraBatchConnectionsLoss(
        IBCParameters(embedding_dimension=8, dropout=0), 3
    ).double()
    nodes = torch.randn(12, 8, dtype=torch.float64, requires_grad=True)
    labels = torch.arange(3).repeat_interleave(4)
    loss.loss_components(nodes, labels)[component].backward()
    assert nodes.grad is not None and nodes.grad.abs().sum() > 0
    classifier = getattr(loss, f"{component}_classifier")
    assert classifier.weight.grad is not None and classifier.weight.grad.abs().sum() > 0
    if component == "refined":
        assert loss.input_projection.weight.grad.abs().sum() > 0
        attention = loss.message_layers[0].attention
        for projection in (
            attention.query,
            attention.key,
            attention.value,
            attention.output,
        ):
            assert projection.weight.grad.abs().sum() > 0


def test_all_trainable_components_and_batchnorm_state_restore():
    torch.manual_seed(11)
    parameters = {"embedding_dimension": 8, "dropout": 0.0}
    loss = build_loss("ibc", parameters, 3).double()
    assert loss.requires_raw_embeddings
    nodes = torch.randn(12, 8, dtype=torch.float64)
    labels = torch.arange(3).repeat_interleave(4)
    before = {name: value.clone() for name, value in loss.named_parameters()}
    optimizer = torch.optim.AdamW(loss.parameters(), lr=0.01)
    loss(nodes, labels).backward()
    optimizer.step()
    for prefix in (
        "loss.input_projection",
        "loss.message_layers",
        "loss.refined_neck",
        "loss.refined_classifier",
        "loss.auxiliary_classifier",
    ):
        assert any(
            name.startswith(prefix) and not torch.equal(value, before[name])
            for name, value in loss.named_parameters()
        )
    assert loss.loss.refined_neck.num_batches_tracked == 1
    assert not loss.loss.refined_neck.bias.requires_grad
    restored = build_loss("ibc", parameters, 3).double()
    restored.load_state_dict(loss.state_dict(), strict=True)
    loss.eval()
    restored.eval()
    torch.testing.assert_close(
        loss(nodes, labels), restored(nodes, labels), rtol=0, atol=0
    )
    for name, value in loss.state_dict().items():
        torch.testing.assert_close(value, restored.state_dict()[name], rtol=0, atol=0)
    with pytest.raises(ValueError, match="globally"):
        loss(nodes, labels + 20)


def test_dropout_locations_follow_active_source_recipe():
    loss = IntraBatchConnectionsLoss(IBCParameters(embedding_dimension=8), 3)
    assert [m.p for m in loss.modules() if isinstance(m, nn.Dropout)] == [0.1] * 4
