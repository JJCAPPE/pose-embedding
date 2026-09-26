"""Independent Metrix equations (Venkataramanan et al., ICLR 2022, Eqs. 7–10).

The official MIT release is pinned as a reference in third_party/upstreams.toml.
It does not contain the three feature variants here. The declared motion
adaptation mixes final encoder tokens, never normalized retrieval embeddings.
"""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as F
from pydantic import Field
from pytorch_metric_learning import distances, miners
from torch import nn
from torch.utils.checkpoint import checkpoint

from pose_embed.benchmark.config import StrictModel
from pose_embed.benchmark.proxy_nca_plus import ProxyNCAPlusParameters

METRIX_METHODS = frozenset(
    {"multi_similarity_metrix", "proxy_anchor_metrix", "proxy_nca_metrix"}
)


class MetrixParameters(StrictModel):
    beta_shape: Literal[2.0] = 2.0
    mix_strength: float = Field(default=0.4, ge=0)
    mixing_layer: Literal["final_motionbert_tokens"] = "final_motionbert_tokens"
    mixed_mask: Literal["intersection_with_exact_endpoints"] = (
        "intersection_with_exact_endpoints"
    )
    feature_chunk_size: int = Field(default=2, ge=1)


class MetrixMSParameters(MetrixParameters):
    pair_strategy: Literal["uniform_positive_negative_or_anchor_negative"] = (
        "uniform_positive_negative_or_anchor_negative"
    )
    positive_scale: float = Field(default=18.0, gt=0)
    negative_scale: float = Field(default=75.0, gt=0)
    base: float = Field(default=0.77, ge=-1, le=1)
    miner_epsilon: float = Field(default=0.39, ge=0)


class MetrixPAParameters(MetrixParameters):
    pair_strategy: Literal["proxy_relative_positive_negative"] = (
        "proxy_relative_positive_negative"
    )
    alpha: float = Field(default=32.0, gt=0)
    margin: float = Field(default=0.1, ge=0, le=1)


class MetrixNCAParameters(MetrixParameters, ProxyNCAPlusParameters):
    pair_strategy: Literal["mixed_anchor_all_cross_class_pairs"] = (
        "mixed_anchor_all_cross_class_pairs"
    )


class MetrixMeanMaxHead(nn.Module):
    """Motion analogue of the paper's final-map average + maximum pooling."""

    requires_valid_mask = True

    def __init__(self, embedding_dimension: int, representation_dimension: int):
        super().__init__()
        self.projection = nn.Linear(representation_dimension, embedding_dimension)

    def forward_raw(self, features, valid_mask):
        if features.ndim != 5 or valid_mask.shape != features.shape[:-1]:
            raise ValueError("features [B,P,T,J,C] and token validity must align")
        if valid_mask.dtype != torch.bool:
            raise ValueError("token validity must be boolean")
        flattened = features.flatten(1, 3)
        valid = valid_mask.flatten(1, 3).unsqueeze(-1)
        count = valid.sum(dim=1)
        mean = flattened.masked_fill(~valid, 0).sum(dim=1) / count.clamp_min(1)
        maximum = flattened.masked_fill(~valid, -torch.inf).amax(dim=1)
        maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
        return self.projection(mean + maximum)

    def forward(self, features, valid_mask):
        return F.normalize(self.forward_raw(features, valid_mask), dim=-1)


def mix_features(left, right, left_mask, right_mask, coefficient):
    """Mask interior mixes conservatively; exact endpoints preserve their source."""
    if not 0 <= coefficient <= 1:
        raise ValueError("mixing coefficient must be in [0,1]")
    if left.shape != right.shape or left_mask.shape != left.shape[:-1]:
        raise ValueError("both source feature maps and masks must align")
    if right_mask.shape != left_mask.shape:
        raise ValueError("both source validity masks must align")
    mask = (
        left_mask
        if coefficient == 1
        else right_mask
        if coefficient == 0
        else left_mask & right_mask
    )
    return coefficient * left + (1 - coefficient) * right, mask


def cross_class_pairs(labels):
    """Every ordered cross-class pair once, in deterministic row-major order."""
    return torch.where(labels[:, None] != labels[None, :])


