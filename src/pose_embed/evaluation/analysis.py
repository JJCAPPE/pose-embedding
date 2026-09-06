"""Paired cluster bootstrap for the preregistered degradation estimand."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.evaluation.result import EvaluationResult

PRIMARY_BOOTSTRAP_SEED = 2026


@dataclass(frozen=True)
class BootstrapInterval:
    estimate: float
    lower: float
    upper: float
    confidence_level: float
    replicates: int
    seed: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "estimate": self.estimate,
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
            "replicates": self.replicates,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class PrimaryCellEffect:
    seed: int
    condition: str
    contextual_clean_top1: float
    contextual_corrupted_top1: float
    contextual_drop: float
    contrastive_clean_top1: float
    contrastive_corrupted_top1: float
    contrastive_drop: float
    effect: float

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "seed": self.seed,
            "condition": self.condition,
            "contextual_clean_top1": self.contextual_clean_top1,
            "contextual_corrupted_top1": self.contextual_corrupted_top1,
            "contextual_drop": self.contextual_drop,
            "contrastive_clean_top1": self.contrastive_clean_top1,
            "contrastive_corrupted_top1": self.contrastive_corrupted_top1,
            "contrastive_drop": self.contrastive_drop,
            "effect": self.effect,
        }


@dataclass(frozen=True)
class PrimaryAnalysis:
    estimate: float
    interval: BootstrapInterval
    cells: tuple[PrimaryCellEffect, ...]
    seeds: tuple[int, ...]
    corruption_conditions: tuple[str, ...]
    query_count_per_cell: int
    paired_query_observations: int
    performance_clusters: int
    synchronized_camera_clusters: int

    @property
    def claim_supported(self) -> bool:
        return self.interval.upper < 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "analysis": "primary_robustness",
            "estimand": "mean(contextual_drop - contrastive_drop)",
            "query_definition": "primary",
            "metric": "top1",
            "methods": ["contextual", "contrastive"],
            "seeds": list(self.seeds),
            "corruption_conditions": list(self.corruption_conditions),
            "cell_count": len(self.cells),
            "cell_weighting": "equal",
            "query_count_per_cell": self.query_count_per_cell,
            "paired_query_observations": self.paired_query_observations,
            "bootstrap": {
                "method": "paired_percentile_cluster_bootstrap",
                "observation": "paired_query_top1_correctness",
                "cluster_fields": ["setup", "performer", "repetition", "action"],
                "performance_clusters": self.performance_clusters,
                "synchronized_camera_clusters": self.synchronized_camera_clusters,
                **self.interval.as_dict(),
            },
            "estimate": self.estimate,
            "effect_direction": "negative_means_contextual_degraded_less",
            "support_rule": "upper_confidence_bound_below_zero",
            "claim_supported": self.claim_supported,
            "claim_caveat": (
                "less_degradation_is_not_higher_overall_retrieval_when_clean_"
                "accuracy_differs"
            ),
            "cells": [cell.as_dict() for cell in self.cells],
        }


def paired_cluster_bootstrap(
    paired_effects: Sequence[float] | np.ndarray,
    cluster_ids: Sequence[Hashable],
    *,
    replicates: int = 10_000,
    confidence_level: float = 0.95,
    seed: int = 2026,
) -> BootstrapInterval:
    """Bootstrap paired effects while keeping every cluster intact."""
    values = np.asarray(paired_effects, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("paired_effects must be a non-empty vector")
    if len(cluster_ids) != values.size:
        raise ValueError("cluster_ids must align with paired_effects")
    if not np.isfinite(values).all():
        raise ValueError("paired_effects must be finite")
    if replicates < 1:
        raise ValueError("replicates must be positive")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")

    grouped: dict[Hashable, list[int]] = defaultdict(list)
    for index, cluster in enumerate(cluster_ids):
        grouped[cluster].append(index)
    clusters = tuple(grouped)
    if not clusters:
        raise ValueError("at least one cluster is required")
    cluster_sums = np.asarray(
        [values[grouped[cluster]].sum() for cluster in clusters], dtype=np.float64
    )
    cluster_counts = np.asarray(
        [len(grouped[cluster]) for cluster in clusters], dtype=np.int64
    )
    rng = np.random.default_rng(seed)
    bootstrap_means = np.empty(replicates, dtype=np.float64)
    # Chunking bounds memory while avoiding expansion back to every repeated
    # seed/cell/query observation inside each bootstrap replicate.
    chunk_size = max(1, min(256, 1_000_000 // len(clusters)))
    for start in range(0, replicates, chunk_size):
        stop = min(start + chunk_size, replicates)
        sampled = rng.integers(
            0,
            len(clusters),
            size=(stop - start, len(clusters)),
        )
        bootstrap_means[start:stop] = cluster_sums[sampled].sum(
            axis=1
        ) / cluster_counts[sampled].sum(axis=1)
    tail = (1.0 - confidence_level) / 2.0
    lower, upper = np.quantile(bootstrap_means, [tail, 1.0 - tail])
    return BootstrapInterval(
        estimate=float(values.mean()),
        lower=float(lower),
        upper=float(upper),
        confidence_level=confidence_level,
        replicates=replicates,
        seed=seed,
    )


def degradation_effects(
    contextual_clean: Sequence[float] | np.ndarray,
    contextual_corrupted: Sequence[float] | np.ndarray,
    contrastive_clean: Sequence[float] | np.ndarray,
    contrastive_corrupted: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return paired `(contextual drop) - (contrastive drop)` observations."""
    arrays = [
        np.asarray(values, dtype=np.float64)
        for values in (
            contextual_clean,
            contextual_corrupted,
            contrastive_clean,
            contrastive_corrupted,
        )
    ]
    if any(array.shape != arrays[0].shape for array in arrays[1:]):
        raise ValueError("all paired outcome arrays must have identical shapes")
    return (arrays[0] - arrays[1]) - (arrays[2] - arrays[3])


