"""Declared v2 losses; unavailable full methods never receive substitutes.

SmoothAP and ROADMAP below are independent implementations of their published
ranking equations. No code from the unlicensed contextual repository is used.
"""

from __future__ import annotations

import importlib.metadata
from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field, model_validator
from pytorch_metric_learning import distances, losses, miners
from torch import nn

from pose_embed.benchmark.config import StrictModel, load_methods
from pose_embed.benchmark.diml import DIMLParameters
from pose_embed.benchmark.drml import DRMLLoss, DRMLParameters
from pose_embed.benchmark.hist import HISTParameters, HypergraphSemanticTupletLoss
from pose_embed.benchmark.ibc import IBCParameters, IntraBatchConnectionsLoss
from pose_embed.benchmark.metrix import METRIX_METHODS, MetrixLoss
from pose_embed.benchmark.mhgl import MHGLLoss
from pose_embed.benchmark.proxy_nca_plus import (
    ProxyNCAPlusLoss,
    ProxyNCAPlusParameters,
)
from pose_embed.benchmark.s2sd import S2SDLoss, S2SDParameters
from pose_embed.losses.contextual import ContextualLossConfig, ContextualMetricLoss
from pose_embed.losses.pairwise import (
    PairwiseContrastiveLoss,
    SupervisedContrastiveLoss,
)

PML_VERSION = "2.9.0"
SUPPORTED_METHODS = METRIX_METHODS | frozenset(
    {
        "contrastive",
        "contextual",
        "contextual_1536",
        "triplet",
        "multi_similarity",
        "multi_similarity_miner",
        "proxy_anchor",
        "proxy_nca",
        "proxy_nca_pp",
        "roadmap",
        "nt_xent",
        "fast_ap",
        "smooth_ap",
        "normalized_softmax",
        "supcon",
        "drml",
        "s2sd",
        "mhgl",
        "ibc",
        "hist",
        "diml",
    }
)


class ContrastiveParameters(StrictModel):
    positive_margin: float = Field(default=0.75, ge=-1, le=1)
    negative_margin: float = Field(default=0.6, ge=-1, le=1)

    @model_validator(mode="after")
    def margins_are_ordered(self) -> ContrastiveParameters:
        if self.positive_margin < self.negative_margin:
            raise ValueError("positive_margin must be >= negative_margin")
        return self


class ContextualParameters(ContrastiveParameters):
    recipe: Literal["liao2023_main"] = "liao2023_main"
    k: int = Field(default=4, ge=4)
    eps: float = Field(default=0.05, ge=0)
    alpha: float = Field(default=10.0, gt=0)
    lam: float = Field(default=0.8, ge=0, le=1)
    gamma: float = Field(default=0.1, ge=0)
    target_mean_similarity: float = Field(default=0.3, ge=-1, le=1)

    @model_validator(mode="after")
    def neighborhood_is_even(self) -> ContextualParameters:
        if self.k % 2:
            raise ValueError("contextual k must be even")
        return self


class TripletParameters(StrictModel):
    margin: float = Field(default=0.05, gt=0)


class MultiSimilarityParameters(StrictModel):
    alpha: float = Field(default=2.0, gt=0)
    beta: float = Field(default=50.0, gt=0)
    base: float = Field(default=0.5, ge=-1, le=1)


class MinedMultiSimilarityParameters(MultiSimilarityParameters):
    miner_epsilon: float = Field(default=0.1, ge=0)


class TemperatureParameters(StrictModel):
    temperature: float = Field(gt=0)


class FastAPParameters(StrictModel):
    num_bins: int = Field(default=10, gt=1)


class ProxyAnchorParameters(StrictModel):
    embedding_dimension: int = Field(default=512, gt=0)
    margin: float = Field(default=0.1, ge=0)
    alpha: float = Field(default=32.0, gt=0)


