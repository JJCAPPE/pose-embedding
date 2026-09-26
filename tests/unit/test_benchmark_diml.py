"""Analytical DIML transport and the declared motion/scoring contract."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn
from torch.utils.data import TensorDataset

from pose_embed.benchmark.descriptors import (
    descriptor_summary,
    encode_retrieval,
    read_descriptors,
    save_descriptors,
)
from pose_embed.benchmark.diml import (
    ANATOMY,
    DIMLHead,
    DIMLParameters,
    DIMLScorer,
    cross_correlation_mass,
    structural_similarity,
    transport_plan,
)
from pose_embed.benchmark.losses import build_loss
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.retrieval import evaluate_retrieval, method_retrieval_policy


def test_entropic_two_by_two_has_exact_closed_form():
    entropy = 0.2
    actual = transport_plan([[0, 1], [1, 0]], [0.5, 0.5], [0.5, 0.5], entropy=entropy)
    diagonal = 0.5 / (1 + np.exp(-1 / entropy))
    np.testing.assert_allclose(
        actual, [[diagonal, 0.5 - diagonal], [0.5 - diagonal, diagonal]], atol=1e-14
    )


def test_nonuniform_and_zero_marginals_are_preserved():
    source, target = np.array([0.0, 0.3, 0.7]), np.array([0.8, 0.2])
    plan = transport_plan(
        [[2, 1], [0.1, 0.3], [0.5, 0.2]], source, target, tolerance=1e-10
    )
    np.testing.assert_allclose(plan.sum(-1), source, atol=1e-10)
    np.testing.assert_allclose(plan.sum(-2), target, atol=1e-10)
    assert (plan[0] == 0).all()
    with pytest.raises(ValueError, match="did not converge"):
        transport_plan([[0, 1], [0.5, 0]], [0.3, 0.7], [0.8, 0.2], iterations=1)


def test_cross_correlation_is_opposite_global_and_zero_mass_uniform_valid():
    local = np.array([[[1.0, 0], [0, 1], [-1, 0]]])
    mask = np.array([[True, True, False]])
    np.testing.assert_array_equal(
        cross_correlation_mass(local, [[1.0, 0]], mask), [[1.0, 0, 0]]
    )
    np.testing.assert_array_equal(
        cross_correlation_mass(local, [[-1.0, -1]], mask), [[0.5, 0.5, 0]]
    )
    np.testing.assert_array_equal(
        cross_correlation_mass(local, [[1.0, 0]], mask * False), [[0, 0, 0]]
    )
    score = structural_similarity(
        local, local, [[1, 0]], [[1, 0]], mask * False, mask, DIMLParameters()
    )
    assert score.tolist() == [0]


def test_motion_grid_shared_projection_mask_and_person_permutation():
    head = DIMLHead(2, 2)
    with torch.no_grad():
        head.projection.weight.copy_(torch.eye(2))
        head.projection.bias.zero_()
    features = torch.zeros(1, 2, 8, 17, 2)
    mask = torch.ones(1, 2, 8, 17, dtype=torch.bool)
    for t in range(4):
        for group, joints in enumerate(ANATOMY):
            features[:, :, t * 2 : t * 2 + 2, joints, 0] = 10 * t + group + 1
            features[:, :, t * 2 : t * 2 + 2, joints, 1] = 1
    values = head.forward_descriptors(features, mask)
    assert values["local"][0, :, 0].tolist() == [
        10 * t + g + 1 for t in range(4) for g in range(4)
    ]
    expected = torch.nn.functional.normalize(features.mean((1, 2, 3)), dim=-1)
    torch.testing.assert_close(values["embeddings"], expected)
    shuffled = head.forward_descriptors(features.flip(1), mask.flip(1))
    for key in values:
        torch.testing.assert_close(shuffled[key], values[key])
    mask[:, :, :2, ANATOMY[0]] = False
    masked = head.forward_descriptors(features, mask)
    assert not masked["local_mask"][0, 0]
    assert not masked["local"][0, 0].any()
    all_invalid = head.forward_descriptors(features, mask * False)
    assert not all_invalid["embeddings"].any() and not all_invalid["local"].any()


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 2)

    def get_representation(self, values):
        return self.linear(values)


def test_ms_miner_training_and_structured_encoding_share_actual_model():
    torch.manual_seed(41)
    model = MotionRetrievalModel(
        Encoder(), method_id="diml", embedding_dimension=4, representation_dimension=2
    )
    criterion = build_loss("diml", {"embedding_dimension": 4}, 2)
    poses = torch.randn(8, 2, 4, 17, 3)
    poses[..., 2] = 1
    labels = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1])
    value = criterion(model(poses), labels)
    value.backward()
    assert torch.isfinite(value)
    assert model.head.projection.weight.grad.abs().sum() > 0
    assert model.encoder.linear.weight.grad.abs().sum() > 0
    descriptors = encode_retrieval(model, TensorDataset(poses, labels), "cpu", 3)
    assert model.training
    assert descriptors["local"].shape == (8, 16, 4)
    assert descriptor_summary(descriptors)["bytes_per_sample"] == (4 + 16 * 4) * 4 + 16
    clone = MotionRetrievalModel(
        Encoder(), method_id="diml", embedding_dimension=4, representation_dimension=2
    )
    clone.load_state_dict(model.state_dict(), strict=True)
    for key, expected in descriptors.items():
        np.testing.assert_allclose(
            encode_retrieval(clone, TensorDataset(poses, labels), "cpu", 2)[key],
            expected,
            atol=1e-6,
        )


def _descriptors(count=6, dimension=2):
    glob = np.zeros((count, dimension), np.float32)
    glob[:, 0] = 1
    local = np.repeat(glob[:, None, :], 16, axis=1)
    local[1::2] *= -1
    return {
        "embeddings": glob,
        "local": local,
        "local_mask": np.ones((count, 16), bool),
    }


def _records(count=6):
    return [
        {"sample_id": f"S001C001P{i + 1:03d}R001A{i % 2 + 1:03d}"} for i in range(count)
    ]


def test_global_plus_transport_ranking_and_chunks_agree_with_hand_scores():
    desc = _descriptors()
    params = DIMLParameters()
    scorer = DIMLScorer(desc, desc, params)
    scores = scorer([0], list(range(6)), [[0]])[0]
    np.testing.assert_allclose(scores, [1, 4, 6, 4, 6, 4])
    policy = method_retrieval_policy("diml", params.model_dump())
    results = []
    for pair_chunk in (1, 3, 64):
        callback = DIMLScorer(
            desc, desc, params.model_copy(update={"pair_chunk_size": pair_chunk})
        )
        for query_chunk in (1, 3, 128):
            results.append(
                evaluate_retrieval(
                    desc["embeddings"],
                    desc["embeddings"],
                    _records(),
                    _records(),
                    chunk_size=query_chunk,
                    score_rows=callback,
                    scoring_policy=policy,
                )
            )
    assert all(row == results[0] for row in results)
    assert results[0]["metrics"]["r_at_1"] == 1
    assert results[0]["metrics"]["map"] == 1


def test_shortlist_excludes_synchronized_views_before_selecting_hundred():
    desc = _descriptors(104)
    scorer = DIMLScorer(desc, desc, DIMLParameters())
    values = scorer([0], list(range(104)), [[0, 1, 2]])[0]
    assert np.all(values[3:103] >= 2)
    assert values[103] == 1
    assert np.array_equal(values[:3], [1, 1, 1])


def test_custom_scorer_can_accept_zero_global_vectors_without_cosine():
    desc = _descriptors()
    desc["embeddings"][:] = 0
    result = evaluate_retrieval(
        desc["embeddings"],
        desc["embeddings"],
        _records(),
        _records(),
        score_rows=DIMLScorer(desc, desc, DIMLParameters()),
        scoring_policy=method_retrieval_policy("diml", {}),
    )
    assert result["metrics"]["map"] == 1
    with pytest.raises(ValueError, match="zero-norm"):
        evaluate_retrieval(
            desc["embeddings"], desc["embeddings"], _records(), _records()
        )


def test_descriptor_archive_cost_and_tampering(tmp_path):
    desc = _descriptors()
    save_descriptors(tmp_path, desc, "diml", 2)
    restored = read_descriptors(tmp_path, "diml", 6, 2)
    assert descriptor_summary(restored)["total_bytes"] == 6 * (17 * 2 * 4 + 16)
    with pytest.raises(FileExistsError):
        save_descriptors(tmp_path, desc, "diml", 2)
    damaged = copy.deepcopy(desc)
    damaged["local"] = damaged["local"][:, :15]
    with (tmp_path / "retrieval-descriptors.npz").open("wb") as stream:
        np.savez(stream, **damaged)
    with pytest.raises(ValueError, match="fields/shapes"):
        read_descriptors(tmp_path, "diml", 6, 2)


def test_structural_report_reconstructs_head_and_rejects_rehashed_descriptor_tamper(
    tmp_path,
):
    from pose_embed.benchmark.config import load_benchmark
    from pose_embed.benchmark.evaluation import _replay_structural_result

    desc = _descriptors(dimension=512)
    spec = SimpleNamespace(method_id="diml", embedding_dimension=512, parameters={})
    config = load_benchmark()
    model = MotionRetrievalModel(nn.Identity(), method_id="diml")
    torch.save({"model": model.state_dict()}, tmp_path / "checkpoint.pt")
    save_descriptors(tmp_path, desc, "diml", 512)
    result = evaluate_retrieval(
        desc["embeddings"],
        desc["embeddings"],
        _records(),
        _records(),
        recall_k=config.metrics.recall_k,
        score_rows=model.head.make_retrieval_scorer(desc, desc),
        scoring_policy=method_retrieval_policy("diml", {}),
    )
    episode = {"sample_ids": [r["sample_id"] for r in _records()]}
    _replay_structural_result(tmp_path, tmp_path, spec, episode, config, result)
    desc["local"][1] *= -1
    with (tmp_path / "retrieval-descriptors.npz").open("wb") as stream:
        np.savez(stream, **desc)
    # Array shapes and bytes are unchanged; a maliciously refreshed archive hash
    # cannot make the old rank evidence agree with independently replayed scoring.
    with pytest.raises(ValueError, match="ranks differ"):
        _replay_structural_result(tmp_path, tmp_path, spec, episode, config, result)


def test_pairwise_first_convergence_is_invariant_to_processing_chunk():
    rng = np.random.default_rng(30)
    cost = rng.uniform(0, 1, size=(4, 5, 5))
    source = rng.uniform(size=(4, 5))
    source /= source.sum(-1, keepdims=True)
    target = rng.uniform(size=(4, 5))
    target /= target.sum(-1, keepdims=True)
    batch = transport_plan(cost, source, target)
    separate = np.stack(
        [transport_plan(c, s, t) for c, s, t in zip(cost, source, target, strict=True)]
    )
    np.testing.assert_array_equal(batch, separate)