def primary_robustness_analysis(
    results: Sequence[EvaluationResult],
    *,
    seeds: Sequence[int],
    corruption_conditions: Sequence[str],
    bootstrap_replicates: int,
    confidence_level: float,
    bootstrap_seed: int = PRIMARY_BOOTSTRAP_SEED,
) -> PrimaryAnalysis:
    """Compute the locked primary effect from paired primary-query rows."""
    paired_seeds = tuple(seeds)
    conditions = tuple(corruption_conditions)
    if len(paired_seeds) != 3 or len(set(paired_seeds)) != 3:
        raise ValueError("primary analysis requires exactly three paired seeds")
    if len(conditions) != 9 or len(set(conditions)) != 9 or "clean" in conditions:
        raise ValueError("primary analysis requires exactly nine corruption cells")

    relevant = [
        result
        for result in results
        if result.query_definition == "primary"
        and result.method in {"contextual", "contrastive"}
    ]
    index: dict[tuple[str, int, str], EvaluationResult] = {}
    for result in relevant:
        if result.mode != "final":
            raise ValueError("primary analysis accepts only locked core-final rows")
        key = (result.method, result.seed, result.condition)
        if key in index:
            raise ValueError(f"duplicate primary analysis cell: {key}")
        index[key] = result

    expected_keys = {
        (method, seed, condition)
        for method in ("contextual", "contrastive")
        for seed in paired_seeds
        for condition in ("clean", *conditions)
    }
    if set(index) != expected_keys:
        missing = sorted(expected_keys - set(index))
        unexpected = sorted(set(index) - expected_keys)
        raise ValueError(
            "primary analysis matrix is not exact: "
            f"missing={missing}, unexpected={unexpected}"
        )

    cells: list[PrimaryCellEffect] = []
    paired_effects: list[float] = []
    cluster_ids: list[tuple[int, int, int, int]] = []
    query_count: int | None = None
    samples_by_cluster: dict[tuple[int, int, int, int], set[str]] = defaultdict(set)

    for seed in paired_seeds:
        contextual_clean = index[("contextual", seed, "clean")]
        contrastive_clean = index[("contrastive", seed, "clean")]
        for condition in conditions:
            contextual_corrupted = index[("contextual", seed, condition)]
            contrastive_corrupted = index[("contrastive", seed, condition)]
            paired = (
                contextual_clean,
                contextual_corrupted,
                contrastive_clean,
                contrastive_corrupted,
            )
            row_identities = [
                tuple((row.sample_id, row.label) for row in result.metrics.per_query)
                for result in paired
            ]
            if any(identity != row_identities[0] for identity in row_identities[1:]):
                raise ValueError(
                    "primary analysis requires identical paired query identities"
                )
            current_count = len(row_identities[0])
            if query_count is None:
                query_count = current_count
            elif current_count != query_count:
                raise ValueError("primary analysis query count changes across cells")

            cell_effect_values = degradation_effects(
                [row.top1_correct for row in contextual_clean.metrics.per_query],
                [row.top1_correct for row in contextual_corrupted.metrics.per_query],
                [row.top1_correct for row in contrastive_clean.metrics.per_query],
                [row.top1_correct for row in contrastive_corrupted.metrics.per_query],
            )
            paired_effects.extend(cell_effect_values.tolist())
            for sample_id, _ in row_identities[0]:
                cluster = parse_ntu_sample_id(sample_id).performance_id
                cluster_ids.append(cluster)
                samples_by_cluster[cluster].add(sample_id)

            contextual_drop = (
                contextual_clean.metrics.top1 - contextual_corrupted.metrics.top1
            )
            contrastive_drop = (
                contrastive_clean.metrics.top1 - contrastive_corrupted.metrics.top1
            )
            cells.append(
                PrimaryCellEffect(
                    seed=seed,
                    condition=condition,
                    contextual_clean_top1=contextual_clean.metrics.top1,
                    contextual_corrupted_top1=contextual_corrupted.metrics.top1,
                    contextual_drop=contextual_drop,
                    contrastive_clean_top1=contrastive_clean.metrics.top1,
                    contrastive_corrupted_top1=(contrastive_corrupted.metrics.top1),
                    contrastive_drop=contrastive_drop,
                    effect=contextual_drop - contrastive_drop,
                )
            )

    assert query_count is not None
    estimate = math.fsum(cell.effect for cell in cells) / len(cells)
    interval = paired_cluster_bootstrap(
        paired_effects,
        cluster_ids,
        replicates=bootstrap_replicates,
        confidence_level=confidence_level,
        seed=bootstrap_seed,
    )
    if not math.isclose(estimate, interval.estimate, rel_tol=0, abs_tol=1e-12):
        raise ValueError("cell-weighted and paired-query primary estimates differ")
    synchronized_clusters = sum(
        len(sample_ids) > 1 for sample_ids in samples_by_cluster.values()
    )
    return PrimaryAnalysis(
        estimate=estimate,
        interval=interval,
        cells=tuple(cells),
        seeds=paired_seeds,
        corruption_conditions=conditions,
        query_count_per_cell=query_count,
        paired_query_observations=len(paired_effects),
        performance_clusters=len(samples_by_cluster),
        synchronized_camera_clusters=synchronized_clusters,
    )


