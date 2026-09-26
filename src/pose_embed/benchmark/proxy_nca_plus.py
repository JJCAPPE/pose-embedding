"""Independent ProxyNCA++ equations and the declared motion recipe.

Teh et al. (2020), equations 4–6: https://arxiv.org/abs/2004.01113.
No upstream implementation is copied. Pooling and optimizer adaptation are
documented in docs/protocol/proxy-nca-plus-motion.md.
"""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field
from torch import nn

from pose_embed.benchmark.config import StrictModel


class ProxyNCAPlusParameters(StrictModel):
    recipe: Literal["teh2020_cub_motion_v1"] = "teh2020_cub_motion_v1"
    temperature: float = Field(default=1 / 9, gt=0)
    proxy_initial_std: float = Field(default=0.125, gt=0)
    head_learning_rate: float = Field(default=0.004, gt=0)
    proxy_learning_rate: float = Field(default=400.0, gt=0)
    optimizer_epsilon: float = Field(default=1.0, gt=0)
    warmup_epochs: Literal[5] = 5
    model_gradient_clip_value: float = Field(default=10.0, gt=0)
    pooling: Literal["confidence_valid_token_max"] = "confidence_valid_token_max"
    all_invalid_policy: Literal["zero_pooled_feature"] = "zero_pooled_feature"


class ProxyNCAPlusLoss(nn.Module):
    """All-proxy assignment probability on normalized squared distances."""

    def __init__(
        self,
        embedding_dimension: int,
        num_classes: int,
        temperature: float = 1 / 9,
        proxy_initial_std: float = 0.125,
    ) -> None:
        super().__init__()
        if embedding_dimension < 1 or num_classes < 2 or temperature <= 0:
            raise ValueError("invalid ProxyNCA++ dimensions or temperature")
        if proxy_initial_std <= 0:
            raise ValueError("proxy initialization scale must be positive")
        self.temperature = temperature
        self.proxies = nn.Parameter(
            torch.randn(num_classes, embedding_dimension) * proxy_initial_std
        )

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        samples = functional.normalize(embeddings, dim=-1)
        proxies = functional.normalize(self.proxies, dim=-1)
        squared_distances = (
            samples.square().sum(dim=-1, keepdim=True)
            + proxies.square().sum(dim=-1).unsqueeze(0)
            - 2 * samples @ proxies.T
        )
        return functional.cross_entropy(-squared_distances / self.temperature, labels)
