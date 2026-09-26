"""Check gradients, label identity, and ranking equations of the v2 losses."""

from __future__ import annotations

import pytest
import torch
import torch.nn.functional as functional
from pydantic import ValidationError
from pytorch_metric_learning import distances, losses

from pose_embed.benchmark.config import load_methods
from pose_embed.benchmark.losses import SUPPORTED_METHODS, build_loss, supports


def batch() -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(52)
    # P != K deliberately catches losses that infer positive groups by shape.
    embeddings = torch.randn(20, 12, generator=generator, dtype=torch.float64)
    labels = torch.arange(5).repeat_interleave(4)
    return embeddings.requires_grad_(), labels


def parameters(method: str) -> dict[str, object]:
    return dict(load_methods()[method].parameters) | {"embedding_dimension": 12}


@pytest.mark.parametrize("method", sorted(SUPPORTED_METHODS))
def test_supported_losses_have_finite_scalar_and_embedding_gradients(
    method: str,
) -> None:
    embeddings, labels = batch()
    module = build_loss(method, parameters(method), 5).double()
    value = module(embeddings, labels)
    assert value.shape == ()
    assert torch.isfinite(value)
    value.backward()
    assert embeddings.grad is not None and torch.isfinite(embeddings.grad).all()
    assert embeddings.grad.abs().sum() > 0


def test_registry_support_status_cannot_claim_a_substitute() -> None:
    for method, spec in load_methods().items():
        assert supports(method) == (spec.status == "implemented")
        if spec.status == "blocked":
            with pytest.raises(NotImplementedError, match=method):
                build_loss(method, {}, 5)
    with pytest.raises(NotImplementedError, match="unknown method"):
        build_loss("invented", {}, 5)


@pytest.mark.parametrize("method", ["proxy_anchor", "proxy_nca", "normalized_softmax"])
def test_trainable_class_parameters_update_and_restore(method: str) -> None:
    embeddings, labels = batch()
    module = build_loss(method, parameters(method), 5).double()
    before = {
        name: parameter.detach().clone()
        for name, parameter in module.named_parameters()
    }
    assert before
    optimizer = torch.optim.SGD(module.parameters(), lr=0.1)
    module(embeddings, labels).backward()
    optimizer.step()
    assert any(
        not torch.equal(before[name], parameter)
        for name, parameter in module.named_parameters()
    )
    restored = build_loss(method, parameters(method), 5).double()
    restored.load_state_dict(module.state_dict())
    assert torch.equal(module(embeddings, labels), restored(embeddings, labels))
    with pytest.raises(ValueError, match="map action labels globally"):
        module(embeddings, labels + 100)


def test_contextual_contrastive_component_has_exact_paired_margins() -> None:
    embeddings, labels = batch()
    values = parameters("contextual") | {"lam": 0.0, "gamma": 0.0}
    contextual = build_loss("contextual", values, 5)
    contrastive = build_loss("contrastive", parameters("contrastive"), 5)
    torch.testing.assert_close(
        contextual(embeddings, labels), contrastive(embeddings, labels)
    )
    assert values["positive_margin"] == 0.75
    assert values["negative_margin"] == 0.6


@pytest.mark.parametrize("method", ["smooth_ap", "roadmap"])
def test_ranking_losses_are_invariant_to_interleaved_class_order(method: str) -> None:
    embeddings, labels = batch()
    module = build_loss(method, parameters(method), 5)
    permutation = torch.randperm(
        len(labels), generator=torch.Generator().manual_seed(8)
    )
    torch.testing.assert_close(
        module(embeddings, labels), module(embeddings[permutation], labels[permutation])
    )


def test_smooth_ap_matches_hand_computed_one_positive_case() -> None:
    embeddings = torch.tensor(
        [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0], [-0.6, 0.8]], dtype=torch.float64
    )
    labels = torch.tensor([0, 0, 1, 1])
    temperature = 0.2
    module = build_loss("smooth_ap", {"temperature": temperature}, 2)
    similarity = (
        functional.normalize(embeddings, dim=1)
        @ functional.normalize(embeddings, dim=1).T
    )
    precision = []
    for index in range(4):
        positive = index ^ 1
        negatives = [j for j in range(4) if labels[j] != labels[index]]
        rank = 1 + sum(
            torch.sigmoid(
                (similarity[index, j] - similarity[index, positive]) / temperature
            )
            for j in negatives
        )
        precision.append(1 / rank)
    torch.testing.assert_close(
        module(embeddings, labels), 1 - torch.stack(precision).mean()
    )


def test_roadmap_surrogate_upper_bounds_exact_ap_loss() -> None:
    embeddings, labels = batch()
    module = build_loss(
        "roadmap", parameters("roadmap") | {"calibration_weight": 0.0}, 5
    )
    similarity = (
        functional.normalize(embeddings, dim=1)
        @ functional.normalize(embeddings, dim=1).T
    )
    average_precisions = []
    for index in range(len(labels)):
        candidates = torch.arange(len(labels)) != index
        order = similarity[index, candidates].argsort(descending=True)
        relevant = (labels[candidates][order] == labels[index]).double()
        precision = relevant.cumsum(0) / torch.arange(
            1, len(labels), dtype=torch.float64
        )
        average_precisions.append((precision * relevant).sum() / relevant.sum())
    exact_loss = 1 - torch.stack(average_precisions).mean()
    assert module(embeddings, labels) >= exact_loss


def test_roadmap_calibration_is_all_pair_mean() -> None:
    embeddings, labels = batch()
    module = build_loss(
        "roadmap", parameters("roadmap") | {"calibration_weight": 1.0}, 5
    )
    similarity = (
        functional.normalize(embeddings, dim=1)
        @ functional.normalize(embeddings, dim=1).T
    )
    same = labels[:, None] == labels[None, :]
    positive = same & ~torch.eye(len(labels), dtype=torch.bool)
    expected = (
        functional.relu(0.9 - similarity[positive]).mean()
        + functional.relu(similarity[~same] - 0.6).mean()
    )
    torch.testing.assert_close(module(embeddings, labels), expected)


def test_ms_miner_changes_objective_and_supcon_is_distinct_from_ntxent() -> None:
    embeddings, labels = batch()
    plain = build_loss("multi_similarity", parameters("multi_similarity"), 5)
    mined = build_loss(
        "multi_similarity_miner", parameters("multi_similarity_miner"), 5
    )
    assert not torch.isclose(plain(embeddings, labels), mined(embeddings, labels))
    supcon = build_loss("supcon", parameters("supcon"), 5)
    nt_xent = build_loss("nt_xent", parameters("nt_xent"), 5)
    assert not torch.isclose(supcon(embeddings, labels), nt_xent(embeddings, labels))


def test_ms_matches_declared_pinned_library_loss() -> None:
    embeddings, labels = batch()
    actual = build_loss("multi_similarity", parameters("multi_similarity"), 5)
    expected = losses.MultiSimilarityLoss(
        alpha=2, beta=50, base=0.5, distance=distances.CosineSimilarity()
    )
    torch.testing.assert_close(actual(embeddings, labels), expected(embeddings, labels))


def test_rejects_misspelled_and_nonfinite_parameters_and_embeddings() -> None:
    with pytest.raises(ValidationError):
        build_loss("contextual", {"epsilon": 0.1}, 5)
    with pytest.raises(ValidationError):
        build_loss("smooth_ap", {"temperature": float("nan")}, 5)
    embeddings, labels = batch()
    invalid = embeddings.detach().clone()
    invalid[0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        build_loss("contrastive", parameters("contrastive"), 5)(invalid, labels)