def complete_core_curve_data(
    results: Sequence[EvaluationResult],
    *,
    methods: Sequence[str],
    seeds: Sequence[int],
    conditions: Sequence[str],
    query_definitions: Sequence[str],
    metrics: Sequence[str],
) -> dict[str, Any]:
    """Summarize every locked core curve without selecting cells or seeds."""
    ordered_methods = tuple(methods)
    ordered_seeds = tuple(seeds)
    ordered_conditions = tuple(conditions)
    ordered_queries = tuple(query_definitions)
    ordered_metrics = tuple(metrics)
    if (
        len(ordered_methods) != 3
        or len(ordered_seeds) != 3
        or len(ordered_conditions) != 10
        or ordered_conditions[0] != "clean"
        or len(ordered_queries) != 2
        or ordered_metrics != ("top1", "mrr", "r_at_5")
    ):
        raise ValueError("curve data requires the complete locked core design")
    index: dict[tuple[str, int, str, str], EvaluationResult] = {}
    for result in results:
        key = (
            result.method,
            result.seed,
            result.condition,
            result.query_definition,
        )
        if key in index:
            raise ValueError(f"duplicate core curve cell: {key}")
        index[key] = result
    expected = {
        (method, seed, condition, query_definition)
        for method in ordered_methods
        for seed in ordered_seeds
        for condition in ordered_conditions
        for query_definition in ordered_queries
    }
    if set(index) != expected:
        raise ValueError("curve data requires the exact locked core matrix")

    families = (
        ("coordinate_jitter", (ordered_conditions[0], *ordered_conditions[1:4])),
        ("joint_mask", (ordered_conditions[0], *ordered_conditions[4:7])),
        ("frame_mask", (ordered_conditions[0], *ordered_conditions[7:10])),
    )
    curves: list[dict[str, Any]] = []
    for query_definition in ordered_queries:
        for metric in ordered_metrics:
            for family, family_conditions in families:
                series = []
                for method in ordered_methods:
                    points = []
                    for condition in family_conditions:
                        seed_values = [
                            {
                                "seed": seed,
                                "value": getattr(
                                    index[
                                        (method, seed, condition, query_definition)
                                    ].metrics,
                                    metric,
                                ),
                            }
                            for seed in ordered_seeds
                        ]
                        values = [item["value"] for item in seed_values]
                        points.append(
                            {
                                "condition": condition,
                                "severity": (
                                    "clean"
                                    if condition == "clean"
                                    else condition.split(":", maxsplit=1)[1]
                                ),
                                "seed_values": seed_values,
                                "mean": math.fsum(values) / len(values),
                                "minimum": min(values),
                                "maximum": max(values),
                            }
                        )
                    series.append({"method": method, "points": points})
                curves.append(
                    {
                        "query_definition": query_definition,
                        "metric": metric,
                        "corruption_family": family,
                        "series": series,
                    }
                )
    return {
        "schema_version": 1,
        "artifact": "complete_core_metric_curves",
        "selection": "all_locked_core_cells_no_selection",
        "aggregation": "arithmetic_mean_across_three_paired_seeds",
        "methods": list(ordered_methods),
        "seeds": list(ordered_seeds),
        "conditions": list(ordered_conditions),
        "query_definitions": list(ordered_queries),
        "metrics": list(ordered_metrics),
        "curves": curves,
    }


