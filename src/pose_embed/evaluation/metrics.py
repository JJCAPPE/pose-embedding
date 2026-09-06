"""Cosine one-shot retrieval with auditable per-query ranks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import torch
import torch.nn.functional as functional


@dataclass(frozen=True)
class QueryRetrieval:
    sample_id: str
    label: int
    rank: int
    predicted_label: int
    top1_correct: bool


@dataclass(frozen=True)
class RetrievalEvaluation:
    top1: float
    mrr: float
    r_at_5: float
    query_count: int
    gallery_count: int
    per_query: tuple[QueryRetrieval, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "top1": self.top1,
            "mrr": self.mrr,
            "r_at_5": self.r_at_5,
            "query_count": self.query_count,
            "gallery_count": self.gallery_count,
            "per_query": [asdict(row) for row in self.per_query],
        }


def evaluate_one_shot(
    gallery_embeddings: torch.Tensor,
    gallery_labels: torch.Tensor,
    query_embeddings: torch.Tensor,
    query_labels: torch.Tensor,
    *,
    query_ids: Sequence[str] | None = None,
) -> RetrievalEvaluation:
    """Evaluate one clean gallery example per class by cosine similarity."""
    if gallery_embeddings.ndim != 2 or query_embeddings.ndim != 2:
        raise ValueError("gallery and query embeddings must be rank-2 tensors")
    if gallery_embeddings.shape[1] != query_embeddings.shape[1]:
        raise ValueError("gallery and query embedding dimensions differ")
    if gallery_labels.shape != (gallery_embeddings.shape[0],):
        raise ValueError("gallery_labels must align with gallery embeddings")
    if query_labels.shape != (query_embeddings.shape[0],):
        raise ValueError("query_labels must align with query embeddings")
    if gallery_embeddings.shape[0] == 0 or query_embeddings.shape[0] == 0:
        raise ValueError("gallery and query sets must be non-empty")
    if (
        not torch.isfinite(gallery_embeddings).all()
        or not torch.isfinite(query_embeddings).all()
    ):
        raise ValueError("gallery and query embeddings must contain only finite values")
    if torch.unique(gallery_labels).numel() != gallery_labels.numel():
        raise ValueError(
            "one-shot evaluation requires exactly one gallery item per label"
        )
    gallery_classes = set(gallery_labels.detach().cpu().tolist())
    missing = sorted(set(query_labels.detach().cpu().tolist()) - gallery_classes)
    if missing:
        raise ValueError(f"queries contain labels absent from the gallery: {missing}")
    if query_ids is None:
        query_ids = tuple(f"query-{index}" for index in range(len(query_labels)))
    if len(query_ids) != len(query_labels):
        raise ValueError("query_ids must have one value per query")

    gallery = functional.normalize(gallery_embeddings, dim=1)
    queries = functional.normalize(query_embeddings, dim=1)
    similarities = queries @ gallery.T
    order = torch.argsort(similarities, dim=1, descending=True, stable=True)
    ranked_labels = gallery_labels[order]
    matches = ranked_labels.eq(query_labels[:, None])
    ranks = matches.to(torch.int64).argmax(dim=1) + 1
    predicted = ranked_labels[:, 0]

    per_query = tuple(
        QueryRetrieval(
            sample_id=str(query_ids[index]),
            label=int(query_labels[index]),
            rank=int(ranks[index]),
            predicted_label=int(predicted[index]),
            top1_correct=bool(ranks[index] == 1),
        )
        for index in range(len(query_labels))
    )
    reciprocal = 1.0 / ranks.to(torch.float64)
    return RetrievalEvaluation(
        top1=float((ranks == 1).to(torch.float64).mean()),
        mrr=float(reciprocal.mean()),
        r_at_5=float((ranks <= 5).to(torch.float64).mean()),
        query_count=len(query_labels),
        gallery_count=len(gallery_labels),
        per_query=per_query,
    )
