"""Auditable contextual-similarity objective for the locked comparison.

This is the package form of the repository's reviewed teaching implementation
in ``contextual-similarity-study-pack/contextual_loss_reference.py``. It follows
the equations in Liao, Tsiligkaridis, and Kulis (ICML 2023); it is not copied
from the authors' unlicensed source repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
import torch.nn.functional as functional
from torch import nn


class GreaterThanSTE(torch.autograd.Function):
    """Exact greater-than comparison with the paper's heuristic gradient."""

    @staticmethod
    def forward(
        ctx: Any,
        x: torch.Tensor,
        y: torch.Tensor,
        alpha: float,
    ) -> torch.Tensor:
        ctx.alpha = float(alpha)
        return (x >= y).to(dtype=x.dtype)

    @staticmethod
    def backward(
        ctx: Any,
        grad_output: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, None]:
        alpha = ctx.alpha
        return grad_output * alpha, -grad_output * alpha, None


def validate_balanced_batch(labels: torch.Tensor, k: int) -> None:
    """Raise unless every represented class contributes exactly ``k`` rows."""
    if labels.ndim != 1:
        raise ValueError(f"labels must have shape [batch], got {tuple(labels.shape)}")
    if k < 2 or k % 2:
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
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    """Compute the paper's symmetric contextual-similarity matrix."""
    if embeddings.ndim != 2:
        raise ValueError(
            f"embeddings must have shape [batch, dim], got {tuple(embeddings.shape)}"
        )
    count = int(embeddings.shape[0])
    if k < 2 or k > count:
        raise ValueError(f"k must be in [2, {count}], got {k}")
    if k % 2:
        raise ValueError("k must be even for the reciprocal k/2 step")
    if eps < 0:
        raise ValueError(f"eps must be nonnegative, got {eps}")
    if alpha <= 0:
        raise ValueError(f"alpha must be positive, got {alpha}")

    normalized = functional.normalize(embeddings, p=2, dim=1)
    similarity = normalized @ normalized.T
    distance = (2.0 - 2.0 * similarity).clamp_min(0.0)

    negative_topk = (-distance).topk(k, dim=1, largest=True, sorted=True).values
    negative_dk = negative_topk[:, -1:]
    neighborhood = GreaterThanSTE.apply(-distance + eps, negative_dk.detach(), alpha)

    neighbor_count = neighborhood.sum(dim=1, keepdim=True).detach().clamp_min(1.0)
    shared_neighbors = (neighborhood @ neighborhood.T) / neighbor_count

    non_neighborhood = 1.0 - neighborhood
    non_neighbor_count = (
        non_neighborhood.sum(dim=1, keepdim=True).detach().clamp_min(1.0)
    )
    shared_non_neighbors = (non_neighborhood @ non_neighborhood.T) / non_neighbor_count
    w1 = 0.5 * (shared_neighbors + shared_non_neighbors) * neighborhood

    k_half = k // 2
    negative_dk_half = negative_topk[:, k_half - 1 : k_half]
    neighborhood_half = GreaterThanSTE.apply(
        -distance + eps, negative_dk_half.detach(), alpha
    )
    reciprocal = neighborhood_half * neighborhood_half.T
    reciprocal_count = reciprocal.sum(dim=1, keepdim=True).clamp_min(1.0)
    w2 = (reciprocal @ w1) / reciprocal_count
    contextual = 0.5 * (w2 + w2.T)

    return contextual, {
        "z": normalized,
        "similarity": similarity,
        "distance": distance,
        "neighborhood": neighborhood,
        "shared_neighbors": shared_neighbors,
        "shared_non_neighbors": shared_non_neighbors,
        "w1": w1,
        "reciprocal": reciprocal,
        "w2": w2,
    }


@dataclass(frozen=True)
class ContextualLossConfig:
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
        if self.k < 2 or self.k % 2:
            raise ValueError(f"k must be an even integer >= 2, got {self.k}")
        if self.eps < 0:
            raise ValueError("eps must be nonnegative")
        if self.alpha <= 0:
            raise ValueError("alpha must be positive")
        if not 0 <= self.lam <= 1:
            raise ValueError("lam must lie in [0, 1]")
        if self.gamma < 0:
            raise ValueError("gamma must be nonnegative")
        if self.positive_margin < self.negative_margin:
            raise ValueError("positive_margin must be >= negative_margin")


class ContextualMetricLoss(nn.Module):
    """Contextual + contrastive + mean-similarity regularization objective."""

    def __init__(self, config: ContextualLossConfig):
        super().__init__()
        self.config = config

    @staticmethod
    def _mean_active(values: torch.Tensor) -> torch.Tensor:
        active = values > 0
        if not torch.any(active):
            return values.new_zeros(())
        return values[active].mean()

    def forward(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        if labels.shape != (embeddings.shape[0],):
            raise ValueError("labels must have shape [batch] matching embeddings")
        if self.config.enforce_balanced_batch:
            validate_balanced_batch(labels, self.config.k)
        contextual, auxiliary = contextual_similarity(
            embeddings,
            k=self.config.k,
            eps=self.config.eps,
            alpha=self.config.alpha,
        )
        similarity = auxiliary["similarity"]
        target = labels[:, None].eq(labels[None, :]).to(similarity.dtype)
        off_diagonal = 1.0 - torch.eye(
            similarity.shape[0], device=similarity.device, dtype=similarity.dtype
        )
        context_loss = (((contextual - target) ** 2) * off_diagonal).mean()
        positive_hinge = (
            functional.relu(self.config.positive_margin - similarity)
            * target
            * off_diagonal
        )
        negative_hinge = functional.relu(similarity - self.config.negative_margin) * (
            1.0 - target
        )
        contrast_loss = self._mean_active(positive_hinge) + self._mean_active(
            negative_hinge
        )
        regularizer_loss = (
            similarity.mean() - self.config.target_mean_similarity
        ).square()
        total = (
            self.config.lam * context_loss
            + (1.0 - self.config.lam) * contrast_loss
            + self.config.gamma * regularizer_loss
        )
        return total, {
            "loss": total.detach(),
            "context": context_loss.detach(),
            "contrast": contrast_loss.detach(),
            "regularizer": regularizer_loss.detach(),
            "mean_similarity": similarity.mean().detach(),
        }
