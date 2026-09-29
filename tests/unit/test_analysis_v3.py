from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from pose_embed.evaluation.analysis import (
    leave_one_action_out_v3,
    primary_robustness_analysis_v3,
    within_action_cluster_bootstrap_v3,
)


def _id(action: int, performer: int = 1, camera: int = 1) -> str:
    return f"S001C{camera:03}P{performer:03}R001A{action:03}"


def test_v3_bootstrap_keeps_actions_fixed_and_weights_unequal_camera_counts() -> None:
    # Action 1 has three positive views in performance A and one zero in B.
    # Action 7 has one negative view in C and two zero views in D.
    ids = [_id(1, 1, c) for c in (1, 2, 3)] + [
        _id(1, 2),
        _id(7, 1),
        _id(7, 2, 1),
        _id(7, 2, 2),
    ]
    effects = [1, 1, 1, 0, -1, 0, 0]
    interval = within_action_cluster_bootstrap_v3(effects, ids)
    assert interval.estimate == pytest.approx(2 / 7)
    # Sixteen equally probable paired draws include two A/zero C (6/10)
    # and zero A/two C (-2/4). Each extreme has mass 1/16, above 2.5%.
    assert interval.lower == -0.5
    assert interval.upper == 0.6
    assert interval.replicates == 10_000
    assert interval.seed == 2026
    assert interval == within_action_cluster_bootstrap_v3(effects[::-1], ids[::-1])


def test_v3_bootstrap_matches_hand_expanded_pcg64_draws() -> None:
    ids = [_id(1, 1, 1), _id(1, 1, 2), _id(1, 2), _id(7, 1), _id(7, 2)]
    effects = [1, 1, 0, -1, 0]
    generator = np.random.Generator(np.random.PCG64(2026))
    draws = []
    for _ in range(13):
        expanded = []
        for performances in (((1, 1), (0,)), ((-1,), (0,))):
            for chosen in generator.integers(0, 2, size=2):
                expanded.extend(performances[chosen])
        draws.append(sum(expanded) / len(expanded))
    interval = within_action_cluster_bootstrap_v3(effects, ids, replicates=13)
    assert interval.lower == np.quantile(draws, 0.025, method="linear")
    assert interval.upper == np.quantile(draws, 0.975, method="linear")
    assert interval.estimate == pytest.approx(1 / 5)


def test_v3_loao_removes_queries_only_without_changing_remaining_effects() -> None:
    rows = leave_one_action_out_v3(
        [1, 1, 1, 0, -1, 0, 0],
        [_id(1, 1, c) for c in (1, 2, 3)]
        + [_id(1, 2), _id(7, 1), _id(7, 2, 1), _id(7, 2, 2)],
    )
    assert rows == [
        {"omitted_action": 1, "query_count": 3, "effect": -1 / 3},
        {"omitted_action": 7, "query_count": 4, "effect": 3 / 4},
    ]


@pytest.mark.parametrize(
    ("values", "ids"),
    [
        ([1, 0], [_id(1)]),
        ([1, 0], [_id(1), _id(1)]),
        ([float("nan")], [_id(1)]),
        ([float("inf")], [_id(1)]),
        ([], []),
        ([1], [_id(1).lower()]),
    ],
)
def test_v3_bootstrap_rejects_misaligned_nonfinite_or_noncanonical_input(values, ids):
    with pytest.raises(ValueError):
        within_action_cluster_bootstrap_v3(values, ids)


CONDITIONS = (
    "coordinate_jitter:0.01",
    "coordinate_jitter:0.025",
    "coordinate_jitter:0.05",
    "joint_mask:3",
    "joint_mask:6",
    "joint_mask:8",
    "frame_mask:10",
    "frame_mask:25",
    "frame_mask:40",
)


def _matrix():
    results = []
    for seed in (7, 17, 29):
        for method in ("contextual", "contrastive"):
            for condition in ("clean", *CONDITIONS):
                wrong_action = 1 if method == "contextual" else 7
                rows = tuple(
                    SimpleNamespace(
                        sample_id=_id(action),
                        label=action,
                        rank=2
                        if condition != "clean" and action == wrong_action
                        else 1,
                    )
                    for action in range(1, 121, 6)
                )
                results.append(
                    SimpleNamespace(
                        mode="final",
                        method=method,
                        seed=seed,
                        condition=condition,
                        query_definition="primary",
                        protocol_sha256="a" * 64,
                        gallery_sample_order_sha256="b" * 64,
                        metrics=SimpleNamespace(per_query=rows, gallery_count=20),
                    )
                )
    return results


def test_v3_full_analysis_uses_ranks_fixed_gallery_and_descriptive_tables() -> None:
    results = _matrix()
    original = deepcopy(results)
    analysis = primary_robustness_analysis_v3(
        results, seeds=(7, 17, 29), corruption_conditions=CONDITIONS
    )
    assert results == original
    assert analysis["estimate"] == 0
    assert analysis["bootstrap"]["lower"] == 0
    assert analysis["bootstrap"]["upper"] == 0
    assert analysis["claim_supported"] is False
    assert len(analysis["cells"]) == 27
    assert len(analysis["seed_effects"]) == 3
    assert len(analysis["condition_effects"]) == 9
    loao = analysis["leave_one_action_out"]
    assert len(loao["rows"]) == 20
    assert loao["rows"][0] == {
        "omitted_action": 1,
        "query_count": 19,
        "effect": -1 / 19,
    }
    assert loao["rows"][1] == {"omitted_action": 7, "query_count": 19, "effect": 1 / 19}
    assert loao["sign_changes"] == [1, 7]
    assert "original_ranks" in loao["gallery"]
    assert all(row.metrics.gallery_count == 20 for row in results)
    assert analysis["bootstrap"]["seeds_resampled"] is False
    assert analysis["bootstrap"]["actions_resampled"] is False


@pytest.mark.parametrize("mutation", ["gallery", "queries", "protocol", "duplicate"])
def test_v3_full_analysis_rejects_unpaired_or_redefined_cells(mutation: str) -> None:
    results = _matrix()
    if mutation == "gallery":
        results[-1].gallery_sample_order_sha256 = "d" * 64
    elif mutation == "queries":
        results[-1].metrics.per_query = results[-1].metrics.per_query[::-1]
    elif mutation == "protocol":
        results[-1].protocol_sha256 = "d" * 64
    else:
        results.append(results[-1])
    with pytest.raises(ValueError):
        primary_robustness_analysis_v3(
            results, seeds=(7, 17, 29), corruption_conditions=CONDITIONS
        )