def complete_core_error_data(
    results: Sequence[EvaluationResult],
    *,
    methods: Sequence[str],
    seeds: Sequence[int],
    conditions: Sequence[str],
    query_definitions: Sequence[str],
    actions: Sequence[int],
) -> dict[str, Any]:
    """Report class errors and one outcome-independent example per matrix cell."""
    ordered_methods = tuple(methods)
    ordered_seeds = tuple(seeds)
    ordered_conditions = tuple(conditions)
    ordered_queries = tuple(query_definitions)
    ordered_actions = tuple(actions)
    index = {
        (result.method, result.seed, result.condition, result.query_definition): result
        for result in results
    }
    expected = {
        (method, seed, condition, query_definition)
        for method in ordered_methods
        for seed in ordered_seeds
        for condition in ordered_conditions
        for query_definition in ordered_queries
    }
    if len(index) != len(results) or set(index) != expected:
        raise ValueError("error analysis requires the exact locked core matrix")

    per_class: list[dict[str, Any]] = []
    representative_errors: list[dict[str, Any]] = []
    for method in ordered_methods:
        for seed in ordered_seeds:
            for condition in ordered_conditions:
                for query_definition in ordered_queries:
                    result = index[(method, seed, condition, query_definition)]
                    by_action: dict[int, list[Any]] = defaultdict(list)
                    errors = []
                    for row in result.metrics.per_query:
                        action = parse_ntu_sample_id(row.sample_id).action
                        if row.label != action:
                            raise ValueError(
                                "per-query label differs from its NTU action identity"
                            )
                        by_action[action].append(row)
                        if not row.top1_correct:
                            errors.append(row)
                    if set(by_action) != set(ordered_actions):
                        raise ValueError(
                            "each core result must cover every locked novel action"
                        )
                    for action in ordered_actions:
                        action_rows = by_action[action]
                        action_errors = [
                            row for row in action_rows if not row.top1_correct
                        ]
                        prediction_counts: dict[int, int] = defaultdict(int)
                        for row in action_errors:
                            prediction_counts[row.predicted_label] += 1
                        count = len(action_rows)
                        per_class.append(
                            {
                                "method": method,
                                "seed": seed,
                                "condition": condition,
                                "query_definition": query_definition,
                                "action": action,
                                "query_count": count,
                                "top1_error_count": len(action_errors),
                                "top1_error_rate": len(action_errors) / count,
                                "mean_rank": math.fsum(row.rank for row in action_rows)
                                / count,
                                "mrr": math.fsum(1.0 / row.rank for row in action_rows)
                                / count,
                                "r_at_5": sum(row.rank <= 5 for row in action_rows)
                                / count,
                                "error_prediction_counts": [
                                    {
                                        "predicted_action": predicted_action,
                                        "count": prediction_counts[predicted_action],
                                    }
                                    for predicted_action in sorted(prediction_counts)
                                ],
                            }
                        )
                    first_error = min(
                        errors, key=lambda row: row.sample_id, default=None
                    )
                    representative_errors.append(
                        {
                            "method": method,
                            "seed": seed,
                            "condition": condition,
                            "query_definition": query_definition,
                            "top1_error_count": len(errors),
                            "example": (
                                None
                                if first_error is None
                                else {
                                    "selection_rule": (
                                        "lexicographically_first_sample_id_among_"
                                        "top1_errors"
                                    ),
                                    "sample_id": first_error.sample_id,
                                    "true_action": first_error.label,
                                    "predicted_action": first_error.predicted_label,
                                    "rank": first_error.rank,
                                }
                            ),
                        }
                    )
    return {
        "schema_version": 1,
        "artifact": "complete_core_error_analysis",
        "selection": "all_locked_core_cells_and_actions_no_selection",
        "representative_example_rule": (
            "lexicographically_first_sample_id_among_top1_errors_per_matrix_cell"
        ),
        "methods": list(ordered_methods),
        "seeds": list(ordered_seeds),
        "conditions": list(ordered_conditions),
        "query_definitions": list(ordered_queries),
        "actions": list(ordered_actions),
        "per_class": per_class,
        "representative_errors": representative_errors,
    }
