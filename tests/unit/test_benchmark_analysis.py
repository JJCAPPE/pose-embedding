from __future__ import annotations

import json
import math

import numpy as np
import pytest

from pose_embed.benchmark import analysis
from pose_embed.benchmark.config import load_benchmark


def _scores(config):
    # Unequal synchronized-view counts expose accidental equal-cluster weighting.
    samples, hits = [], []
    for action in analysis.ACTIONS:
        for performer, cameras in ((1, (1,)), (2, (1, 2, 3))):
            for camera in cameras:
                samples.append(f"S001C{camera:03}P{performer:03}R001A{action:03}")
                hits.append(performer == 2)
    scores = {
        (method, seed): list(hits)
        for method in config.final_methods
        for seed in config.training.seeds
    }
    return samples, scores


def test_plan_rejects_changed_seed_family_and_missing_policy(tmp_path, monkeypatch):
    plan = analysis.load_analysis_plan()
    assert len(plan["comparisons"]) == 24
    assert plan["bootstrap"]["replicates"] == 20_000
    path = tmp_path / "analysis.json"
    monkeypatch.setattr(analysis, "ANALYSIS_PATH", path)
    for key in ("seeds", "comparisons", "bootstrap"):
        altered = dict(plan)
        altered.pop(key)
        path.write_text(json.dumps(altered))
        with pytest.raises(ValueError, match="statistical design"):
            analysis.load_analysis_plan()
    path.write_text(json.dumps(plan))
    config = load_benchmark()
    changed = config.model_copy(
        update={
            "training": config.training.model_copy(update={"seeds": (1, 2, 3, 4, 5, 6)})
        }
    )
    with pytest.raises(ValueError, match="seeds or method family"):
        analysis.load_analysis_plan(changed)


def test_common_resamples_cancel_identical_methods_and_preserve_query_weights():
    config = load_benchmark()
    samples, scores = _scores(config)
    # A focal method that always hits has an observed advantage of .25, not .5:
    # original query weights include three synchronized views of the good cluster.
    for seed in config.training.seeds:
        scores[("contextual", seed)] = [1] * len(samples)
    report = analysis.paired_intervals(scores, samples, config)
    main = report["comparisons"][0]
    assert main["comparator"] == "contrastive"
    assert main["mean_difference"] == 0.25
    # With 40 sampled clusters and equal chance of each performance, the number
    # of poor clusters is Binomial(40, .5); the retained view weights yield B /
    # (120 - 2B). This independent reference would expose per-view resampling.
    cdf = np.cumsum([math.comb(40, b) / 2**40 for b in range(41)])
    exact = [int(np.searchsorted(cdf, q)) for q in (0.025, 0.975)]
    expected_ci = [b / (120 - 2 * b) for b in exact]
    assert main["raw_ci95"] == pytest.approx(expected_ci, abs=0.02)
    assert main["simultaneous_ci95"][0] <= main["raw_ci95"][0]
    assert main["simultaneous_ci95"][1] >= main["raw_ci95"][1]
    matched = report["comparisons"][-1]
    assert matched["raw_ci95"] == matched["simultaneous_ci95"] == [0.0, 0.0]
    assert matched["supports_positive_difference"] is False
    assert report["performance_cluster_count"] == 40
    assert report == analysis.paired_intervals(scores, samples, config)


def test_seed_resampling_is_paired_and_each_fixed_action_is_retained():
    config = load_benchmark()
    samples, scores = _scores(config)
    for seed_index, seed in enumerate(config.training.seeds):
        for method in config.final_methods:
            scores[(method, seed)] = [seed_index % 2] * len(samples)
    report = analysis.paired_intervals(scores, samples, config)
    assert all(row["simultaneous_ci95"] == [0.0, 0.0] for row in report["comparisons"])
    shorter = samples[4:]
    with pytest.raises(ValueError, match="twenty fixed"):
        analysis.paired_intervals(
            {key: value[4:] for key, value in scores.items()}, shorter, config
        )


def test_invalid_hit_vectors_cannot_enter_bootstrap():
    config = load_benchmark()
    samples, scores = _scores(config)
    for value in (0.5, np.nan):
        scores[("contextual", config.training.seeds[0])][0] = value
        with pytest.raises(ValueError, match="binary hits"):
            analysis.paired_intervals(scores, samples, config)
