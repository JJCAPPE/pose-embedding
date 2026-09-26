"""The narrow selection grid preserves all published method rate ratios."""

import pytest

from pose_embed.benchmark.campaign import CANDIDATES, candidate_config
from pose_embed.benchmark.config import load_benchmark, load_methods
from pose_embed.benchmark.training import resolve_recipe


@pytest.mark.parametrize(
    "method",
    [key for key, spec in load_methods().items() if spec.status == "implemented"],
)
@pytest.mark.parametrize("candidate", CANDIDATES)
def test_candidate_scales_every_rate_and_preserves_all_other_recipe_fields(
    method, candidate
):
    base = load_benchmark("configs/benchmark.selection.v2.yaml")
    scaled = candidate_config(base, candidate)
    params = load_methods()[method].parameters
    original = resolve_recipe(method, params, base.training, 76013, 95001)
    changed = resolve_recipe(method, params, scaled.training, 76013, 95001)
    for key, value in original.items():
        if key.endswith("learning_rate"):
            assert changed[key] == value * CANDIDATES[candidate]
        elif key == "learning_rate_scale":
            assert changed[key] == CANDIDATES[candidate]
        else:
            assert changed[key] == value
    assert scaled.training.steps == base.training.steps
    assert scaled.training.seeds == base.training.seeds
    assert scaled.training.physical_batch_size == base.training.physical_batch_size


def test_grid_rejects_an_undeclared_candidate():
    with pytest.raises(ValueError, match="candidate"):
        candidate_config(load_benchmark(), "extra")
