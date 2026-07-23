"""Reference implementation of supervised contextual similarity optimization.

This module follows the equations in:
    Liao, Tsiligkaridis, and Kulis,
    "Supervised Metric Learning to Rank for Retrieval via Contextual
    Similarity Optimization" (ICML 2023).

It is intentionally written as a compact, auditable teaching implementation.
For an experiment, keep the balanced-batch invariant: every represented class
must contribute exactly ``k`` samples, and ``k`` must be even.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class GreaterThanSTE(torch.autograd.Function):
    """Exact ``x >= y`` in the forward pass; constant heuristic gradient.

    Forward:
        output = 1[x >= y]
    Backward:
        d output / d x = alpha
        d output / d y = -alpha

    This is the non-standard optimization step in the contextual-loss paper.
    """

    @staticmethod
    def forward(  # type: ignore[override]
        ctx: torch.autograd.function.FunctionCtx,
        x: torch.Tensor,
        y: torch.Tensor,
        alpha: float,
    ) -> torch.Tensor:
        ctx.alpha = float(alpha)
        return (x >= y).to(dtype=x.dtype)

    @staticmethod
    def backward(  # type: ignore[override]
        ctx: torch.autograd.function.FunctionCtx,
        grad_output: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, None]:
        alpha = ctx.alpha
        return grad_output * alpha, -grad_output * alpha, None


def validate_balanced_batch(labels: torch.Tensor, k: int) -> None:
    """Raise ``ValueError`` unless every represented class occurs exactly k times."""
    if labels.ndim != 1:
        raise ValueError(f"labels must have shape [batch], got {tuple(labels.shape)}")
    if k < 2 or k % 2 != 0:
        raise ValueError(f"k must be an even integer >= 2, got {k}")
    _, counts = torch.unique(labels, return_counts=True)
    if counts.numel() == 0 or not torch.all(counts == k):
        raise ValueError(
            "contextual loss requires exactly k samples per represented class; "
            f"observed counts={counts.tolist()}, k={k}"
        )


def contextual_similarity(
    embeddings: torch.Tensor,
    *,
    k: int,
    eps: float,
    alpha: float = 10.0,
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    """Compute the contextual-similarity matrix W.

    Args:
        embeddings: Tensor with shape [n, d]. It may be normalized or raw.
        k: Neighborhood size, equal to samples per class in a balanced batch.
        eps: Additive neighborhood margin from the paper.
        alpha: Constant backward derivative of the binary comparison.

    Returns:
        W: Symmetric contextual-similarity matrix with shape [n, n].
        aux: Intermediate matrices useful for debugging and visualization.
    """
    if embeddings.ndim != 2:
        raise ValueError(
            f"embeddings must have shape [batch, dim], got {tuple(embeddings.shape)}"
        )
    n = int(embeddings.shape[0])
    if k < 2 or k > n:
        raise ValueError(f"k must be in [2, {n}], got {k}")
    if k % 2 != 0:
        raise ValueError("k must be even for the reciprocal k/2 step")
    if eps < 0:
        raise ValueError(f"eps must be nonnegative, got {eps}")
    if alpha <= 0:
        raise ValueError(f"alpha must be positive, got {alpha}")

    # Unit-sphere geometry: cosine similarity and squared Euclidean distance.
    z = F.normalize(embeddings, p=2, dim=1)
    similarity = z @ z.T
    distance = (2.0 - 2.0 * similarity).clamp_min(0.0)

    # Step 1: expanded top-k neighborhood N_{k+eps}.
    # -distance is largest for the closest points. The k-th returned value is
    # therefore the negative distance to the k-th closest point, including self.
    negative_topk = (-distance).topk(k, dim=1, largest=True, sorted=True).values
    negative_dk = negative_topk[:, -1:]
    neighborhood = GreaterThanSTE.apply(
        -distance + eps, negative_dk.detach(), alpha
    )

    # Step 2: shared-neighbor and shared-non-neighbor agreements.
    neighbor_count = (
        neighborhood.sum(dim=1, keepdim=True).detach().clamp_min(1.0)
    )
    shared_neighbors = (neighborhood @ neighborhood.T) / neighbor_count

    non_neighborhood = 1.0 - neighborhood
    non_neighbor_count = (
        non_neighborhood.sum(dim=1, keepdim=True).detach().clamp_min(1.0)
    )
    shared_non_neighbors = (
        non_neighborhood @ non_neighborhood.T
    ) / non_neighbor_count

    w1 = 0.5 * (shared_neighbors + shared_non_neighbors) * neighborhood

    # Step 3: reciprocal k/2 graph, query expansion, and symmetrization.
    k_half = k // 2
    negative_dk_half = negative_topk[:, k_half - 1 : k_half]
    neighborhood_half = GreaterThanSTE.apply(
        -distance + eps, negative_dk_half.detach(), alpha
    )
    reciprocal = neighborhood_half * neighborhood_half.T
    reciprocal_count = reciprocal.sum(dim=1, keepdim=True).clamp_min(1.0)
    w2 = (reciprocal @ w1) / reciprocal_count
    contextual = 0.5 * (w2 + w2.T)

    aux = {
        "z": z,
        "similarity": similarity,
        "distance": distance,
        "neighborhood": neighborhood,
        "shared_neighbors": shared_neighbors,
        "shared_non_neighbors": shared_non_neighbors,
        "w1": w1,
        "reciprocal": reciprocal,
        "w2": w2,
    }
    return contextual, aux


@dataclass(frozen=True)
class ContextualLossConfig:
    """Hyperparameters for the paper's three-term objective."""

    k: int
    eps: float = 0.05
    alpha: float = 10.0
    lam: float = 0.2
    gamma: float = 0.1
    target_mean_similarity: float = 0.0
    positive_margin: float = 0.9
    negative_margin: float = 0.6
    enforce_balanced_batch: bool = True

    def __post_init__(self) -> None:
        if self.k < 2 or self.k % 2 != 0:
            raise ValueError(f"k must be an even integer >= 2, got {self.k}")
        if self.eps < 0:
            raise ValueError("eps must be nonnegative")
        if self.alpha <= 0:
            raise ValueError("alpha must be positive")
        if not 0.0 <= self.lam <= 1.0:
            raise ValueError("lam must lie in [0, 1]")
        if self.gamma < 0:
            raise ValueError("gamma must be nonnegative")
        if self.positive_margin < self.negative_margin:
            raise ValueError(
                "positive_margin should be >= negative_margin to create a margin gap"
            )


