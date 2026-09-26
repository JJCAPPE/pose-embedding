"""Independent arithmetic and feature-training checks for the three Metrix rows."""

import math

import pytest
import torch
import torch.nn.functional as F
from torch import nn

from pose_embed.benchmark.metrix import (
    MetrixLoss,
    MetrixMeanMaxHead,
    MetrixMSParameters,
    MetrixPAParameters,
    cross_class_pairs,
    mix_features,
    mixed_class_targets,
    ms_mining_masks,
    multi_similarity_terms,
    proxy_anchor_terms,
    proxy_nca_terms,
)
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import optimizer_step


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(3, 4)
        self.calls = 0

    def get_representation(self, value):
        self.calls += 1
        return self.projection(value)


def fixture(method="multi_similarity_metrix", frozen=False):
    torch.manual_seed(91)
    model = MotionRetrievalModel(
        TinyEncoder(),
        method_id=method,
        train_encoder=not frozen,
        representation_dimension=4,
        joints=2,
        embedding_dimension=6,
    ).double()
    loss = MetrixLoss(method, {"feature_chunk_size": 2}, 3, 6).double()
    poses = torch.randn(6, 2, 3, 2, 3, dtype=torch.float64)
    poses[..., 2] = 1
    return model, loss, poses, torch.tensor([0, 0, 1, 1, 2, 2])


def test_weighted_ms_matches_hand_equation_not_convex_hard_losses():
    p = MetrixMSParameters(positive_scale=2, negative_scale=3, base=0.1)
    sim = torch.tensor([[0.2, 0.7]], dtype=torch.float64, requires_grad=True)
    weights = torch.tensor([[0.25, 0.75]], dtype=torch.float64)
    observed = multi_similarity_terms(sim, weights, 1 - weights, p)
    expected = math.log1p(0.25 * math.exp(-0.2) + 0.75 * math.exp(-1.2)) / 2
    expected += math.log1p(0.75 * math.exp(0.3) + 0.25 * math.exp(1.8)) / 3
    assert observed.item() == pytest.approx(expected)
    hard = torch.tensor([[1.0, 0.0]], dtype=torch.float64)
    wrong = 0.25 * multi_similarity_terms(sim, hard, 1 - hard, p)
    wrong += 0.75 * multi_similarity_terms(sim, 1 - hard, hard, p)
    assert abs(observed - wrong) > 1e-3
    observed.backward()
    assert torch.isfinite(sim.grad).all()


def test_empty_mined_rows_are_zero_with_finite_zero_gradient():
    sim = torch.ones(2, 2, requires_grad=True)
    zero = torch.zeros_like(sim)
    value = multi_similarity_terms(sim, zero, zero, MetrixMSParameters())
    assert value == 0
    value.backward()
    assert torch.equal(sim.grad, zero)


def test_clean_mining_keeps_hard_pairs_and_never_self():
    embeddings = F.normalize(
        torch.tensor([[1.0, 0.0], [0.99, 0.1], [0.0, 1.0], [0.1, 0.99]]), dim=-1
    )
    labels = torch.tensor([0, 0, 1, 1])
    pos, neg = ms_mining_masks(embeddings, labels, 0.01)
    assert not pos.any() and not neg.any()
    pos, neg = ms_mining_masks(embeddings, labels, 2.0)
    assert pos.sum() == 4 and neg.sum() == 8
    assert not pos.diagonal().any() and not neg.diagonal().any()


def test_proxy_anchor_weighted_terms_and_present_proxy_denominator():
    p = MetrixPAParameters(alpha=2, margin=0.1)
    sim = torch.tensor([[0.2, 0.4, 0.6], [0.5, 0.3, 0.1]], dtype=torch.float64)
    y = torch.tensor([[0.25, 0.75, 0], [0.6, 0.4, 0]], dtype=torch.float64)
    positive = (
        sum(
            math.log1p(
                sum(
                    float(y[i, j]) * math.exp(-2 * (float(sim[i, j]) - 0.1))
                    for i in range(2)
                )
            )
            for j in range(2)
        )
        / 2
    )
    negative = (
        sum(
            math.log1p(
                sum(
                    (1 - float(y[i, j])) * math.exp(2 * (float(sim[i, j]) + 0.1))
                    for i in range(2)
                )
            )
            for j in range(3)
        )
        / 3
    )
    assert proxy_anchor_terms(sim, y, p).item() == pytest.approx(positive + negative)


def test_proxy_nca_weights_inside_log_and_all_proxy_denominator():
    logits = torch.tensor(
        [[math.log(2), math.log(3), math.log(5)]],
        dtype=torch.float64,
        requires_grad=True,
    )
    y = torch.tensor([[0.25, 0.75, 0]], dtype=torch.float64)
    value = proxy_nca_terms(logits, y)
    assert value.item() == pytest.approx(math.log(10) - math.log(0.25 * 2 + 0.75 * 3))
    assert abs(value + (y * F.log_softmax(logits, dim=1)).sum()) > 1e-3
    value.backward()
    assert logits.grad[0, 2] > 0
    for target in [0, 1]:
        label = torch.tensor([target])
        torch.testing.assert_close(
            proxy_nca_terms(logits, F.one_hot(label, 3).double()),
            F.cross_entropy(logits, label),
        )


