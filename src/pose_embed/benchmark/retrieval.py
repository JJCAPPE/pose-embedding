"""Exact multi-positive retrieval with per-query performance exclusions."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import torch

from pose_embed.data.manifest import ManifestRecord
from pose_embed.data.ntu import NTUSampleId, parse_ntu_sample_id

RETRIEVAL_POLICY = {
    "similarity": "cosine_after_l2_normalization",
    "relevance": "same_action_after_exclusions",
    "exclusion": "self_and_all_synchronized_performance_views",
    "tie_break": "gallery_manifest_order",
    "recall": "at_least_one_relevant_item_in_first_k",
    "average_precision": "all_valid_relevant_items",
    "average_precision_at_r": "first_r_ranks_divided_by_valid_relevant_count",
    "aggregation": "unweighted_mean_over_queries",
}

CUSTOM_SCORERS = {
    "diml": "diml_cross_correlation_transport_multiscale",
    "proxy_anchor_avsl": "avsl_negative_hierarchical_distance",
}


def method_retrieval_policy(method_id: str, parameters: Mapping | None = None) -> dict:
    policy = dict(RETRIEVAL_POLICY)
    if method_id in CUSTOM_SCORERS:
        if parameters is None:
            raise ValueError("custom retrieval requires its bound method parameters")
        policy["similarity"] = CUSTOM_SCORERS[method_id]
        policy["scoring_arithmetic"] = "cpu_float64"
        policy["scoring_specification_sha256"] = _digest(
            {"method_id": method_id, "parameters": dict(parameters)}
        )
    return policy


def common_retrieval_policy(policy: Mapping) -> dict:
    """Comparison conditions shared by cosine and declared structural scorers."""
    return {key: policy[key] for key in RETRIEVAL_POLICY if key != "similarity"}


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _identities(
    records: Sequence[ManifestRecord | Mapping[str, Any]], label: str
) -> list[NTUSampleId]:
    identities = []
    for record in records:
        sample_id = (
            record.sample_id
            if isinstance(record, ManifestRecord)
            else record.get("sample_id")
        )
        if not isinstance(sample_id, str):
            raise ValueError(f"{label} records require string sample_id values")
        identity = parse_ntu_sample_id(sample_id)
        if identity.sample_id != sample_id:
            raise ValueError(f"{label} sample IDs must be canonical NTU identities")
        identities.append(identity)
    if len({row.sample_id for row in identities}) != len(identities):
        raise ValueError(f"{label} sample IDs must be unique")
    return identities


def _validated_vectors(
    values: Any, count: int, label: str, *, normalize: bool
) -> torch.Tensor:
    embeddings = torch.as_tensor(values).detach()
    if embeddings.ndim != 2 or embeddings.shape[0] != count:
        raise ValueError(f"{label} embeddings must be [N,D] aligned with records")
    if count == 0 or embeddings.shape[1] == 0:
        raise ValueError(f"{label} embeddings must have positive dimensions")
    if not embeddings.is_floating_point():
        raise ValueError(f"{label} embeddings must have a floating-point dtype")
    if not torch.isfinite(embeddings).all():
        raise ValueError(f"{label} embeddings must contain only finite values")
    if embeddings.dtype not in {torch.float32, torch.float64}:
        embeddings = embeddings.to(torch.float32)
    if not normalize:
        return embeddings
    # Scaling first avoids overflow/underflow for finite, nonzero input vectors.
    scale = embeddings.abs().amax(dim=1, keepdim=True)
    if (scale == 0).any():
        raise ValueError(f"{label} embeddings contain zero-norm vectors")
    scaled = embeddings / scale
    return scaled / torch.linalg.vector_norm(scaled, dim=1, keepdim=True)


def evaluate_retrieval(
    query_embeddings: Any,
    gallery_embeddings: Any,
    query_records: Sequence[ManifestRecord | Mapping[str, Any]],
    gallery_records: Sequence[ManifestRecord | Mapping[str, Any]],
    recall_k: Sequence[int] = (1, 2, 4, 8),
    chunk_size: int = 128,
    *,
    score_rows: Callable | None = None,
    scoring_policy: Mapping | None = None,
) -> dict[str, Any]:
    """Rank every valid candidate exactly, retaining only relevant-item ranks.

    Query and gallery pools may overlap. Each query excludes its own sample and
    every camera view sharing setup, performer, repetition, and action. Recall
    uses the metric-learning any-hit convention; AP@R divides by the number of
    valid relevant gallery items, including those ranked below R.
    """
    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size < 1
    ):
        raise ValueError("chunk_size must be a positive integer")
    policy = dict(RETRIEVAL_POLICY if scoring_policy is None else scoring_policy)
    if score_rows is None:
        if policy != RETRIEVAL_POLICY:
            raise ValueError("non-cosine policy requires its actual retrieval scorer")
    elif (
        set(policy)
        != set(RETRIEVAL_POLICY)
        | {"scoring_specification_sha256", "scoring_arithmetic"}
        or common_retrieval_policy(policy) != common_retrieval_policy(RETRIEVAL_POLICY)
        or policy["similarity"] not in CUSTOM_SCORERS.values()
        or policy["scoring_arithmetic"] != "cpu_float64"
        or not isinstance(policy["scoring_specification_sha256"], str)
        or len(policy["scoring_specification_sha256"]) != 64
    ):
        raise ValueError("custom retrieval requires a complete declared scoring policy")
    cutoffs = tuple(recall_k)
    if (
        not cutoffs
        or any(isinstance(k, bool) or not isinstance(k, int) or k < 1 for k in cutoffs)
        or len(set(cutoffs)) != len(cutoffs)
    ):
        raise ValueError("recall_k must contain distinct positive integers")
    queries = _identities(query_records, "query")
    galleries = _identities(gallery_records, "gallery")
    query_vectors = _validated_vectors(
        query_embeddings, len(queries), "query", normalize=score_rows is None
    )
    gallery_vectors = _validated_vectors(
        gallery_embeddings, len(galleries), "gallery", normalize=score_rows is None
    )
    if query_vectors.shape[1] != gallery_vectors.shape[1]:
        raise ValueError("query and gallery embedding dimensions differ")
    if query_vectors.device != gallery_vectors.device:
        raise ValueError("query and gallery embeddings must share a device")
    dtype = torch.promote_types(query_vectors.dtype, gallery_vectors.dtype)
    query_vectors = query_vectors.to(dtype)
    gallery_vectors = gallery_vectors.to(dtype)
    gallery_labels = torch.tensor(
        [row.action for row in galleries], device=gallery_vectors.device
    )
    performance_indexes: dict[tuple[int, int, int, int], list[int]] = defaultdict(list)
    for index, row in enumerate(galleries):
        performance_indexes[row.performance_id].append(index)
    exclusions = [performance_indexes[row.performance_id] for row in queries]
    per_query: list[dict[str, Any]] = []
    with torch.no_grad():
        for start in range(0, len(queries), chunk_size):
            stop = min(start + chunk_size, len(queries))
            if score_rows is None:
                scores = query_vectors[start:stop] @ gallery_vectors.T
            else:
                scores = torch.as_tensor(
                    score_rows(
                        list(range(start, stop)),
                        list(range(len(galleries))),
                        exclusions[start:stop],
                    ),
                    device=query_vectors.device,
                ).clone()
                if (
                    scores.shape != (stop - start, len(galleries))
                    or not scores.is_floating_point()
                    or not torch.isfinite(scores).all()
                ):
                    raise ValueError(
                        "custom scorer must return finite floating-point [Q,G] scores"
                    )
            for offset in range(len(scores)):
                excluded = exclusions[start + offset]
                scores[offset, excluded] = -torch.inf
            order = torch.argsort(scores, dim=1, descending=True, stable=True)
            ranked_labels = gallery_labels[order]
            for offset in range(len(scores)):
                query = queries[start + offset]
                excluded = exclusions[start + offset]
                valid_count = len(galleries) - len(excluded)
                relevant_ranks = (
                    (
                        torch.nonzero(
                            ranked_labels[offset, :valid_count] == query.action,
                            as_tuple=True,
                        )[0]
                        + 1
                    )
                    .cpu()
                    .tolist()
                )
                relevant_count = len(relevant_ranks)
                if relevant_count == 0:
                    raise ValueError(
                        f"query {query.sample_id} has no relevant gallery item "
                        "after performance exclusions"
                    )
                precision = [
                    position / rank
                    for position, rank in enumerate(relevant_ranks, start=1)
                ]
                first_rank = relevant_ranks[0]
                per_query.append(
                    {
                        "sample_id": query.sample_id,
                        "label": query.action,
                        "valid_gallery_count": valid_count,
                        "relevant_count": relevant_count,
                        "excluded_gallery_ids": [
                            galleries[index].sample_id for index in excluded
                        ],
                        "relevant_ranks": relevant_ranks,
                        "first_relevant_rank": first_rank,
                        "average_precision": sum(precision) / relevant_count,
                        "average_precision_at_r": sum(
                            value
                            for value, rank in zip(
                                precision, relevant_ranks, strict=True
                            )
                            if rank <= relevant_count
                        )
                        / relevant_count,
                        "reciprocal_rank": 1.0 / first_rank,
                        "recall_at_k": {str(k): first_rank <= k for k in cutoffs},
                    }
                )
    query_ids = [row.sample_id for row in queries]
    gallery_ids = [row.sample_id for row in galleries]
    metrics = {
        name: sum(row[key] for row in per_query) / len(per_query)
        for name, key in (
            ("map", "average_precision"),
            ("map_at_r", "average_precision_at_r"),
            ("mrr", "reciprocal_rank"),
        )
    }
    metrics.update(
        {
            f"r_at_{k}": sum(row["recall_at_k"][str(k)] for row in per_query)
            / len(per_query)
            for k in cutoffs
        }
    )
    metrics.update(query_count=len(queries), gallery_count=len(galleries))
    return {
        "schema_version": 1,
        "policy": policy,
        "query_sample_ids": query_ids,
        "gallery_sample_ids": gallery_ids,
        "query_order_sha256": _digest(query_ids),
        "gallery_order_sha256": _digest(gallery_ids),
        "exclusion_sha256": _digest(
            [
                {"sample_id": row["sample_id"], "excluded": row["excluded_gallery_ids"]}
                for row in per_query
            ]
        ),
        "metrics": metrics,
        "per_query": per_query,
    }
