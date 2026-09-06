"""Controlled contrastive and supervised-contrastive objectives."""

from __future__ import annotations

import torch
import torch.nn.functional as functional
from torch import nn


def _validate_embeddings_and_labels(
    embeddings: torch.Tensor,
    labels: torch.Tensor,
) -> None:
    if embeddings.ndim != 2:
        raise ValueError("embeddings must have shape [batch, dimension]")
    if labels.shape != (embeddings.shape[0],):
        raise ValueError("labels must have shape [batch] matching embeddings")
    if embeddings.shape[0] < 2:
        raise ValueError("at least two embeddings are required")


class PairwiseContrastiveLoss(nn.Module):
    """The hinge-based contrastive component used by the contextual objective."""

    def __init__(self, *, positive_margin: float = 0.9, negative_margin: float = 0.6):
        super().__init__()
        if positive_margin < negative_margin:
            raise ValueError("positive_margin must be >= negative_margin")
        self.positive_margin = positive_margin
        self.negative_margin = negative_margin

    @staticmethod
    def _mean_active(values: torch.Tensor) -> torch.Tensor:
        active = values > 0
        return values[active].mean() if torch.any(active) else values.sum() * 0.0

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        _validate_embeddings_and_labels(embeddings, labels)
        normalized = functional.normalize(embeddings, dim=1)
        similarity = normalized @ normalized.T
        same = labels[:, None].eq(labels[None, :])
        off_diagonal = ~torch.eye(len(labels), device=labels.device, dtype=torch.bool)
        positive = functional.relu(self.positive_margin - similarity)[
            same & off_diagonal
        ]
        negative = functional.relu(similarity - self.negative_margin)[~same]
        return self._mean_active(positive) + self._mean_active(negative)


class SupervisedContrastiveLoss(nn.Module):
    """Single-view supervised contrastive loss with self-comparisons excluded."""

    def __init__(self, *, temperature: float = 0.07):
        super().__init__()
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.temperature = temperature

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        _validate_embeddings_and_labels(embeddings, labels)
        normalized = functional.normalize(embeddings, dim=1)
        logits = (normalized @ normalized.T) / self.temperature
        logits = logits - logits.max(dim=1, keepdim=True).values.detach()
        self_mask = torch.eye(len(labels), dtype=torch.bool, device=labels.device)
        positives = labels[:, None].eq(labels[None, :]) & ~self_mask
        positive_count = positives.sum(dim=1)
        if torch.any(positive_count == 0):
            raise ValueError("every sample needs another same-class positive")
        exp_logits = torch.exp(logits) * (~self_mask)
        log_probability = logits - torch.log(exp_logits.sum(dim=1, keepdim=True))
        mean_positive_log_probability = (log_probability * positives).sum(
            dim=1
        ) / positive_count
        return -mean_positive_log_probability.mean()