def test_mix_masks_endpoints_and_gradients_to_both_sources():
    left = torch.tensor([1.0, 3.0]).reshape(1, 1, 1, 2, 1).requires_grad_()
    right = torch.tensor([5.0, 7.0]).reshape_as(left).requires_grad_()
    lm = torch.tensor([True, False]).reshape(1, 1, 1, 2)
    rm = torch.ones_like(lm)
    for weight, expected, mask in [(0, right, rm), (1, left, lm)]:
        mixed, actual = mix_features(left, right, lm, rm, weight)
        torch.testing.assert_close(mixed, expected)
        assert torch.equal(actual, mask)
    mixed, mask = mix_features(left, right, lm, rm, 0.25)
    assert torch.equal(mask, lm & rm)
    mixed.sum().backward()
    torch.testing.assert_close(left.grad, torch.full_like(left, 0.25))
    torch.testing.assert_close(right.grad, torch.full_like(right, 0.75))


def test_mixing_precedes_nonlinear_pooling_not_embedding_mixing():
    head = MetrixMeanMaxHead(1, 1).double()
    with torch.no_grad():
        head.projection.weight.fill_(1)
        head.projection.bias.zero_()
    left = torch.tensor([0.0, 4.0], dtype=torch.float64).reshape(1, 1, 1, 2, 1)
    right = torch.tensor([4.0, 0.0], dtype=torch.float64).reshape_as(left)
    mask = torch.ones(left.shape[:-1], dtype=torch.bool)
    mixed, valid = mix_features(left, right, mask, mask, 0.5)
    assert head.forward_raw(mixed, valid).item() == 4
    assert (
        0.5 * head.forward_raw(left, mask) + 0.5 * head.forward_raw(right, mask)
    ).item() == 6
    torch.testing.assert_close(
        head.forward_raw(mixed, ~valid), head.projection.bias[None]
    )


def test_all_pair_coverage_soft_targets_and_both_ms_pair_modes():
    labels = torch.tensor([0, 0, 1, 1, 1, 2, 2])
    left, right = cross_class_pairs(labels)
    assert len(left) == 49 - (4 + 9 + 4)
    assert torch.all(labels[left] != labels[right])
    y = mixed_class_targets(labels, left, right, 0.25, 3)
    torch.testing.assert_close(y.sum(1), torch.ones(len(left)))
    assert y[0].tolist() == [0.25, 0.75, 0]
    clean = F.normalize(torch.arange(28, dtype=torch.float64).reshape(7, 4) + 1, dim=-1)
    mixed = F.normalize(clean[left] + clean[right], dim=-1)
    loss = MetrixLoss("multi_similarity_metrix", {}, 3, 4)
    for mode in ["positive_negative", "anchor_negative"]:
        observed = loss.mixed_loss(clean, mixed, labels, left, right, 0.25, mode)
        expected = []
        for anchor in range(7):

            def eligible(i, anchor=anchor, mode=mode):
                source = int(left[i])
                positive = (
                    source == anchor
                    if mode == "anchor_negative"
                    else labels[source] == labels[anchor] and source != anchor
                )
                return positive and labels[right[i]] != labels[anchor]

            indices = [i for i in range(len(left)) if eligible(i)]
            similarities = (clean[anchor] @ mixed[indices].T).tolist()
            p = loss.config
            pos = (
                math.log1p(
                    sum(
                        0.25 * math.exp(-p.positive_scale * (s - p.base))
                        for s in similarities
                    )
                )
                / p.positive_scale
            )
            neg = (
                math.log1p(
                    sum(
                        0.75 * math.exp(p.negative_scale * (s - p.base))
                        for s in similarities
                    )
                )
                / p.negative_scale
            )
            expected.append(pos + neg)
        assert observed.item() == pytest.approx(sum(expected) / 7)


@pytest.mark.parametrize(
    "method", ["multi_similarity_metrix", "proxy_anchor_metrix", "proxy_nca_metrix"]
)
@pytest.mark.parametrize("frozen", [False, True])
def test_full_training_one_forward_gradients_and_no_eval_mix(method, frozen):
    model, loss, poses, labels = fixture(method, frozen)
    before = model.head.projection.weight.detach().clone()
    optimizer = torch.optim.AdamW([*model.parameters(), *loss.parameters()], lr=0.01)
    value = optimizer_step(model, loss, optimizer, poses, labels)
    assert math.isfinite(value) and model.encoder.calls == 1
    assert not torch.equal(before, model.head.projection.weight)
    assert (model.encoder.projection.weight.grad is None) == frozen
    if method != "multi_similarity_metrix":
        assert loss.proxies.grad.abs().sum() > 0
    model.eval()
    first = model(poses)
    torch.testing.assert_close(first, model(poses))
    assert first.shape == (6, 6)
    with pytest.raises(RuntimeError, match="training-only"):
        loss.training_loss(model, poses, labels)
    with pytest.raises(RuntimeError, match="embedding-only"):
        loss(first, labels)


