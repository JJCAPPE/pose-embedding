"""Shared MotionBERT initialization with explicit frozen and fine-tuning tracks."""

from __future__ import annotations

import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.models.action_head import ActionHeadEmbed


class MotionRetrievalModel(nn.Module):
    def __init__(
        self,
        encoder: nn.Module,
        *,
        embedding_dimension: int = 512,
        train_encoder: bool = True,
        representation_dimension: int = 512,
        joints: int = 17,
    ) -> None:
        super().__init__()
        self.encoder = encoder
        self.train_encoder = train_encoder
        self.encoder.requires_grad_(train_encoder)
        # get_representation bypasses the pretrained pose-regression output head.
        if hasattr(self.encoder, "head"):
            self.encoder.head.requires_grad_(False)
        self.head = ActionHeadEmbed(
            embedding_dimension=embedding_dimension,
            representation_dimension=representation_dimension,
            joints=joints,
        )
        self.train()

    def train(self, mode: bool = True) -> MotionRetrievalModel:
        super().train(mode)
        if not self.train_encoder:
            self.encoder.eval()
        return self

    def forward(self, poses: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.forward_raw(poses), dim=-1)

    def forward_raw(self, poses: torch.Tensor) -> torch.Tensor:
        """Compute one encoder pass and expose its unnormalized retrieval head."""
        if poses.ndim != 5 or any(size == 0 for size in poses.shape):
            raise ValueError(
                "poses must be nonempty [batch,people,frames,joints,channels]"
            )
        batch, people, frames, joints, channels = poses.shape
        flattened = poses.reshape(batch * people, frames, joints, channels)
        if self.train_encoder:
            represented = self.encoder.get_representation(flattened)
        else:
            with torch.no_grad():
                represented = self.encoder.get_representation(flattened)
        return self.head.forward_raw(
            represented.reshape(batch, people, frames, joints, -1)
        )
