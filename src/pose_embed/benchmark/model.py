"""Shared MotionBERT initialization with explicit frozen and fine-tuning tracks."""

from __future__ import annotations

import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.benchmark.drml import DRMLHead
from pose_embed.benchmark.hist import HISTHead
from pose_embed.benchmark.metrix import METRIX_METHODS, MetrixMeanMaxHead
from pose_embed.models.action_head import ActionHeadEmbed


def head_recipe(method_id: str) -> str:
    if method_id in {"multi_similarity_metrix", "proxy_anchor_metrix"}:
        return "confidence_valid_token_mean_plus_max"
    if method_id == "hist":
        return "confidence_valid_token_mean_plus_max_project_nonaffine_ln"
    if method_id == "drml":
        return "drml_four_branch_directed_relations_mean_tokens"
    return (
        "confidence_valid_token_max_nonaffine_ln"
        if method_id in {"proxy_nca_pp", "proxy_nca_metrix"}
        else "motionbert_action_head"
    )


def supports_embedding_inference(method_id: str) -> bool:
    from pose_embed.benchmark.config import load_methods
    from pose_embed.benchmark.losses import supports

    specification = load_methods().get(method_id)
    return bool(
        specification
        and supports(method_id)
        and (
            specification.family == "embedding_loss"
            or method_id in {"proxy_nca_pp", "ibc", "hist", "drml", "s2sd"}
            or method_id in METRIX_METHODS
        )
    )


class MaskedMaxHead(nn.Module):
    """Max over valid person/time/joint tokens, LayerNorm, linear, unit length."""

    requires_valid_mask = True

    def __init__(self, embedding_dimension: int, representation_dimension: int):
        super().__init__()
        self.representation_dimension = representation_dimension
        self.normalization = nn.LayerNorm(
            representation_dimension, elementwise_affine=False
        )
        self.projection = nn.Linear(representation_dimension, embedding_dimension)

    def forward(self, features: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.forward_raw(features, valid_mask), dim=-1)

    def forward_raw(
        self, features: torch.Tensor, valid_mask: torch.Tensor
    ) -> torch.Tensor:
        if (
            features.ndim != 5
            or any(size == 0 for size in features.shape)
            or features.shape[-1] != self.representation_dimension
            or valid_mask.shape != features.shape[:-1]
            or valid_mask.dtype != torch.bool
            or valid_mask.device != features.device
        ):
            raise ValueError(
                "max pooling requires aligned feature tokens and bool mask"
            )
        masked = features.masked_fill(~valid_mask.unsqueeze(-1), -torch.inf)
        pooled = masked.amax(dim=(1, 2, 3))
        has_valid = valid_mask.any(dim=(1, 2, 3)).unsqueeze(-1)
        pooled = torch.where(has_valid, pooled, torch.zeros_like(pooled))
        return self.projection(self.normalization(pooled))


class MotionRetrievalModel(nn.Module):
    def __init__(
        self,
        encoder: nn.Module,
        *,
        embedding_dimension: int = 512,
        train_encoder: bool = True,
        representation_dimension: int = 512,
        joints: int = 17,
        method_id: str = "contrastive",
    ) -> None:
        super().__init__()
        self.encoder = encoder
        self.method_id = method_id
        self.head = (
            DRMLHead(representation_dimension, embedding_dimension // 4)
            if method_id == "drml"
            else MaskedMaxHead(embedding_dimension, representation_dimension)
            if method_id in {"proxy_nca_pp", "proxy_nca_metrix"}
            else ActionHeadEmbed(
                embedding_dimension=embedding_dimension,
                representation_dimension=representation_dimension,
                joints=joints,
            )
        )
        if method_id in {"multi_similarity_metrix", "proxy_anchor_metrix"}:
            self.head = MetrixMeanMaxHead(embedding_dimension, representation_dimension)
        if method_id == "hist":
            self.head = HISTHead(embedding_dimension, representation_dimension)
        if method_id == "drml" and embedding_dimension % 4:
            raise ValueError("DRML embedding dimension must be divisible by four")
        self.set_encoder_trainable(train_encoder)

    def set_encoder_trainable(self, enabled: bool) -> None:
        self.train_encoder = enabled
        self.encoder.requires_grad_(enabled)
        # get_representation bypasses the pretrained pose-regression output head.
        if hasattr(self.encoder, "head"):
            self.encoder.head.requires_grad_(False)
        self.train(self.training)

    def train(self, mode: bool = True) -> MotionRetrievalModel:
        super().train(mode)
        if not self.train_encoder:
            self.encoder.eval()
        return self

    def forward(self, poses: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.forward_raw(poses), dim=-1)

    def forward_raw(self, poses: torch.Tensor) -> torch.Tensor:
        represented = self.forward_features(poses)
        if getattr(self.head, "requires_valid_mask", False):
            if poses.shape[-1] != 3:
                raise ValueError("confidence masking requires x, y, confidence inputs")
            return self.head.forward_raw(represented, poses[..., 2] > 0)
        return self.head.forward_raw(represented)

    def project_features(
        self, features: torch.Tensor, valid_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        """Apply the declared retrieval head to an already computed token grid."""
        if getattr(self.head, "requires_valid_mask", False):
            if valid_mask is None:
                raise ValueError("this retrieval head requires a valid token mask")
            return self.head(features, valid_mask)
        return self.head(features)

    def forward_features(self, poses: torch.Tensor) -> torch.Tensor:
        """Expose the same encoder token grid without an additional encoder pass."""
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
        return represented.reshape(batch, people, frames, joints, -1)