class ContextualMetricLoss(nn.Module):
    """Contextual + contrastive + mean-similarity regularization objective."""

    def __init__(self, cfg: ContextualLossConfig):
        super().__init__()
        self.cfg = cfg

    @staticmethod
    def _mean_active(values: torch.Tensor) -> torch.Tensor:
        active = values > 0
        if not torch.any(active):
            return values.new_zeros(())
        return values[active].mean()

    def forward(
        self, embeddings: torch.Tensor, labels: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        if labels.shape != (embeddings.shape[0],):
            raise ValueError(
                "labels must have shape [batch] matching embeddings; "
                f"got labels={tuple(labels.shape)}, embeddings={tuple(embeddings.shape)}"
            )
        if self.cfg.enforce_balanced_batch:
            validate_balanced_batch(labels, self.cfg.k)

        contextual, aux = contextual_similarity(
            embeddings,
            k=self.cfg.k,
            eps=self.cfg.eps,
            alpha=self.cfg.alpha,
        )
        similarity = aux["similarity"]
        target = labels[:, None].eq(labels[None, :]).to(similarity.dtype)
        off_diagonal = 1.0 - torch.eye(
            similarity.shape[0], device=similarity.device, dtype=similarity.dtype
        )

        # Eq. (5): contextual similarity is optimized against label agreement.
        loss_context = (((contextual - target) ** 2) * off_diagonal).mean()

        positive_hinge = (
            F.relu(self.cfg.positive_margin - similarity)
            * target
            * off_diagonal
        )
        negative_hinge = (
            F.relu(similarity - self.cfg.negative_margin) * (1.0 - target)
        )
        loss_contrast = self._mean_active(positive_hinge) + self._mean_active(
            negative_hinge
        )

        loss_regularizer = (
            similarity.mean() - self.cfg.target_mean_similarity
        ).square()
        total = (
            self.cfg.lam * loss_context
            + (1.0 - self.cfg.lam) * loss_contrast
            + self.cfg.gamma * loss_regularizer
        )

        stats = {
            "loss": total.detach(),
            "context": loss_context.detach(),
            "contrast": loss_contrast.detach(),
            "regularizer": loss_regularizer.detach(),
            "mean_similarity": similarity.mean().detach(),
        }
        return total, stats


def _smoke_test() -> None:
    """Run a deterministic shape/range/gradient check."""
    torch.manual_seed(7)
    classes, k, dim = 4, 4, 12
    labels = torch.arange(classes).repeat_interleave(k)

    # Create visibly clustered examples, but keep trainable noise so gradients flow.
    centers = F.normalize(torch.randn(classes, dim), dim=1)
    noise = 0.15 * torch.randn(classes * k, dim)
    embeddings = (centers.repeat_interleave(k, dim=0) + noise).requires_grad_(True)

    criterion = ContextualMetricLoss(ContextualLossConfig(k=k))
    loss, stats = criterion(embeddings, labels)
    loss.backward()

    contextual, _ = contextual_similarity(embeddings.detach(), k=k, eps=0.05)
    assert contextual.shape == (classes * k, classes * k)
    assert torch.allclose(contextual, contextual.T, atol=1e-6)
    assert torch.isfinite(contextual).all()
    assert contextual.min() >= -1e-6 and contextual.max() <= 1.0 + 1e-6
    assert embeddings.grad is not None and torch.isfinite(embeddings.grad).all()

    printable = {name: float(value) for name, value in stats.items()}
    print("Smoke test passed.")
    print(printable)


if __name__ == "__main__":
    _smoke_test()
