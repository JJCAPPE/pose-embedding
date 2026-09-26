from __future__ import annotations

import importlib.util
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.models import ActionHeadEmbed, FrozenEncoderAdapter
from pose_embed.training import BalancedBatchSampler


def test_action_head_matches_locked_pooling_equation() -> None:
    candidate = ActionHeadEmbed(
        representation_dimension=2, joints=17, embedding_dimension=3
    )
    with torch.no_grad():
        candidate.projection.weight.copy_(
            torch.arange(3 * 34, dtype=torch.float32).reshape(3, 34) / 100
        )
        candidate.projection.bias.copy_(torch.tensor([-0.2, 0.1, 0.3]))
    features = torch.arange(2 * 2 * 3 * 17 * 2, dtype=torch.float32).reshape(
        2, 2, 3, 17, 2
    )
    pooled = features.permute(0, 1, 3, 4, 2).mean(dim=-1)
    pooled = pooled.reshape(2, 2, 34).mean(dim=1)
    expected = functional.normalize(candidate.projection(pooled), dim=-1)

    torch.testing.assert_close(candidate(features), expected)


@pytest.mark.parametrize("dropout", [0.0, 0.4])
@pytest.mark.parametrize("training", [False, True])
def test_raw_projection_extension_preserves_original_pilot_forward(
    dropout: float, training: bool
) -> None:
    """Certify the sole input-code difference from archival release 0ef8583."""
    candidate = ActionHeadEmbed(
        dropout_ratio=dropout,
        representation_dimension=4,
        joints=17,
        embedding_dimension=8,
    ).train(training)
    reference = deepcopy(candidate)
    features = torch.randn(3, 2, 7, 17, 4, requires_grad=True)
    reference_features = features.detach().clone().requires_grad_(True)
    weights = torch.randn(3, 8)
    rng = torch.get_rng_state()
    actual = candidate(features)
    (actual * weights).sum().backward()
    after = torch.get_rng_state()

    torch.set_rng_state(rng)
    dropped = reference.dropout(reference_features)
    pooled = dropped.permute(0, 1, 3, 4, 2).mean(dim=-1)
    pooled = pooled.reshape(3, 2, -1).mean(dim=1)
    expected = functional.normalize(reference.projection(pooled), dim=-1)
    (expected * weights).sum().backward()

    assert torch.equal(actual, expected)
    assert torch.equal(features.grad, reference_features.grad)
    assert torch.equal(after, torch.get_rng_state())
    for actual_parameter, expected_parameter in zip(
        candidate.parameters(), reference.parameters(), strict=True
    ):
        assert torch.equal(actual_parameter.grad, expected_parameter.grad)


def test_action_head_optionally_matches_fetched_motionbert_checkout(
    repository_root: Path,
) -> None:
    path = repository_root / ".cache/upstreams/MotionBERT/lib/model/model_action.py"
    if not path.is_file():
        pytest.skip("run scripts/fetch_upstreams.py before upstream parity testing")
    spec = importlib.util.spec_from_file_location("motionbert_action", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference = module.ActionHeadEmbed(dim_rep=4, num_joints=17, hidden_dim=6)
    candidate = ActionHeadEmbed(
        representation_dimension=4, joints=17, embedding_dimension=6
    )
    candidate.projection.load_state_dict(reference.fc1.state_dict())
    features = torch.randn(2, 2, 3, 17, 4)

    torch.testing.assert_close(candidate(features), reference(features))


def test_frozen_adapter_keeps_encoder_in_eval_mode() -> None:
    class Encoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.linear = nn.Linear(3, 4)

        def get_representation(self, poses: torch.Tensor) -> torch.Tensor:
            return self.linear(poses)

    encoder = Encoder()
    adapter = FrozenEncoderAdapter(
        encoder,
        ActionHeadEmbed(representation_dimension=4, joints=17, embedding_dimension=8),
    )
    adapter.train()
    output = adapter(torch.randn(2, 1, 5, 17, 3))

    assert not encoder.training
    assert not any(parameter.requires_grad for parameter in encoder.parameters())
    assert output.shape == (2, 8)
    assert all(parameter.requires_grad for parameter in adapter.head.parameters())


def test_balanced_batch_plan_is_deterministic_and_exact() -> None:
    labels = [label for label in range(4) for _ in range(4)]
    first = list(
        BalancedBatchSampler(labels, classes_per_batch=2, samples_per_class=4, seed=17)
    )
    second = list(
        BalancedBatchSampler(labels, classes_per_batch=2, samples_per_class=4, seed=17)
    )

    assert first == second
    for batch in first:
        assert set(Counter(labels[index] for index in batch).values()) == {4}
