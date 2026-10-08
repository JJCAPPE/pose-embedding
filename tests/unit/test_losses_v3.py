from __future__ import annotations

import math

import pytest
import torch

from pose_embed.losses.contextual import (
    ContextualLossConfig,
    ContextualMetricLoss,
    GreaterThanSTE,
    contextual_similarity,
)
from pose_embed.losses.pairwise import (
    PairwiseContrastiveLoss,
    SupervisedContrastiveLoss,
)


def test_hand_calculated_contrastive_value_and_embedding_backward():
    # Four active positive hinges average 0.9; four active negative hinges
    # average 0.4. Only the orthogonal positives have a nonzero tangent gradient.
    values = torch.tensor(
        [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 1, 0, 1])
    loss = PairwiseContrastiveLoss(positive_margin=0.9, negative_margin=0.6)(
        values, labels
    )
    assert float(loss.detach()) == pytest.approx(13 / 10)
    loss.backward()
    expected = torch.tensor(
        [[0, -1 / 2], [0, -1 / 2], [-1 / 2, 0], [-1 / 2, 0]],
        dtype=torch.float64,
    )
    torch.testing.assert_close(values.grad, expected, atol=1e-12, rtol=1e-12)


def test_inactive_contrastive_hinges_have_zero_loss_and_gradient():
    values = torch.tensor(
        [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    loss = PairwiseContrastiveLoss(positive_margin=0.9, negative_margin=0.6)(
        values, torch.tensor([0, 0, 1, 1])
    )
    assert float(loss.detach()) == 0
    loss.backward()
    torch.testing.assert_close(values.grad, torch.zeros_like(values))


def test_hand_calculated_supcon_value_and_embedding_backward():
    # Each anchor has three collinear and four orthogonal alternatives;
    # its three positives contain one collinear and two orthogonal rows.
    # D=3*exp(1/T)+4, L=log(D)-1/(3T). The tangent gradient includes both
    # anchor and candidate roles: 2*(4/D-2/3)/(8T)=(1/D-1/6)/T.
    values = (
        torch.eye(2, dtype=torch.float64).repeat_interleave(4, dim=0).requires_grad_()
    )
    labels = torch.tensor([0, 1, 0, 1, 0, 1, 0, 1])
    temperature = 0.07
    denominator = 3 * math.exp(1 / temperature) + 4
    loss = SupervisedContrastiveLoss(temperature=temperature)(values, labels)
    assert float(loss.detach()) == pytest.approx(
        math.log(denominator) - 1 / (3 * temperature), abs=1e-12, rel=1e-12
    )
    loss.backward()
    tangent = (1 / denominator - 1 / 6) / temperature
    expected = torch.tensor(
        [[0, tangent]] * 4 + [[tangent, 0]] * 4, dtype=torch.float64
    )
    torch.testing.assert_close(values.grad, expected, atol=1e-12, rtol=1e-12)


def test_comparison_backward_uses_constant_alpha_including_ties():
    x = torch.tensor([0.0, 1.0, 2.0], requires_grad=True)
    y = torch.tensor([1.0, 1.0, 1.0], requires_grad=True)
    result = GreaterThanSTE.apply(x, y, 10.0)
    result.backward(torch.tensor([2.0, -3.0, 4.0]))
    torch.testing.assert_close(result, torch.tensor([0.0, 1.0, 1.0]))
    torch.testing.assert_close(x.grad, torch.tensor([20.0, -30.0, 40.0]))
    torch.testing.assert_close(y.grad, torch.tensor([-20.0, 30.0, -40.0]))


def test_hand_calculated_contextual_value_and_embedding_backward():
    # Two duplicate orthogonal pairs give W=A=diag(J2,J2), with opposite
    # labels inside each pair. Equation 5 has eight off-diagonal errors:
    # Lcontext=8/16=1/2, Lcontrast=3/4+2/5=23/20, Lreg=(1/2-1/4)^2=1/16.
    # Their 0.4/0.6/0.1 mixture is 717/800. With alpha=10, the tangent
    # gradients are -5 (context), -1/2 (contrast), +1/8 (regularizer),
    # giving -2 - 3/10 + 1/80 = -183/80 along the other basis direction.
    values = torch.tensor(
        [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 1, 0, 1])
    criterion = ContextualMetricLoss(
        ContextualLossConfig(
            k=2,
            lam=0.4,
            gamma=0.1,
            target_mean_similarity=0.25,
            positive_margin=0.75,
            negative_margin=0.6,
        )
    )
    loss, components = criterion(values, labels)
    assert float(loss.detach()) == pytest.approx(717 / 800)
    assert float(components["context"]) == pytest.approx(0.5)
    assert float(components["contrast"]) == pytest.approx(23 / 20)
    assert float(components["regularizer"]) == pytest.approx(1 / 16)
    loss.backward()
    expected = torch.tensor(
        [[0, -183 / 80], [0, -183 / 80], [-183 / 80, 0], [-183 / 80, 0]],
        dtype=torch.float64,
    )
    torch.testing.assert_close(values.grad, expected, atol=1e-12, rtol=1e-12)


def test_reciprocal_denominator_gradient_has_hand_calculated_cancellation():
    # A=diag(J2,J2), W1=A, each reciprocal row denominator is 2.
    # dL/dW2=E=(A-Y)*offdiag/8. The numerator contributes E A^T/2:
    # +1/16 within a block, -1/16 across blocks. Differentiating the
    # denominator subtracts 1/16 everywhere, leaving 0 and -1/8.
    values = torch.tensor(
        [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 1, 0, 1])
    context, auxiliary = contextual_similarity(values, k=2, eps=0.05)
    reciprocal = auxiliary["reciprocal"]
    reciprocal.retain_grad()
    target = labels[:, None].eq(labels[None, :]).double()
    (
        (context - target).square() * (1 - torch.eye(4, dtype=torch.float64))
    ).mean().backward()
    expected = torch.tensor(
        [
            [0, 0, -1 / 8, -1 / 8],
            [0, 0, -1 / 8, -1 / 8],
            [-1 / 8, -1 / 8, 0, 0],
            [-1 / 8, -1 / 8, 0, 0],
        ],
        dtype=torch.float64,
    )
    torch.testing.assert_close(reciprocal.grad, expected, atol=1e-12, rtol=1e-12)


def test_tied_complete_neighborhood_uses_finite_empty_complement_convention():
    # Every neighborhood is full: its complement denominator clamps to one.
    # W1=W2=1/2, context loss=12*(1/2)^2/16=3/16;
    # contrast=2/5 and regularizer=9/16. Total is 297/800.
    values = torch.ones(4, 2, dtype=torch.float64, requires_grad=True)
    labels = torch.tensor([0, 0, 1, 1])
    criterion = ContextualMetricLoss(
        ContextualLossConfig(
            k=2,
            lam=0.4,
            gamma=0.1,
            target_mean_similarity=0.25,
            positive_margin=0.75,
            negative_margin=0.6,
        )
    )
    loss, _ = criterion(values, labels)
    assert float(loss.detach()) == pytest.approx(297 / 800)
    loss.backward()
    assert torch.isfinite(values.grad).all()
