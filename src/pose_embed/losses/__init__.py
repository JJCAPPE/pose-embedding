"""Metric-learning objectives used by the controlled comparison."""

from pose_embed.losses.contextual import ContextualLossConfig, ContextualMetricLoss
from pose_embed.losses.multi_similarity import MultiSimilarityWithMinerLoss
from pose_embed.losses.pairwise import (
    PairwiseContrastiveLoss,
    SupervisedContrastiveLoss,
)

__all__ = [
    "ContextualLossConfig",
    "ContextualMetricLoss",
    "MultiSimilarityWithMinerLoss",
    "PairwiseContrastiveLoss",
    "SupervisedContrastiveLoss",
]
