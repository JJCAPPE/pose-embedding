"""Independent DIML equations (ICCV 2021, Eqs. 2–9, supplement A).

No upstream code is used. The declared motion variant trains MS+miner and
applies optimal transport only at retrieval, with time/anatomy local sites.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import torch
import torch.nn.functional as functional
from pydantic import Field
from torch import nn

from pose_embed.benchmark.config import StrictModel

ANATOMY = ((0, 7, 8, 9, 10), (11, 12, 13), (14, 15, 16), (1, 2, 3, 4, 5, 6))


class DIMLParameters(StrictModel):
    recipe: Literal["motion_ms_miner_512_time_anatomy_v1"] = (
        "motion_ms_miner_512_time_anatomy_v1"
    )
    alpha: float = Field(default=2.0, gt=0)
    beta: float = Field(default=50.0, gt=0)
    base: float = Field(default=0.5, ge=-1, le=1)
    miner_epsilon: float = Field(default=0.1, ge=0)
    entropy: float = Field(default=0.05, gt=0)
    shortlist: Literal[100] = 100
    temporal_bins: Literal[4] = 4
    sinkhorn_tolerance: float = Field(default=1e-7, gt=0, lt=0.01)
    sinkhorn_iterations: int = Field(default=10000, ge=1)
    pair_chunk_size: int = Field(default=64, ge=1)


def _unit(values):
    values = np.asarray(values, dtype=np.float64)
    return values / np.maximum(np.linalg.norm(values, axis=-1, keepdims=True), 1e-12)


def cross_correlation_mass(local, opposite_global, valid):
    """Own local sites correlated with the opposite global vector (Eqs. 8–9)."""
    local, opposite_global = _unit(local), _unit(opposite_global)
    valid = np.asarray(valid, dtype=bool)
    if (
        local.shape[:-1] != valid.shape
        or local.shape[:-2] != opposite_global.shape[:-1]
    ):
        raise ValueError("cross-correlation descriptors are not aligned")
    scores = (
        np.maximum(np.einsum("...ld,...d->...l", local, opposite_global), 0) * valid
    )
    totals = scores.sum(axis=-1, keepdims=True)
    fallback = valid / np.maximum(valid.sum(axis=-1, keepdims=True), 1)
    return np.divide(scores, totals, out=fallback.astype(float), where=totals > 0)


def transport_plan(
    cost, source_mass, target_mass, *, entropy=0.05, tolerance=1e-7, iterations=10000
):
    """Batched log-domain Sinkhorn; fail explicitly on nonconvergence."""
    cost = np.asarray(cost, dtype=np.float64)
    source_mass, target_mass = (
        np.asarray(source_mass, dtype=float),
        np.asarray(target_mass, dtype=float),
    )
    if (
        cost.ndim < 2
        or cost.shape[:-1] != source_mass.shape
        or (*cost.shape[:-2], cost.shape[-1]) != target_mass.shape
        or not np.isfinite(cost).all()
        or not np.isfinite(source_mass).all()
        or not np.isfinite(target_mass).all()
        or (source_mass < 0).any()
        or (target_mass < 0).any()
        or not np.allclose(source_mass.sum(-1), 1)
        or not np.allclose(target_mass.sum(-1), 1)
        or entropy <= 0
        or tolerance <= 0
        or iterations < 1
    ):
        raise ValueError("transport requires finite costs and probability marginals")
    log_kernel = -cost / entropy
    with np.errstate(divide="ignore"):
        log_source, log_target = np.log(source_mass), np.log(target_mass)
    log_v = np.zeros_like(target_mass)
    converged = np.zeros(cost.shape[:-2], dtype=bool)
    result = np.zeros_like(cost)
    for _ in range(iterations):
        log_u = log_source - np.logaddexp.reduce(
            log_kernel + log_v[..., None, :], axis=-1
        )
        log_v = log_target - np.logaddexp.reduce(
            log_kernel + log_u[..., :, None], axis=-2
        )
        plan = np.exp(log_u[..., :, None] + log_kernel + log_v[..., None, :])
        error = np.maximum(
            np.max(abs(plan.sum(-1) - source_mass), axis=-1),
            np.max(abs(plan.sum(-2) - target_mass), axis=-1),
        )
        newly_converged = (~converged) & (error <= tolerance)
        result = np.where(newly_converged[..., None, None], plan, result)
        converged |= newly_converged
        if converged.all():
            return result

    raise ValueError(
        f"DIML Sinkhorn did not converge: marginal error {float(np.max(error)):.3g}"
    )


def structural_similarity(
    source, target, source_global, target_global, source_valid, target_valid, parameters
):
    source, target = _unit(source), _unit(target)
    similarity = source @ np.swapaxes(target, -1, -2)
    source_mass = cross_correlation_mass(source, target_global, source_valid)
    target_mass = cross_correlation_mass(target, source_global, target_valid)
    present = np.asarray(source_valid).any(-1) & np.asarray(target_valid).any(-1)
    result = np.zeros(present.shape, dtype=float)
    if present.any():
        plan = transport_plan(
            1 - similarity[present],
            source_mass[present],
            target_mass[present],
            entropy=parameters.entropy,
            tolerance=parameters.sinkhorn_tolerance,
            iterations=parameters.sinkhorn_iterations,
        )
        result[present] = (similarity[present] * plan).sum(axis=(-1, -2))
    return result


class DIMLHead(nn.Module):
    """Shared global/local projection; 4 temporal bins × 4 H36M body groups."""

    requires_valid_mask = True

    def __init__(self, embedding_dimension, representation_dimension, parameters=None):
        super().__init__()
        self.projection = nn.Linear(representation_dimension, embedding_dimension)
        self.parameters_recipe = DIMLParameters.model_validate(parameters or {})

    def _pooled(self, features, mask):
        if (
            features.ndim != 5
            or features.shape[-2] != 17
            or features.shape[-1] != self.projection.in_features
            or mask.shape != features.shape[:-1]
            or mask.dtype != torch.bool
            or mask.device != features.device
            or any(size == 0 for size in features.shape)
        ):
            raise ValueError("DIML requires aligned H36M-17 tokens and confidence mask")
        return (features * mask.unsqueeze(-1)).sum((1, 2, 3)) / mask.sum(
            (1, 2, 3)
        ).clamp_min(1).unsqueeze(-1)

    def forward_raw(self, features, valid_mask):
        projected = self.projection(self._pooled(features, valid_mask))
        return projected * valid_mask.any((1, 2, 3)).unsqueeze(-1)

    def forward(self, features, valid_mask):
        return functional.normalize(self.forward_raw(features, valid_mask), dim=-1)

    def forward_descriptors(self, features, valid_mask):
        embeddings = self(features, valid_mask)
        local, validity = [], []
        frames = features.shape[2]
        for time in range(4):
            start, end = time * frames // 4, (time + 1) * frames // 4
            for joints in ANATOMY:
                mask = valid_mask[:, :, start:end, joints]
                token = features[:, :, start:end, joints, :]
                present = mask.any((1, 2, 3))
                pooled = (token * mask.unsqueeze(-1)).sum((1, 2, 3)) / mask.sum(
                    (1, 2, 3)
                ).clamp_min(1).unsqueeze(-1)
                local.append(self.projection(pooled) * present.unsqueeze(-1))
                validity.append(present)
        return {
            "embeddings": embeddings,
            "local": torch.stack(local, dim=1),
            "local_mask": torch.stack(validity, dim=1),
        }

    def make_retrieval_scorer(self, query, gallery):
        return DIMLScorer(query, gallery, self.parameters_recipe)


class DIMLScorer:
    """Eligible global top-100 prefix reranked by global+OT; global tail retained."""

    def __init__(self, query, gallery, parameters):
        self.parameters = parameters
        self.query, self.gallery = {}, {}
        sources = (
            ((query, self.query),)
            if query is gallery
            else ((query, self.query), (gallery, self.gallery))
        )
        if query is gallery:
            self.gallery = self.query
        for source, destination in sources:
            if set(source) != {"embeddings", "local", "local_mask"}:
                raise ValueError("DIML requires global/local/mask descriptors")
            n, d = np.asarray(source["embeddings"]).shape
            if (
                np.asarray(source["local"]).shape != (n, 16, d)
                or np.asarray(source["local_mask"]).shape != (n, 16)
                or np.asarray(source["local_mask"]).dtype != np.bool_
            ):
                raise ValueError("DIML descriptor shapes or mask dtype are invalid")
            for name, value in source.items():
                array = np.array(value, copy=True)
                if not np.isfinite(array).all():
                    raise ValueError("DIML descriptors must be finite")
                destination[name] = array
            destination["embeddings"] = _unit(destination["embeddings"])
            destination["local"] = _unit(destination["local"])
        if self.query["embeddings"].shape[1] != self.gallery["embeddings"].shape[1]:
            raise ValueError("DIML query and gallery dimensions differ")

    def __call__(self, query_indices, gallery_indices, excluded_gallery_indices=None):
        qids, gids = (
            np.asarray(query_indices, dtype=int),
            np.asarray(gallery_indices, dtype=int),
        )
        excluded_gallery_indices = excluded_gallery_indices or [[] for _ in qids]
        if len(excluded_gallery_indices) != len(qids):
            raise ValueError("DIML exclusions must align with query rows")
        output = self.query["embeddings"][qids] @ self.gallery["embeddings"][gids].T
        for row, (qid, exclusions) in enumerate(
            zip(qids, excluded_gallery_indices, strict=True)
        ):
            eligible = np.flatnonzero(~np.isin(gids, exclusions))
            order = eligible[np.argsort(-output[row, eligible], kind="stable")]
            shortlist = order[: self.parameters.shortlist]
            for start in range(0, len(shortlist), self.parameters.pair_chunk_size):
                positions = shortlist[start : start + self.parameters.pair_chunk_size]
                selected = gids[positions]
                count = len(positions)
                scores = structural_similarity(
                    np.repeat(self.query["local"][qid : qid + 1], count, axis=0),
                    self.gallery["local"][selected],
                    np.repeat(self.query["embeddings"][qid : qid + 1], count, axis=0),
                    self.gallery["embeddings"][selected],
                    np.repeat(self.query["local_mask"][qid : qid + 1], count, axis=0),
                    self.gallery["local_mask"][selected],
                    self.parameters,
                )
                # Offset preserves prefix: combined scores in [-2,2], tail in [-1,1].
                output[row, positions] += 4 + scores
        return output