def mixed_class_targets(labels, left, right, coefficient, num_classes, dtype=None):
    dtype = dtype or torch.get_default_dtype()
    return coefficient * F.one_hot(labels[left], num_classes).to(dtype) + (
        1 - coefficient
    ) * F.one_hot(labels[right], num_classes).to(dtype)


def ms_mining_masks(embeddings, labels, epsilon):
    miner = miners.MultiSimilarityMiner(
        epsilon=epsilon, distance=distances.CosineSimilarity()
    )
    a, p, b, n = miner(embeddings, labels)
    positive = embeddings.new_zeros((len(labels), len(labels)), dtype=torch.bool)
    negative = torch.zeros_like(positive)
    positive[a, p] = True
    negative[b, n] = True
    return positive, negative


def _weighted_log1pexp(logits, weights, dim):
    """log(1 + sum weight*exp(logit)); zero weights have exact zero gradient."""
    weights = weights.to(logits.dtype)
    logged = weights.clamp_min(torch.finfo(logits.dtype).tiny).log()
    terms = (logits + logged).masked_fill(weights == 0, -torch.inf)
    shape = list(terms.shape)
    shape[dim] = 1
    return torch.logsumexp(torch.cat([terms, terms.new_zeros(shape)], dim=dim), dim=dim)


def multi_similarity_terms(similarities, positive, negative, parameters):
    return (
        _weighted_log1pexp(
            -parameters.positive_scale * (similarities - parameters.base),
            positive,
            1,
        )
        / parameters.positive_scale
        + _weighted_log1pexp(
            parameters.negative_scale * (similarities - parameters.base),
            negative,
            1,
        )
        / parameters.negative_scale
    ).mean()


def proxy_anchor_terms(similarities, targets, parameters, negative_weights=None):
    """PA positive average covers present proxies; negative average covers all."""
    positive = _weighted_log1pexp(
        -parameters.alpha * (similarities - parameters.margin), targets, 0
    )
    negative = _weighted_log1pexp(
        parameters.alpha * (similarities + parameters.margin),
        1 - targets if negative_weights is None else negative_weights,
        0,
    )
    present = (targets > 0).any(dim=0)
    return positive.sum() / present.sum().clamp_min(1) + negative.mean()


def proxy_nca_terms(logits, targets):
    """Eq. 9 weights positive probabilities INSIDE log; denominator is all proxies."""
    weighted = logits + targets.clamp_min(torch.finfo(logits.dtype).tiny).log()
    weighted = weighted.masked_fill(targets == 0, -torch.inf)
    return (torch.logsumexp(logits, dim=1) - torch.logsumexp(weighted, dim=1)).mean()