class ProxyNCAParameters(StrictModel):
    embedding_dimension: int = Field(default=512, gt=0)
    softmax_scale: float = Field(default=1.0, gt=0)


class SoftmaxParameters(TemperatureParameters):
    embedding_dimension: int = Field(default=512, gt=0)


class RoadmapParameters(ContrastiveParameters):
    positive_margin: float = Field(default=0.9, ge=-1, le=1)
    temperature: float = Field(default=0.01, gt=0)
    rho: float = Field(default=100.0, gt=0)
    delta: float = Field(default=0.05, ge=0)
    calibration_weight: float = Field(default=0.5, ge=0, le=1)


class _ScalarContextual(nn.Module):
    def __init__(self, parameters: ContextualParameters):
        super().__init__()
        self.loss = ContextualMetricLoss(
            ContextualLossConfig(**parameters.model_dump(exclude={"recipe"}))
        )

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return self.loss(embeddings, labels)[0]


class _MinedLoss(nn.Module):
    def __init__(self, parameters: MinedMultiSimilarityParameters):
        super().__init__()
        self.miner = miners.MultiSimilarityMiner(
            epsilon=parameters.miner_epsilon, distance=distances.CosineSimilarity()
        )
        self.loss = losses.MultiSimilarityLoss(
            alpha=parameters.alpha,
            beta=parameters.beta,
            base=parameters.base,
            distance=distances.CosineSimilarity(),
        )

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return self.loss(embeddings, labels, self.miner(embeddings, labels))


class SmoothAPLoss(nn.Module):
    """Brown et al. (2020), sigmoid AP ranks with query and item self excluded.

    Label masks make the loss independent of batch order and of P versus K.
    https://arxiv.org/abs/2007.12163
    """

    def __init__(self, temperature: float):
        super().__init__()
        self.temperature = temperature

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        normalized = functional.normalize(embeddings, dim=1)
        similarity = normalized @ normalized.T
        terms = []
        for anchor in range(len(labels)):
            positive = labels == labels[anchor]
            positive[anchor] = False
            pos = similarity[anchor, positive]
            neg = similarity[anchor, labels != labels[anchor]]
            # Row k ranks positive k against each other positive j.
            differences = pos[None, :] - pos[:, None]
            off_diagonal = ~torch.eye(len(pos), dtype=torch.bool, device=pos.device)
            positive_rank = 1 + (
                torch.sigmoid(differences / self.temperature) * off_diagonal
            ).sum(dim=1)
            negative_rank = torch.sigmoid(
                (neg[None, :] - pos[:, None]) / self.temperature
            ).sum(dim=1)
            terms.append((positive_rank / (positive_rank + negative_rank)).mean())
        return 1 - torch.stack(terms).mean()


class RoadmapLoss(nn.Module):
    """Ramzi et al. (2021), equations 2–7, with explicit tie convention.

    Positive ranks use the hard >= comparator without a gradient. Negative
    ranks use the upper surrogate (the +0.5 branch includes a tie at zero).
    Calibration averages all pairs, including pairs with zero hinge loss.
    https://arxiv.org/abs/2110.01445
    """

    def __init__(self, parameters: RoadmapParameters):
        super().__init__()
        self.config = parameters

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        normalized = functional.normalize(embeddings, dim=1)
        similarity = normalized @ normalized.T
        ap_terms, calibration_terms = [], []
        config = self.config
        for anchor in range(len(labels)):
            positive = labels == labels[anchor]
            positive[anchor] = False
            pos = similarity[anchor, positive]
            neg = similarity[anchor, labels != labels[anchor]]
            positive_rank = (pos[None, :] >= pos[:, None]).sum(dim=1)
            difference = neg[None, :] - pos[:, None]
            sigmoid = torch.sigmoid(difference / config.temperature)
            saturation = torch.sigmoid(
                difference.new_tensor(config.delta / config.temperature)
            )
            negative_comparison = torch.where(
                difference < 0,
                sigmoid,
                torch.where(
                    difference <= config.delta,
                    sigmoid + 0.5,
                    config.rho * (difference - config.delta) + saturation + 0.5,
                ),
            )
            ap_terms.append(
                (
                    positive_rank / (positive_rank + negative_comparison.sum(dim=1))
                ).mean()
            )
            calibration_terms.append(
                functional.relu(config.positive_margin - pos).mean()
                + functional.relu(neg - config.negative_margin).mean()
            )
        ap_loss = 1 - torch.stack(ap_terms).mean()
        calibration = torch.stack(calibration_terms).mean()
        weight = config.calibration_weight
        return (1 - weight) * ap_loss + weight * calibration


