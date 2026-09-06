"""Pinned-library Multi-Similarity loss used only by the gated stretch track."""

from __future__ import annotations

import importlib.metadata

import torch
from pytorch_metric_learning import distances, losses, miners
from torch import nn


class MultiSimilarityWithMinerLoss(nn.Module):
    """Compose the fully declared pinned-library loss and miner.

    This intentionally mirrors the behavioral combination observed in the
    contextual study. Every upstream parameter is passed explicitly; changing
    the package version or any value is a protocol amendment.
    """

    def __init__(
        self,
        *,
        library_version: str,
        loss_alpha: float,
        loss_beta: float,
        loss_base: float,
        miner_epsilon: float,
        distance_p: int,
        distance_power: int,
    ) -> None:
        super().__init__()
        installed = importlib.metadata.version("pytorch-metric-learning")
        if installed != library_version:
            raise RuntimeError(
                "pytorch-metric-learning version differs from the experiment "
                f"configuration: installed={installed}, required={library_version}"
            )
        distance = distances.CosineSimilarity(p=distance_p, power=distance_power)
        self.miner = miners.MultiSimilarityMiner(
            epsilon=miner_epsilon,
            distance=distance,
        )
        self.loss = losses.MultiSimilarityLoss(
            alpha=loss_alpha,
            beta=loss_beta,
            base=loss_base,
            distance=distance,
        )

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        if embeddings.ndim != 2 or labels.shape != (embeddings.shape[0],):
            raise ValueError("embeddings [N,D] and labels [N] must align")
        mined_pairs = self.miner(embeddings, labels)
        return self.loss(embeddings, labels, mined_pairs)
