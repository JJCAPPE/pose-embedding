"""Preregistered paired seed/performance bootstrap for the fixed v2 family."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from pose_embed.benchmark.config import METHOD_IDS
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.provenance import sha256_file

ANALYSIS_PATH = (
    Path(__file__).resolve().parents[3] / "configs/benchmark-analysis.v2.json"
)
SEEDS = [7, 17, 29, 43, 59, 71]
ACTIONS = list(range(1, 120, 6))


def load_analysis_plan(config=None) -> dict:
    """Reject incomplete or unsupported statistics before selection can be locked."""
    plan = json.loads(ANALYSIS_PATH.read_text())
    comparisons = [
        {"focal": "contextual", "comparator": method, "embedding_dimension": 512}
        for method in METHOD_IDS
        if method not in {"contextual", "contextual_1536", "proxy_anchor_avsl"}
    ] + [
        {
            "focal": "contextual_1536",
            "comparator": "proxy_anchor_avsl",
            "embedding_dimension": 1536,
        }
    ]
    expected = {
        "schema_version": 1,
        "protocol_id": "motion-retrieval-v2",
        "status": "specified",
        "primary_metric": "r_at_1",
        "primary_comparison": {"focal": "contextual", "comparator": "contrastive"},
        "novel_actions": ACTIONS,
        "seeds": SEEDS,
        "aggregation": "unweighted_mean_over_queries_then_equal_mean_over_seeds",
        "bootstrap": {
            "replicates": 20_000,
            "random_seed": 20260924,
            "seed_sampling": "six_paired_training_seeds_with_replacement",
            "query_sampling": (
                "performance_clusters_with_replacement_within_each_fixed_action"
            ),
            "cluster_fields": ["setup", "performer", "repetition", "action"],
            "synchronized_views": "retained_together_with_original_query_weights",
            "shared_resamples": "all_methods_seeds_and_dimension_groups",
            "class_sampling": "none_fixed_twenty_actions",
            "gallery_sampling": "none_fixed_eligible_gallery",
            "query_denominator": "number_of_queries_in_sampled_clusters",
            "quantile_method": "linear",
        },
        "confidence": 0.95,
        "multiplicity": {
            "method": "bonferroni",
            "family_size": 24,
            "claim_rule": (
                "simultaneous_interval_lower_bound_strictly_greater_than_zero"
            ),
            "raw_intervals": "descriptive_only",
        },
        "comparisons": comparisons,
        "secondary_metrics": (
            "means_sample_standard_deviation_and_each_seed_no_confirmatory_claims"
        ),
    }
    if plan != expected:
        raise ValueError(
            "analysis plan is missing or differs from the implemented "
            "statistical design"
        )
    if config is not None and (
        list(config.training.seeds) != SEEDS
        or set(config.final_methods) != set(METHOD_IDS)
    ):
        raise ValueError(
            "analysis plan seeds or method family differ from the benchmark"
        )
    return plan


def analysis_plan_sha256() -> str:
    load_analysis_plan()
    return sha256_file(ANALYSIS_PATH)


def paired_intervals(scores: dict, sample_ids: list[str], config) -> dict:
    """Bootstrap primary R@1, pairing both seeds and performance clusters.

    The held-out actions and eligible gallery are fixed. Within each action,
    sample its original number of underlying performances with replacement and
    retain every synchronized query view with its original weight. Common
    resampling counts are used for every method and both dimension groups.
    Chunked matrix products avoid a replicates-by-all-queries allocation.
    """
    plan = load_analysis_plan(config)
    methods = list(config.final_methods)
    seeds = list(config.training.seeds)
    keys = [(method, seed) for method in methods for seed in seeds]
    if (
        set(scores) != set(keys)
        or not sample_ids
        or len(set(sample_ids)) != len(sample_ids)
    ):
        raise ValueError(
            "paired analysis requires the complete matrix and unique query IDs"
        )
    identities = [parse_ntu_sample_id(value) for value in sample_ids]
    if {row.action for row in identities} != set(plan["novel_actions"]):
        raise ValueError("analysis must contain all twenty fixed novel actions")
    vectors = np.asarray([scores[key] for key in keys], dtype=np.float64)
    if (
        vectors.shape != (len(keys), len(sample_ids))
        or not np.isfinite(vectors).all()
        or not np.isin(vectors, [0, 1]).all()
    ):
        raise ValueError("primary per-query R@1 values must be aligned binary hits")
    clusters = {}
    class_clusters = defaultdict(list)
    query_clusters = []
    for row in identities:
        if row.performance_id not in clusters:
            index = len(clusters)
            clusters[row.performance_id] = index
            class_clusters[row.action].append(index)
        query_clusters.append(clusters[row.performance_id])
    if any(len(values) < 2 for values in class_clusters.values()):
        raise ValueError("each action needs at least two performance clusters")
    cluster_sizes = np.bincount(query_clusters).astype(np.float64)
    cluster_sums = np.zeros((len(clusters), len(keys)), dtype=np.float64)
    np.add.at(cluster_sums, query_clusters, vectors.T)
    settings = plan["bootstrap"]
    rng = np.random.default_rng(settings["random_seed"])
    replicates = settings["replicates"]
    sampled = np.empty((replicates, len(methods)), dtype=np.float64)
    # The fixed chunk size is part of the code hash and deterministic RNG sequence.
    for start in range(0, replicates, 128):
        count = min(128, replicates - start)
        seed_counts = rng.multinomial(
            len(seeds), [1 / len(seeds)] * len(seeds), size=count
        )
        weights = np.zeros((count, len(clusters)), dtype=np.float64)
        for action in sorted(class_clusters):
            indexes = class_clusters[action]
            weights[:, indexes] = rng.multinomial(
                len(indexes), [1 / len(indexes)] * len(indexes), size=count
            )
        numerators = (weights @ cluster_sums).reshape(count, len(methods), len(seeds))
        sampled[start : start + count] = (
            (numerators * seed_counts[:, None, :]).sum(axis=2)
            / len(seeds)
            / (weights @ cluster_sizes)[:, None]
        )
    means = vectors.mean(axis=1).reshape(len(methods), len(seeds)).mean(axis=1)
    alpha = 1 - plan["confidence"]
    family = plan["multiplicity"]["family_size"]
    comparisons = []
    for comparison in plan["comparisons"]:
        left = methods.index(comparison["focal"])
        right = methods.index(comparison["comparator"])
        delta = sampled[:, left] - sampled[:, right]
        raw = np.quantile(delta, [alpha / 2, 1 - alpha / 2], method="linear")
        adjusted = np.quantile(
            delta, [alpha / (2 * family), 1 - alpha / (2 * family)], method="linear"
        )
        comparisons.append(
            comparison
            | {
                "mean_difference": float(means[left] - means[right]),
                "raw_ci95": raw.tolist(),
                "simultaneous_ci95": adjusted.tolist(),
                "supports_positive_difference": bool(adjusted[0] > 0),
            }
        )
    return {
        "analysis_plan_sha256": analysis_plan_sha256(),
        "primary_metric": plan["primary_metric"],
        "confidence": plan["confidence"],
        "bootstrap": settings,
        "multiplicity": plan["multiplicity"],
        "query_count": len(sample_ids),
        "performance_cluster_count": len(clusters),
        "comparisons": comparisons,
        "scope": (
            "Uncertainty over training seeds and query performances, conditional on "
            "the fixed twenty actions and eligible gallery. Bootstrap intervals "
            "are approximate."
        ),
    }