class _CheckedLoss(nn.Module):
    """Validate global contiguous training labels before trainable proxy indexing."""

    def __init__(
        self, loss: nn.Module, num_classes: int, embedding_dimension: int | None
    ):
        super().__init__()
        self.loss = loss
        self.num_classes = num_classes
        self.embedding_dimension = embedding_dimension
        self.requires_raw_embeddings = getattr(loss, "requires_raw_embeddings", False)

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        if embeddings.ndim != 2 or labels.shape != (len(embeddings),):
            raise ValueError("embeddings [N,D] and labels [N] must align")
        if labels.dtype != torch.long or labels.device != embeddings.device:
            raise ValueError("labels must be int64 on the embedding device")
        if not embeddings.is_floating_point() or not torch.isfinite(embeddings).all():
            raise ValueError("embeddings must contain finite floating-point values")
        if (
            self.embedding_dimension is not None
            and embeddings.shape[1] != self.embedding_dimension
        ):
            raise ValueError(
                "embedding dimension differs from trainable class parameters"
            )
        if (
            labels.numel() == 0
            or (labels < 0).any()
            or (labels >= self.num_classes).any()
        ):
            raise ValueError(
                "map action labels globally into [0, num_classes); never per batch"
            )
        _, counts = labels.unique(return_counts=True)
        if len(counts) < 2 or (counts < 2).any():
            raise ValueError(
                "every batch needs at least two classes and two samples per class"
            )
        return self.loss(embeddings, labels)


def supports(method_id: str) -> bool:
    """Whether this module implements the declared method rather than a substitute."""
    return method_id in SUPPORTED_METHODS


