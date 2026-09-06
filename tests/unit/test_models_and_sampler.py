from __future__ import annotations

import importlib.util
from collections import Counter
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
