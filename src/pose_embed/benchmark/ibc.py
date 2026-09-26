"""IBC training graph and auxiliary classification for motion embeddings.

Independent dense implementation of Seidenschwarz et al. (ICML 2021),
equations 2--6, with the audited CUB recipe from the pinned official source.
The graph includes self-edges and the source's zero-logit null message.
See docs/protocol/ibc-motion-adaptation.md for source and motion distinctions.
"""

from __future__ import annotations

import math
from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field, model_validator
from torch import nn

from pose_embed.benchmark.config import StrictModel


class IBCParameters(StrictModel):
    recipe: Literal["seidenschwarz2021_cub_motion"] = "seidenschwarz2021_cub_motion"
    embedding_dimension: int = Field(default=512, gt=1)
    attention_heads: int = Field(default=2, gt=0)
    message_steps: int = Field(default=1, gt=0)
    dropout: float = Field(default=0.1, ge=0, lt=1)
    temperature: float = Field(default=0.2, gt=0)
    label_smoothing: float = Field(default=0.1, ge=0, le=1)
    auxiliary_weight: float = Field(default=1.0, gt=0)
    refined_weight: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def attention_dimension_divides(self) -> IBCParameters:
        if self.embedding_dimension % self.attention_heads:
            raise ValueError("IBC embedding dimension must divide into attention heads")
        return self


class IntraBatchAttention(nn.Module):
    """Dense complete graph, incoming attention, and concatenated head messages."""

    def __init__(self, dimension: int, heads: int, dropout: float):
        super().__init__()
        self.heads = heads
        self.head_dimension = dimension // heads
        self.query = nn.Linear(dimension, dimension)
        self.key = nn.Linear(dimension, dimension)
        self.value = nn.Linear(dimension, dimension)
        self.output = nn.Linear(dimension, dimension)
        self.dropout = nn.Dropout(dropout)
        for layer in (self.query, self.key, self.value, self.output):
            nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)

    def _heads(self, values: torch.Tensor) -> torch.Tensor:
        return values.reshape(-1, self.heads, self.head_dimension).transpose(0, 1)

    def attention_weights(self, embeddings: torch.Tensor) -> torch.Tensor:
        query = self._heads(self.query(embeddings))
        key = self._heads(self.key(embeddings))
        scores = query @ key.transpose(-1, -2) / math.sqrt(self.head_dimension)
        # The reference scatter softmax has a +1 denominator. Appending a
        # zero-logit, zero-value message is its numerically stable dense form.
        return functional.softmax(functional.pad(scores, (0, 1)), dim=-1)[..., :-1]

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        weights = self.dropout(self.attention_weights(embeddings))
        messages = weights @ self._heads(self.value(embeddings))
        concatenated = messages.transpose(0, 1).reshape(len(embeddings), -1)
        return self.output(concatenated)


class IBCMessageLayer(nn.Module):
    def __init__(self, parameters: IBCParameters):
        super().__init__()
        dimension = parameters.embedding_dimension
        self.attention = IntraBatchAttention(
            dimension, parameters.attention_heads, parameters.dropout
        )
        self.attention_residual_dropout = nn.Dropout(parameters.dropout)
        self.attention_norm = nn.LayerNorm(dimension, eps=1e-5)
        self.feedforward = nn.Sequential(
            nn.Linear(dimension, 4 * dimension),
            nn.ReLU(),
            nn.Dropout(parameters.dropout),
            nn.Linear(4 * dimension, dimension),
        )
        self.feedforward_residual_dropout = nn.Dropout(parameters.dropout)
        self.feedforward_norm = nn.LayerNorm(dimension, eps=1e-5)

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        attended = self.attention_norm(
            embeddings + self.attention_residual_dropout(self.attention(embeddings))
        )
        return self.feedforward_norm(
            attended + self.feedforward_residual_dropout(self.feedforward(attended))
        )


class IntraBatchConnectionsLoss(nn.Module):
    """Training-only MPN and two globally indexed classification objectives."""

    requires_raw_embeddings = True

    def __init__(self, parameters: IBCParameters, num_classes: int):
        super().__init__()
        self.config = parameters
        dimension = parameters.embedding_dimension
        self.input_projection = nn.Linear(dimension, dimension)
        self.message_layers = nn.Sequential(
            *(IBCMessageLayer(parameters) for _ in range(parameters.message_steps))
        )
        self.refined_neck = nn.BatchNorm1d(dimension)
        self.refined_neck.bias.requires_grad_(False)
        self.refined_classifier = nn.Linear(dimension, num_classes, bias=False)
        nn.init.normal_(self.refined_classifier.weight, std=0.001)
        self.auxiliary_classifier = nn.Linear(dimension, num_classes)

    def refine(self, embeddings: torch.Tensor) -> torch.Tensor:
        unit_embeddings = functional.normalize(embeddings, dim=-1)
        return self.message_layers(self.input_projection(unit_embeddings))

    def loss_components(
        self, embeddings: torch.Tensor, labels: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        refined = self.refined_classifier(self.refined_neck(self.refine(embeddings)))
        auxiliary = self.auxiliary_classifier(embeddings)
        return {
            name: functional.cross_entropy(
                logits / self.config.temperature,
                labels,
                label_smoothing=self.config.label_smoothing,
            )
            for name, logits in (("refined", refined), ("auxiliary", auxiliary))
        }

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        losses = self.loss_components(embeddings, labels)
        return (
            self.config.refined_weight * losses["refined"]
            + self.config.auxiliary_weight * losses["auxiliary"]
        )