class MetrixLoss(nn.Module):
    """Training-only clean + 0.4*mixed objective with a single encoder forward.

    ``forward`` intentionally refuses embedding-only use: the complete method
    requires ``training_loss(model, poses, labels)`` and the model's token API.
    ProxyNCA++ optimizer/head requirements are supplied by the method factory.
    """

    requires_feature_training = True

    def __init__(self, method_id, parameters, num_classes, embedding_dimension):
        super().__init__()
        if method_id not in METRIX_METHODS:
            raise ValueError("unknown Metrix variant")
        self.method_id = method_id
        self.num_classes = num_classes
        self.embedding_dimension = embedding_dimension
        parameter_type = {
            "multi_similarity_metrix": MetrixMSParameters,
            "proxy_anchor_metrix": MetrixPAParameters,
            "proxy_nca_metrix": MetrixNCAParameters,
        }[method_id]
        self.config = parameter_type.model_validate(parameters)
        if method_id != "multi_similarity_metrix":
            self.proxies = nn.Parameter(torch.empty(num_classes, embedding_dimension))
            if method_id == "proxy_nca_metrix":
                nn.init.normal_(self.proxies, std=self.config.proxy_initial_std)
            else:
                nn.init.kaiming_normal_(self.proxies, mode="fan_out")

    def forward(self, embeddings, labels):
        raise RuntimeError(
            "Metrix requires feature training, not an embedding-only loss"
        )

    def _validate_labels(self, labels, batch, device):
        if (
            labels.shape != (batch,)
            or labels.dtype != torch.long
            or labels.device != device
        ):
            raise ValueError(
                "global int64 labels must align with input batch and device"
            )
        if (labels < 0).any() or (labels >= self.num_classes).any():
            raise ValueError("map action labels globally into [0, num_classes)")
        _, counts = labels.unique(return_counts=True)
        if len(counts) < 2 or (counts < 2).any():
            raise ValueError(
                "Metrix requires two or more examples of two or more classes"
            )

    def clean_loss(self, embeddings, labels):
        embedded = F.normalize(embeddings, dim=-1)
        if self.method_id == "multi_similarity_metrix":
            positive, negative = ms_mining_masks(
                embedded, labels, self.config.miner_epsilon
            )
            return multi_similarity_terms(
                embedded @ embedded.T, positive, negative, self.config
            )
        targets = F.one_hot(labels, self.num_classes).to(embedded.dtype)
        proxies = F.normalize(self.proxies, dim=-1)
        similarities = embedded @ proxies.T
        if self.method_id == "proxy_anchor_metrix":
            return proxy_anchor_terms(similarities, targets, self.config)
        return proxy_nca_terms(self._proxy_logits(embedded, proxies), targets)

    def _proxy_logits(self, embeddings, proxies):
        squared_distances = (
            embeddings.square().sum(dim=-1, keepdim=True)
            + proxies.square().sum(dim=-1).unsqueeze(0)
            - 2 * embeddings @ proxies.T
        )
        return -squared_distances / self.config.temperature

    def mixed_loss(self, clean, mixed, labels, left, right, coefficient, mode):
        if mode not in {"positive_negative", "anchor_negative"}:
            raise ValueError("unknown mixing pair mode")
        if self.method_id == "multi_similarity_metrix":
            anchors = torch.arange(len(labels), device=labels.device)[:, None]
            if mode == "anchor_negative":
                eligible = anchors == left[None, :]
            else:
                eligible = (labels[:, None] == labels[left][None, :]) & (
                    anchors != left[None, :]
                )
            eligible &= labels[:, None] != labels[right][None, :]
            eligible = eligible.to(clean.dtype)
            return multi_similarity_terms(
                clean @ mixed.T,
                coefficient * eligible,
                (1 - coefficient) * eligible,
                self.config,
            )
        targets = mixed_class_targets(
            labels, left, right, coefficient, self.num_classes, mixed.dtype
        )
        similarities = mixed @ F.normalize(self.proxies, dim=-1).T
        if self.method_id == "proxy_anchor_metrix":
            # Eq. 8: for each proxy anchor, M(a) = U+(a) x U-(a).
            # A proxy has no encoder feature map for an anchor-negative mix.
            eligible = F.one_hot(labels[left], self.num_classes).to(mixed.dtype)
            return proxy_anchor_terms(
                similarities,
                coefficient * eligible,
                self.config,
                (1 - coefficient) * eligible,
            )
        return proxy_nca_terms(
            self._proxy_logits(mixed, F.normalize(self.proxies, dim=-1)), targets
        )

    def training_loss(self, model, poses, labels):
        if not self.training or not model.training:
            raise RuntimeError("Metrix mixing is training-only")
        if model.method_id != self.method_id:
            raise ValueError("Metrix requires its declared feature head")
        self._validate_labels(labels, len(poses), poses.device)
        features = model.forward_features(poses)
        valid = poses[..., 2] > 0
        clean = model.project_features(features, valid)
        clean_loss = self.clean_loss(clean, labels)
        if self.config.mix_strength == 0:
            return clean_loss
        left, right = cross_class_pairs(labels)
        # One shared factor per iteration, matching the released sampling helper.
        coefficient = float(torch.distributions.Beta(2.0, 2.0).sample())
        mode = "positive_negative"
        if self.method_id == "multi_similarity_metrix" and torch.randint(2, ()).item():
            mode = "anchor_negative"
        chunks = []

        def project(source, first, second):
            mixed, mask = mix_features(
                source[first], source[second], valid[first], valid[second], coefficient
            )
            return model.project_features(mixed, mask)

        for start in range(0, len(left), self.config.feature_chunk_size):
            first = left[start : start + self.config.feature_chunk_size]
            second = right[start : start + self.config.feature_chunk_size]
            # Store the original features once; rematerialize mixed maps on backward.
            chunks.append(
                checkpoint(project, features, first, second, use_reentrant=False)
            )
        mixed = torch.cat(chunks)
        return clean_loss + self.config.mix_strength * self.mixed_loss(
            clean, mixed, labels, left, right, coefficient, mode
        )
