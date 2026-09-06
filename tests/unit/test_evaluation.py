from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from pose_embed.evaluation.analysis import (
    PRIMARY_BOOTSTRAP_SEED,
    complete_core_curve_data,
    complete_core_error_data,
    degradation_effects,
    paired_cluster_bootstrap,
    primary_robustness_analysis,
)
from pose_embed.evaluation.metrics import evaluate_one_shot


def test_one_shot_metrics_match_hand_calculated_ranks() -> None:
    gallery = torch.eye(3)
    gallery_labels = torch.tensor([10, 20, 30])
    queries = torch.tensor([[1.0, 0.0, 0.0], [0.2, 1.0, 0.0], [0.0, 0.5, 1.0]])
    query_labels = torch.tensor([10, 10, 20])

    result = evaluate_one_shot(gallery, gallery_labels, queries, query_labels)

    assert result.top1 == pytest.approx(1 / 3)
    assert result.mrr == pytest.approx(2 / 3)
    assert result.r_at_5 == 1.0
    assert [row.rank for row in result.per_query] == [1, 2, 2]


def test_one_shot_rejects_more_than_one_gallery_example_per_class() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        evaluate_one_shot(
            torch.eye(2),
            torch.tensor([1, 1]),
            torch.eye(2),
            torch.tensor([1, 1]),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_one_shot_rejects_nonfinite_embeddings(value: float) -> None:
    gallery = torch.eye(2)
    queries = torch.eye(2)
    queries[0, 0] = value

    with pytest.raises(ValueError, match="finite"):
        evaluate_one_shot(
            gallery,
            torch.tensor([1, 2]),
            queries,
            torch.tensor([1, 2]),
        )


def test_paired_cluster_bootstrap_uses_registered_effect_direction() -> None:
    effects = degradation_effects(
        contextual_clean=[1, 1, 1, 1],
        contextual_corrupted=[0.9, 0.8, 0.9, 0.8],
        contrastive_clean=[1, 1, 1, 1],
        contrastive_corrupted=[0.7, 0.6, 0.7, 0.6],
    )
    interval = paired_cluster_bootstrap(
        effects,
        cluster_ids=["a", "a", "b", "b"],
        replicates=200,
        seed=5,
    )

    np.testing.assert_allclose(effects, [-0.2, -0.2, -0.2, -0.2])
    assert interval.estimate == pytest.approx(-0.2)
    assert interval.upper < 0


def test_primary_analysis_pairs_all_cells_and_clusters_synchronized_cameras() -> None:
    sample_ids = (
        "S001C001P001R001A001",
        "S001C002P001R001A001",
        "S002C001P002R001A007",
    )
    seeds = (7, 17, 29)
    conditions = tuple(f"corruption:{index}" for index in range(1, 10))

    def result(
        method: str,
        seed: int,
        condition: str,
        correctness: tuple[bool, ...],
    ) -> SimpleNamespace:
        rows = tuple(
            SimpleNamespace(
                sample_id=sample_id, label=int(sample_id[-3:]), top1_correct=value
            )
            for sample_id, value in zip(sample_ids, correctness, strict=True)
        )
        return SimpleNamespace(
            mode="final",
            method=method,
            seed=seed,
            condition=condition,
            query_definition="primary",
            metrics=SimpleNamespace(
                top1=sum(correctness) / len(correctness),
                per_query=rows,
            ),
        )

    results = []
    for seed in seeds:
        for method in ("contextual", "contrastive"):
            results.append(result(method, seed, "clean", (True, True, True)))
            corrupted = (
                (True, True, True) if method == "contextual" else (False, False, False)
            )
            results.extend(
                result(method, seed, condition, corrupted) for condition in conditions
            )

    first = primary_robustness_analysis(
        results,
        seeds=seeds,
        corruption_conditions=conditions,
        bootstrap_replicates=10_000,
        confidence_level=0.95,
    )
    second = primary_robustness_analysis(
        results,
        seeds=seeds,
        corruption_conditions=conditions,
        bootstrap_replicates=10_000,
        confidence_level=0.95,
    )

    assert first == second
    assert first.estimate == -1.0
    assert first.interval.lower == -1.0
    assert first.interval.upper == -1.0
    assert first.interval.replicates == 10_000
    assert first.interval.seed == PRIMARY_BOOTSTRAP_SEED
    assert first.claim_supported is True
    assert len(first.cells) == 27
    assert first.paired_query_observations == 81
    assert first.performance_clusters == 2
    assert first.synchronized_camera_clusters == 1


def test_complete_core_curves_and_class_errors_include_every_locked_cell() -> None:
    methods = ("contrastive", "supcon", "contextual")
    seeds = (7, 17, 29)
    conditions = ("clean", *(f"corruption:{index}" for index in range(1, 10)))
    query_definitions = ("primary", "official")
    query_rows = (
        SimpleNamespace(
            sample_id="S001C001P001R001A001",
            label=1,
            rank=1,
            predicted_label=1,
            top1_correct=True,
        ),
        SimpleNamespace(
            sample_id="S002C001P002R001A007",
            label=7,
            rank=2,
            predicted_label=1,
            top1_correct=False,
        ),
    )
    results = [
        SimpleNamespace(
            method=method,
            seed=seed,
            condition=condition,
            query_definition=query_definition,
            metrics=SimpleNamespace(
                top1=0.5,
                mrr=0.75,
                r_at_5=1.0,
                per_query=query_rows,
            ),
        )
        for method in methods
        for seed in seeds
        for condition in conditions
        for query_definition in query_definitions
    ]

    curves = complete_core_curve_data(
        list(reversed(results)),
        methods=methods,
        seeds=seeds,
        conditions=conditions,
        query_definitions=query_definitions,
        metrics=("top1", "mrr", "r_at_5"),
    )
    errors = complete_core_error_data(
        list(reversed(results)),
        methods=methods,
        seeds=seeds,
        conditions=conditions,
        query_definitions=query_definitions,
        actions=(1, 7),
    )

    assert len(curves["curves"]) == 18
    assert all(len(curve["series"]) == 3 for curve in curves["curves"])
    assert all(
        len(series["points"]) == 4
        and all(len(point["seed_values"]) == 3 for point in series["points"])
        for curve in curves["curves"]
        for series in curve["series"]
    )
    assert len(errors["per_class"]) == 180 * 2
    assert len(errors["representative_errors"]) == 180
    assert all(
        row["example"]["sample_id"] == "S002C001P002R001A007"
        for row in errors["representative_errors"]
    )
    assert errors == complete_core_error_data(
        results,
        methods=methods,
        seeds=seeds,
        conditions=conditions,
        query_definitions=query_definitions,
        actions=(1, 7),
    )
