from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import torch
from pytorch_metric_learning import losses, miners

from pose_embed.losses import (
    ContextualLossConfig,
    ContextualMetricLoss,
    MultiSimilarityWithMinerLoss,
    PairwiseContrastiveLoss,
    SupervisedContrastiveLoss,
)


def test_contextual_loss_matches_audited_repository_reference(
    repository_root: Path,
) -> None:
    reference_path = (
        repository_root
        / "contextual-similarity-study-pack"
        / "contextual_loss_reference.py"
    )
    spec = importlib.util.spec_from_file_location(
        "contextual_reference", reference_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    torch.manual_seed(13)
    labels = torch.tensor([0, 0, 1, 1, 2, 2])
    candidate_embeddings = torch.randn(6, 7, requires_grad=True)
    reference_embeddings = candidate_embeddings.detach().clone().requires_grad_(True)
    candidate = ContextualMetricLoss(ContextualLossConfig(k=2))
    reference = module.ContextualMetricLoss(module.ContextualLossConfig(k=2))

    candidate_loss, candidate_stats = candidate(candidate_embeddings, labels)
    reference_loss, reference_stats = reference(reference_embeddings, labels)
    candidate_loss.backward()
    reference_loss.backward()

    torch.testing.assert_close(candidate_loss, reference_loss)
    torch.testing.assert_close(candidate_embeddings.grad, reference_embeddings.grad)
    for key in reference_stats:
        torch.testing.assert_close(candidate_stats[key], reference_stats[key])


def test_contextual_loss_rejects_unbalanced_physical_batch() -> None:
    criterion = ContextualMetricLoss(ContextualLossConfig(k=2))
    embeddings = torch.randn(5, 3)
    labels = torch.tensor([0, 0, 1, 1, 1])

    with pytest.raises(ValueError, match="exactly k"):
        criterion(embeddings, labels)


@pytest.mark.parametrize(
    "criterion",
    [PairwiseContrastiveLoss(), SupervisedContrastiveLoss(temperature=0.1)],
)
def test_core_baseline_losses_are_finite_and_differentiable(
    criterion: torch.nn.Module,
) -> None:
    embeddings = torch.tensor(
        [[1.0, 0.1], [0.9, 0.2], [-1.0, 0.1], [-0.9, 0.2]],
        requires_grad=True,
    )
    labels = torch.tensor([0, 0, 1, 1])
    loss = criterion(embeddings, labels)
    loss.backward()

    assert torch.isfinite(loss)
    assert embeddings.grad is not None
    assert torch.isfinite(embeddings.grad).all()


def test_gated_multi_similarity_matches_pinned_library_composition() -> None:
    torch.manual_seed(23)
    embeddings = torch.randn(8, 5)
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    candidate = MultiSimilarityWithMinerLoss(
        library_version="2.9.0",
        loss_alpha=2.0,
        loss_beta=50.0,
        loss_base=0.5,
        miner_epsilon=0.1,
        distance_p=2,
        distance_power=1,
    )(embeddings, labels)
    pairs = miners.MultiSimilarityMiner(epsilon=0.1)(embeddings, labels)
    expected = losses.MultiSimilarityLoss(alpha=2, beta=50, base=0.5)(
        embeddings, labels, pairs
    )

    torch.testing.assert_close(candidate, expected)
