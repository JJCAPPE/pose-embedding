from __future__ import annotations

import json

import numpy as np
import pytest
import torch

from pose_embed.benchmark.retrieval import evaluate_retrieval
from pose_embed.data.manifest import ManifestRecord
from pose_embed.data.ntu import parse_ntu_sample_id


def _record(action: int, performer: int, camera: int = 1) -> dict[str, str]:
    return {"sample_id": f"S001C{camera:03d}P{performer:03d}R001A{action:03d}"}


def test_hand_calculated_ap_and_ap_at_r_use_all_valid_positives() -> None:
    query = [_record(1, 1)]
    gallery = [
        _record(1, 1),
        _record(1, 1, 2),
        _record(2, 3),
        _record(1, 2),
        _record(2, 4),
        _record(1, 3),
    ]
    result = evaluate_retrieval(
        np.array([[2.0, 0.0]]),
        np.array([[1.0, 0.0], [1, 0], [1, 0], [0.8, 0.6], [0.6, 0.8], [0, 1]]),
        query,
        gallery,
    )
    row = result["per_query"][0]
    assert row["relevant_ranks"] == [2, 4]
    assert row["excluded_gallery_ids"] == [
        record["sample_id"] for record in gallery[:2]
    ]
    assert row["valid_gallery_count"] == 4
    assert row["relevant_count"] == 2
    assert result["metrics"] == {
        "map": 0.5,
        "map_at_r": 0.25,
        "mrr": 0.5,
        "r_at_1": 0.0,
        "r_at_2": 1.0,
        "r_at_4": 1.0,
        "r_at_8": 1.0,
        "query_count": 1,
        "gallery_count": 6,
    }
    json.dumps(result, allow_nan=False)


def test_chunked_shared_pool_matches_independent_dense_reference() -> None:
    records = [
        ManifestRecord(
            sample_id=_record(action, performer, camera)["sample_id"],
            split="development_validation",
        )
        for action in (2, 8)
        for performer in (1, 2, 3)
        for camera in (1, 2)
    ]
    features = np.random.default_rng(31).normal(size=(len(records), 7))
    baseline = evaluate_retrieval(features, features, records, records, chunk_size=128)
    for chunk_size in (1, 3, 5):
        assert (
            evaluate_retrieval(
                features, features, records, records, chunk_size=chunk_size
            )
            == baseline
        )
    normalized = features / np.linalg.norm(features, axis=1, keepdims=True)
    scores = normalized @ normalized.T
    for i, query in enumerate(records):
        valid = [
            j
            for j, gallery in enumerate(records)
            if gallery.ntu.performance_id != query.ntu.performance_id
        ]
        order = sorted(valid, key=lambda j: (-scores[i, j], j))
        ranks = [
            rank
            for rank, j in enumerate(order, start=1)
            if records[j].ntu.action == query.ntu.action
        ]
        assert baseline["per_query"][i]["relevant_ranks"] == ranks
        assert baseline["per_query"][i]["relevant_count"] == 4


def test_exact_ties_follow_gallery_order_after_exclusions() -> None:
    query = [_record(1, 1)]
    gallery = [_record(1, 1), _record(2, 2), _record(1, 2)]
    embeddings = torch.ones((3, 2))
    first = evaluate_retrieval(embeddings[:1], embeddings, query, gallery)
    reordered = evaluate_retrieval(
        embeddings[:1], embeddings, query, [gallery[0], gallery[2], gallery[1]]
    )
    assert first["per_query"][0]["relevant_ranks"] == [2]
    assert reordered["per_query"][0]["relevant_ranks"] == [1]
    assert first["gallery_order_sha256"] != reordered["gallery_order_sha256"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 0.0])
def test_invalid_vectors_are_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="finite|zero-norm"):
        evaluate_retrieval(
            np.array([[value, value]]),
            np.ones((1, 2)),
            [_record(1, 1)],
            [_record(1, 2)],
        )


@pytest.mark.parametrize("records_side", ["query", "gallery"])
def test_duplicate_identities_are_rejected(records_side: str) -> None:
    query = [_record(1, 1)]
    gallery = [_record(1, 2)]
    if records_side == "query":
        query *= 2
    else:
        gallery *= 2
    with pytest.raises(ValueError, match="unique"):
        evaluate_retrieval(
            np.ones((len(query), 2)), np.ones((len(gallery), 2)), query, gallery
        )


@pytest.mark.parametrize("gallery", [[_record(1, 1, 2)], [_record(2, 2)]])
def test_missing_positive_after_exclusions_is_rejected(gallery: list[dict]) -> None:
    with pytest.raises(ValueError, match="no relevant gallery item"):
        evaluate_retrieval(np.ones((1, 2)), np.ones((1, 2)), [_record(1, 1)], gallery)


def test_dimension_alignment_cutoffs_and_chunk_size_are_validated() -> None:
    query, gallery = [_record(1, 1)], [_record(1, 2)]
    with pytest.raises(ValueError, match="dimensions differ"):
        evaluate_retrieval(np.ones((1, 2)), np.ones((1, 3)), query, gallery)
    with pytest.raises(ValueError, match="aligned"):
        evaluate_retrieval(np.ones((2, 2)), np.ones((1, 2)), query, gallery)
    for cutoffs in ((), (1, 1), (0,), (True,), (1.5,)):
        with pytest.raises(ValueError, match="recall_k"):
            evaluate_retrieval(
                np.ones((1, 2)), np.ones((1, 2)), query, gallery, cutoffs
            )
    for size in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="chunk_size"):
            evaluate_retrieval(
                np.ones((1, 2)), np.ones((1, 2)), query, gallery, chunk_size=size
            )


def test_extreme_finite_vectors_are_normalized_without_overflow() -> None:
    result = evaluate_retrieval(
        torch.tensor([[1e30, 1e30]], dtype=torch.float32),
        torch.tensor([[1e-30, 1e-30]], dtype=torch.float32),
        [_record(1, 1)],
        [_record(1, 2)],
    )
    assert result["metrics"]["map"] == 1.0


def test_canonical_identity_required_and_camera_is_not_performance_identity() -> None:
    with pytest.raises(ValueError, match="canonical"):
        evaluate_retrieval(
            np.ones((1, 2)),
            np.ones((1, 2)),
            [{"sample_id": _record(1, 1)["sample_id"].lower()}],
            [_record(1, 2)],
        )
    left = parse_ntu_sample_id(_record(1, 1)["sample_id"])
    mate = parse_ntu_sample_id(_record(1, 1, 2)["sample_id"])
    assert left.performance_id == mate.performance_id


@pytest.mark.parametrize("failure", ["shape", "nan", "integer", "policy"])
def test_custom_callback_must_supply_declared_finite_scores(failure):
    from pose_embed.benchmark.retrieval import method_retrieval_policy

    records = [_record(1, 1), _record(1, 2)]
    observed = []

    def callback(query_indices, gallery_indices, exclusions):
        observed.append((query_indices, gallery_indices, exclusions))
        if failure == "shape":
            return np.zeros((2, 1))
        if failure == "nan":
            return np.full((2, 2), np.nan)
        if failure == "integer":
            return np.zeros((2, 2), dtype=int)
        return np.zeros((2, 2))

    policy = method_retrieval_policy("diml", {})
    if failure == "policy":
        policy["exclusion"] = "none"
    with pytest.raises(ValueError, match="custom"):
        evaluate_retrieval(
            np.zeros((2, 2)),
            np.zeros((2, 2)),
            records,
            records,
            score_rows=callback,
            scoring_policy=policy,
        )
    if failure != "policy":
        assert observed == [([0, 1], [0, 1], [[0], [1]])]
