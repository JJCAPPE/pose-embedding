"""MotionBERT-compatible action embedding head and frozen encoder adapter."""

from __future__ import annotations

from typing import Protocol

import torch
import torch.nn.functional as functional
from torch import nn


class RepresentationEncoder(Protocol):
    """Minimal interface needed from a MotionBERT-style encoder."""

    def get_representation(self, poses: torch.Tensor) -> torch.Tensor: ...


class ActionHeadEmbed(nn.Module):
    """Pool `[N,M,T,J,C]` features and return normalized action embeddings.

    The operation order intentionally matches MotionBERT's ActionHeadEmbed:
    temporal mean, flattened joint features, person mean, linear projection,
    and L2 normalization.
    """

    def __init__(
        self,
        *,
        dropout_ratio: float = 0.0,
        representation_dimension: int = 512,
        joints: int = 17,
        embedding_dimension: int = 2048,
    ) -> None:
        super().__init__()
        self.representation_dimension = representation_dimension
        self.joints = joints
        self.dropout = nn.Dropout(p=dropout_ratio)
        self.projection = nn.Linear(
            representation_dimension * joints,
            embedding_dimension,
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if features.ndim != 5:
            raise ValueError(
                "features must have shape [batch, people, frames, joints, channels]"
            )
        batch, people, _, joints, channels = features.shape
        if joints != self.joints or channels != self.representation_dimension:
            raise ValueError(
                f"expected J={self.joints}, C={self.representation_dimension}; "
                f"got J={joints}, C={channels}"
            )
        pooled = self.dropout(features).permute(0, 1, 3, 4, 2).mean(dim=-1)
        pooled = pooled.reshape(batch, people, -1).mean(dim=1)
        return functional.normalize(self.projection(pooled), dim=-1)


class FrozenEncoderAdapter(nn.Module):
    """Freeze a MotionBERT-style encoder and pair it with a trainable head."""

    def __init__(self, encoder: nn.Module, head: ActionHeadEmbed) -> None:
        super().__init__()
        if not hasattr(encoder, "get_representation"):
            raise TypeError("encoder must implement get_representation")
        self.encoder = encoder
        self.head = head
        self.encoder.requires_grad_(False)
        self.encoder.eval()

    def train(self, mode: bool = True) -> FrozenEncoderAdapter:
        super().train(mode)
        self.encoder.eval()
        return self

    def forward(self, poses: torch.Tensor) -> torch.Tensor:
        if poses.ndim != 5:
            raise ValueError(
                "poses must have shape [batch, people, frames, joints, channels]"
            )
        batch, people, frames, joints, channels = poses.shape
        flattened = poses.reshape(batch * people, frames, joints, channels)
        with torch.no_grad():
            represented = self.encoder.get_representation(flattened)  # type: ignore[attr-defined]
        represented = represented.reshape(batch, people, frames, joints, -1)
        return self.head(represented)