def test_sampling_reproducibility_chunk_equivalence_and_label_validation():
    model, loss, poses, labels = fixture()
    torch.manual_seed(36)
    first = loss.training_loss(model, poses, labels)
    first.backward()
    gradient = model.encoder.projection.weight.grad.clone()
    model.zero_grad(set_to_none=True)
    unchunked = MetrixLoss(
        "multi_similarity_metrix", {"feature_chunk_size": 1000}, 3, 6
    ).double()
    torch.manual_seed(36)
    second = unchunked.training_loss(model, poses, labels)
    second.backward()
    torch.testing.assert_close(first, second)
    torch.testing.assert_close(gradient, model.encoder.projection.weight.grad)
    with pytest.raises(ValueError, match="globally"):
        loss.training_loss(model, poses, labels + 99)


def test_proxy_nca_clean_recipe_and_optimizer_groups_match_base():
    from pose_embed.benchmark.config import load_benchmark
    from pose_embed.benchmark.proxy_nca_plus import ProxyNCAPlusLoss
    from pose_embed.benchmark.training import build_optimizer, resolve_recipe

    model, loss, poses, labels = fixture("proxy_nca_metrix")
    embeddings = model(poses)
    base = ProxyNCAPlusLoss(6, 3).double()
    with torch.no_grad():
        base.proxies.copy_(loss.proxies)
    torch.testing.assert_close(
        loss.clean_loss(embeddings, labels), base(embeddings, labels)
    )
    torch.testing.assert_close(
        loss.clean_loss(torch.zeros_like(embeddings), labels),
        base(torch.zeros_like(embeddings), labels),
    )
    training = load_benchmark().training.model_copy(update={"encoder_mode": "finetune"})
    recipe = resolve_recipe("proxy_nca_metrix", loss.config.model_dump(), training, 64)
    base_recipe = resolve_recipe("proxy_nca_pp", {}, training, 64)
    assert recipe == base_recipe
    optimizer = build_optimizer(model, loss, recipe, "main")
    assert [g["lr"] for g in optimizer.param_groups] == [0.004, 0.004, 400]
    assert optimizer.defaults["eps"] == 1 and optimizer.defaults["weight_decay"] == 0
    assert recipe["warmup_steps"] == 10
    assert optimizer.param_groups[-1]["params"][0] is loss.proxies
    value = loss.training_loss(model, poses, labels)
    value.backward()
    assert loss.proxies.grad.abs().sum() > 0


def test_zero_mix_strength_equals_clean_and_wrong_head_is_rejected():
    model, loss, poses, labels = fixture("proxy_anchor_metrix")
    loss.config = loss.config.model_copy(update={"mix_strength": 0})
    before_rng = torch.random.get_rng_state()
    expected = loss.clean_loss(model(poses), labels)
    torch.testing.assert_close(loss.training_loss(model, poses, labels), expected)
    assert torch.equal(before_rng, torch.random.get_rng_state())
    model.method_id = "contrastive"
    with pytest.raises(ValueError, match="declared feature head"):
        loss.training_loss(model, poses, labels)


def test_pa_mixed_pairs_are_positive_negative_relative_to_each_proxy_anchor():
    labels = torch.tensor([0, 0, 1, 1])
    left, right = cross_class_pairs(labels)
    criterion = MetrixLoss(
        "proxy_anchor_metrix", {"alpha": 2, "margin": 0.1}, 3, 2
    ).double()
    with torch.no_grad():
        criterion.proxies.copy_(torch.tensor([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]))
    mixed = F.normalize(torch.arange(16, dtype=torch.float64).reshape(8, 2) + 1, dim=-1)
    sim = (mixed @ F.normalize(criterion.proxies, dim=-1).T).detach()
    for coefficient in [0.0, 0.25, 1.0]:
        expected_pos, expected_neg = 0.0, 0.0
        for proxy in range(3):
            indices = [i for i in range(len(left)) if labels[left[i]] == proxy]
            expected_pos += math.log1p(
                sum(
                    coefficient * math.exp(-2 * (float(sim[i, proxy]) - 0.1))
                    for i in indices
                )
            )
            expected_neg += math.log1p(
                sum(
                    (1 - coefficient) * math.exp(2 * (float(sim[i, proxy]) + 0.1))
                    for i in indices
                )
            )
        expected = expected_pos / 2 + expected_neg / 3
        observed = criterion.mixed_loss(
            None, mixed, labels, left, right, coefficient, "positive_negative"
        )
        assert observed.item() == pytest.approx(expected)
        assert torch.isfinite(observed)
    criterion.zero_grad()
    criterion.mixed_loss(
        None, mixed, labels, left, right, 0.25, "positive_negative"
    ).backward()
    assert torch.equal(criterion.proxies.grad[2], torch.zeros(2, dtype=torch.float64))
