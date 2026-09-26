"""Independent HIST equations 2--8 (Lim et al., CVPR 2022).

No code from the unlicensed reference repository is incorporated. Numerical
conventions and motion adaptations are recorded in hist-motion-adaptation.md.
"""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field
from torch import nn

from pose_embed.benchmark.config import StrictModel


class HISTParameters(StrictModel):
    recipe: Literal["lim2022_cub_motion"] = "lim2022_cub_motion"
    embedding_dimension: int = Field(default=512, gt=1)
    hidden_dimension: int = Field(default=512, gt=1)
    temperature_scale: float = Field(default=32.0, gt=0)
    incidence_scale: float = Field(default=1.1, gt=0)
    graph_weight: float = Field(default=1.0, gt=0)
    head_learning_rate: float = Field(default=0.00012, gt=0)
    distribution_learning_rate: float = Field(default=0.1, gt=0)
    graph_learning_rate: float = Field(default=0.0006, gt=0)
    weight_decay: float = Field(default=0.00005, ge=0)
    warmup_epochs: int = Field(default=1, ge=0)
    decay_epochs: int = Field(default=5, gt=0)
    decay_factor: float = Field(default=0.5, gt=0, le=1)


class HISTHead(nn.Module):
    """Valid-token mean plus max, projection, then non-affine LayerNorm."""

    requires_valid_mask = True

    def __init__(self, embedding_dimension: int, representation_dimension: int):
        super().__init__()
        self.projection = nn.Linear(representation_dimension, embedding_dimension)
        nn.init.kaiming_normal_(self.projection.weight, mode="fan_out")
        nn.init.zeros_(self.projection.bias)
        self.normalization = nn.LayerNorm(embedding_dimension, elementwise_affine=False)

    def forward_raw(self, features, valid_mask):
        if (
            features.ndim != 5
            or features.shape[-1] != self.projection.in_features
            or valid_mask.shape != features.shape[:-1]
            or valid_mask.dtype != torch.bool
            or valid_mask.device != features.device
            or any(size == 0 for size in features.shape)
        ):
            raise ValueError("HIST head requires aligned tokens and boolean validity")
        count = valid_mask.sum((1, 2, 3)).unsqueeze(1)
        mean = features.masked_fill(~valid_mask.unsqueeze(-1), 0).sum((1, 2, 3))
        mean = mean / count.clamp_min(1)
        maximum = features.masked_fill(~valid_mask.unsqueeze(-1), -torch.inf).amax(
            (1, 2, 3)
        )
        maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
        return self.normalization(self.projection(mean + maximum))

    def forward(self, features, valid_mask):
        return functional.normalize(self.forward_raw(features, valid_mask), dim=-1)


def hypergraph_propagation(incidence: torch.Tensor) -> torch.Tensor:
    """Dv^-1/2 H De^-1 H^T Dv^-1/2; all hyperedges have unit weight."""
    if incidence.ndim != 2 or any(size == 0 for size in incidence.shape):
        raise ValueError("HIST incidence must be a nonempty matrix")
    if not torch.isfinite(incidence).all() or (incidence < 0).any():
        raise ValueError("HIST incidence must be finite and nonnegative")
    node_degree = incidence.sum(dim=1)
    edge_degree = incidence.sum(dim=0)
    if (node_degree <= 0).any() or (edge_degree <= 0).any():
        raise ValueError("HIST requires positive node and hyperedge degrees")
    normalized = incidence * node_degree.rsqrt().unsqueeze(1)
    return (normalized / edge_degree.unsqueeze(0)) @ normalized.T


class SemanticDistributions(nn.Module):
    """Class-conditioned diagonal Gaussians and soft semantic incidence."""

    def __init__(self, dimension: int, num_classes: int):
        super().__init__()
        self.means = nn.Parameter(torch.empty(num_classes, dimension))
        self.log_variances = nn.Parameter(torch.empty(num_classes, dimension))
        for parameter in self.parameters():
            nn.init.kaiming_normal_(parameter, mode="fan_out")

    def squared_distances(self, embeddings: torch.Tensor) -> torch.Tensor:
        unit = functional.normalize(embeddings, dim=-1)
        centers = functional.normalize(self.means, dim=-1)
        inverse_variances = (-functional.hardtanh(self.log_variances, 0, 6)).exp()
        displacement = unit.unsqueeze(1) - centers.unsqueeze(0)
        return (displacement.square() * inverse_variances.unsqueeze(0)).sum(-1)

    def forward(self, embeddings, labels, temperature_scale, incidence_scale):
        distances = self.squared_distances(embeddings)
        distribution_loss = functional.cross_entropy(
            -temperature_scale * distances, labels
        )
        present_classes = labels.unique(sorted=True)
        positive = labels.unsqueeze(1) == present_classes.unsqueeze(0)
        incidence = torch.where(
            positive,
            torch.ones_like(distances[:, present_classes]),
            (-incidence_scale * distances[:, present_classes]).exp(),
        )
        return distribution_loss, incidence


class HypergraphClassifier(nn.Module):
    def __init__(self, dimension: int, hidden_dimension: int, num_classes: int):
        super().__init__()
        self.hidden = nn.Linear(dimension, hidden_dimension)
        self.normalization = nn.BatchNorm1d(hidden_dimension)
        self.output = nn.Linear(hidden_dimension, num_classes)

    def forward(self, embeddings, propagation):
        hidden = self.normalization(propagation @ self.hidden(embeddings))
        return propagation @ self.output(functional.leaky_relu(hidden, 0.1))


class HypergraphSemanticTupletLoss(nn.Module):
    """Training-only distributions/graph; retrieval uses the independent head."""

    requires_raw_embeddings = True

    def __init__(self, parameters: HISTParameters, num_classes: int):
        super().__init__()
        self.config = parameters
        self.distributions = SemanticDistributions(
            parameters.embedding_dimension, num_classes
        )
        self.graph = HypergraphClassifier(
            parameters.embedding_dimension, parameters.hidden_dimension, num_classes
        )

    def loss_components(self, embeddings, labels):
        distribution, incidence = self.distributions(
            embeddings,
            labels,
            self.config.temperature_scale,
            self.config.incidence_scale,
        )
        propagation = hypergraph_propagation(incidence)
        graph = functional.cross_entropy(self.graph(embeddings, propagation), labels)
        return {"distribution": distribution, "graph": graph}

    def forward(self, embeddings, labels):
        components = self.loss_components(embeddings, labels)
        return (
            components["distribution"] + self.config.graph_weight * components["graph"]
        )