def build_loss(
    method_id: str,
    parameters: dict[str, object],
    num_classes: int,
) -> nn.Module:
    """Build a scalar loss; include its parameters and state in optimizer/checkpoint.

    Labels must use one global, persisted action-to-contiguous-index mapping.
    The proxy and classifier parameters are registered children of the returned
    module, so optimizing only the embedding head would silently omit them.
    """
    if not supports(method_id):
        spec = load_methods().get(method_id)
        reason = spec.blocker if spec else "unknown method"
        raise NotImplementedError(f"{method_id}: {reason}")
    if (
        isinstance(num_classes, bool)
        or not isinstance(num_classes, int)
        or num_classes < 2
    ):
        raise ValueError("num_classes must be an integer >= 2")
    if importlib.metadata.version("pytorch-metric-learning") != PML_VERSION:
        raise RuntimeError("benchmark requires pytorch-metric-learning==2.9.0")
    parameters = dict(parameters)
    dimension = parameters.pop("embedding_dimension", None)
    if dimension is not None and (
        isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 1
    ):
        raise ValueError("embedding_dimension must be a positive integer")
    if method_id in {"proxy_anchor", "proxy_nca", "normalized_softmax", "ibc", "hist"}:
        parameters["embedding_dimension"] = dimension or 512
    if method_id in METRIX_METHODS:
        return MetrixLoss(method_id, parameters, num_classes, dimension or 512)
    if method_id == "mhgl":
        return MHGLLoss(parameters, num_classes, dimension or 512)
    if method_id == "s2sd":
        return S2SDLoss(
            S2SDParameters.model_validate(
                parameters | {"embedding_dimension": dimension or 512}
            ),
            num_classes,
        )
    if method_id == "drml":
        config = DRMLParameters.model_validate(parameters)
        if dimension is not None and dimension != 4 * config.branch_dimension:
            raise ValueError("DRML dimension differs from its four individual branches")
        return DRMLLoss(num_classes, config)
    if method_id == "contrastive":
        config = ContrastiveParameters.model_validate(parameters)
        module = PairwiseContrastiveLoss(**config.model_dump())
    elif method_id in {"contextual", "contextual_1536"}:
        module = _ScalarContextual(ContextualParameters.model_validate(parameters))
    elif method_id == "triplet":
        config = TripletParameters.model_validate(parameters)
        module = losses.TripletMarginLoss(
            margin=config.margin,
            swap=False,
            smooth_loss=False,
            triplets_per_anchor="all",
            distance=distances.LpDistance(p=2, power=1),
        )
    elif method_id == "multi_similarity":
        config = MultiSimilarityParameters.model_validate(parameters)
        module = losses.MultiSimilarityLoss(
            **config.model_dump(), distance=distances.CosineSimilarity()
        )
    elif method_id == "diml":
        config = DIMLParameters.model_validate(parameters)
        module = _MinedLoss(
            MinedMultiSimilarityParameters.model_validate(
                config.model_dump(include={"alpha", "beta", "base", "miner_epsilon"})
            )
        )
    elif method_id == "multi_similarity_miner":
        module = _MinedLoss(MinedMultiSimilarityParameters.model_validate(parameters))
    elif method_id in {"nt_xent", "supcon", "smooth_ap"}:
        config = TemperatureParameters.model_validate(parameters)
        factory = {
            "nt_xent": losses.NTXentLoss,
            "supcon": SupervisedContrastiveLoss,
            "smooth_ap": SmoothAPLoss,
        }[method_id]
        module = factory(temperature=config.temperature)
    elif method_id == "fast_ap":
        config = FastAPParameters.model_validate(parameters)
        module = losses.FastAPLoss(
            num_bins=config.num_bins, distance=distances.LpDistance(p=2, power=2)
        )
    elif method_id == "roadmap":
        module = RoadmapLoss(RoadmapParameters.model_validate(parameters))
    elif method_id == "hist":
        config = HISTParameters.model_validate(parameters)
        dimension = config.embedding_dimension
        module = HypergraphSemanticTupletLoss(config, num_classes)
    elif method_id == "ibc":
        config = IBCParameters.model_validate(parameters)
        dimension = config.embedding_dimension
        module = IntraBatchConnectionsLoss(config, num_classes)
    elif method_id == "proxy_anchor":
        config = ProxyAnchorParameters.model_validate(parameters)
        dimension = config.embedding_dimension
        module = losses.ProxyAnchorLoss(
            num_classes=num_classes,
            embedding_size=dimension,
            margin=config.margin,
            alpha=config.alpha,
            distance=distances.CosineSimilarity(),
        )
    elif method_id == "proxy_nca":
        config = ProxyNCAParameters.model_validate(parameters)
        dimension = config.embedding_dimension
        module = losses.ProxyNCALoss(
            num_classes=num_classes,
            embedding_size=dimension,
            softmax_scale=config.softmax_scale,
            distance=distances.LpDistance(p=2, power=2),
        )
    elif method_id == "proxy_nca_pp":
        config = ProxyNCAPlusParameters.model_validate(parameters)
        dimension = dimension or 512
        module = ProxyNCAPlusLoss(
            dimension, num_classes, config.temperature, config.proxy_initial_std
        )
    else:
        config = SoftmaxParameters.model_validate(parameters)
        dimension = config.embedding_dimension
        module = losses.NormalizedSoftmaxLoss(
            num_classes=num_classes,
            embedding_size=dimension,
            temperature=config.temperature,
        )
    return _CheckedLoss(module, num_classes, dimension)
