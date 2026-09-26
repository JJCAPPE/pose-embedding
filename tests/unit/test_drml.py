from __future__ import annotations

import copy

import pytest
import torch

from pose_embed.benchmark.drml import DRMLHead, DRMLLoss, DRMLParameters


def _fixture():
    torch.manual_seed(31)
    head = DRMLHead(3, 2).double()
    objective = DRMLLoss(3, DRMLParameters(branch_dimension=2)).double()
    features = torch.randn(8, 1, 2, 2, 3, dtype=torch.double, requires_grad=True)
    valid = torch.ones(features.shape[:-1], dtype=torch.bool)
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 0, 1])
    return head, objective, features, valid, labels


def _has_gradient(module):
    return any(
        p.grad is not None and p.grad.abs().sum() > 0 for p in module.parameters()
    )


def test_masked_global_mean_excludes_invalid_tokens_and_handles_empty_clip():
    head = DRMLHead(2, 1)
    features = torch.tensor([[[[[2.0, 4.0], [4.0, 8.0], [999.0, 999.0]]]]])
    mask = torch.tensor([[[[True, True, False]]]])
    torch.testing.assert_close(head.pool(features, mask), torch.tensor([[3.0, 6.0]]))
    torch.testing.assert_close(head.pool(features, mask & False), torch.zeros(1, 2))
    with pytest.raises(ValueError, match="aligned tokens"):
        head.pool(features, mask.float())


def test_reconstruction_is_unsquared_l2_and_assignment_ties_use_first_branch():
    head = DRMLHead(2, 1)
    with torch.no_grad():
        for decoder in head.decoders:
            decoder.weight.zero_()
            decoder.bias.zero_()
    features = torch.tensor([[[[[3.0, 4.0]]]]])
    outputs = head.training_outputs(features, torch.ones(1, 1, 1, 1, dtype=torch.bool))
    torch.testing.assert_close(
        outputs["reconstruction_errors"], torch.full((1, 4), 5.0)
    )
    assert outputs["assignment"].tolist() == [0]
    with torch.no_grad():
        head.decoders[2].bias.copy_(torch.tensor([3.0, 4.0]))
    outputs = head.training_outputs(features, torch.ones(1, 1, 1, 1, dtype=torch.bool))
    assert outputs["assignment"].tolist() == [2]


def test_graph_matches_directed_linear_sum_equation_including_negative_weights():
    head = DRMLHead(1, 1).double()
    with torch.no_grad():
        for layer, bias in zip(head.relation_a, [1.0, 2.0, 4.0, 5.0], strict=True):
            layer.weight.zero_()
            layer.bias.fill_(bias)
        for layer, bias in zip(head.relation_b, [0.0, 0.5, 1.0, 2.0], strict=True):
            layer.weight.zero_()
            layer.bias.fill_(bias)
        head.score.weight.fill_(1)
        head.score.bias.zero_()
        head.updater.weight.copy_(torch.tensor([[0.0, 1.0]]))
        head.updater.bias.zero_()
    individual = torch.tensor([[[2.0], [3.0], [7.0], [11.0]]], dtype=torch.double)
    raw, weights, messages = head.relation_graph(
        individual, torch.zeros(1, 1, dtype=torch.double)
    )
    scores = torch.tensor(
        [
            [1.0, 0.5, 0.0, -1.0],
            [2.0, 1.5, 1.0, 0.0],
            [4.0, 3.5, 3.0, 2.0],
            [5.0, 4.5, 4.0, 3.0],
        ],
        dtype=torch.double,
    )
    expected_weights = scores / scores.sum(dim=0)
    expected_messages = expected_weights.T @ individual[0]
    torch.testing.assert_close(weights[0], expected_weights)
    torch.testing.assert_close(messages[0], expected_messages)
    torch.testing.assert_close(raw, expected_messages.T)
    assert weights.min() < 0
    torch.testing.assert_close(weights.sum(dim=1), torch.ones(1, 4, dtype=torch.double))


def test_zero_relation_denominator_is_rejected_without_substituting_softmax():
    head = DRMLHead(3, 2)
    with torch.no_grad():
        head.score.weight.zero_()
        head.score.bias.zero_()
    with pytest.raises(ValueError, match="zero or non-finite"):
        head.relation_graph(torch.ones(1, 4, 2), torch.ones(1, 3))


@pytest.mark.parametrize("component", ["reconstruction", "ensemble", "embedding"])
def test_objectives_have_exact_separate_gradient_paths(component):
    head, objective, features, valid, labels = _fixture()
    outputs = head.training_outputs(features, valid)
    # Give every branch a subset to test every branch's allowed gradient path.
    outputs["assignment"] = torch.arange(8) % 4
    objective.components(outputs, labels)[component].backward()
    assert (features.grad is not None and features.grad.abs().sum() > 0) == (
        component == "ensemble"
    )
    assert _has_gradient(head.individual) == (component == "ensemble")
    assert _has_gradient(head.decoders) == (component == "reconstruction")
    for module in (head.relation_a, head.relation_b, head.score, head.updater):
        assert _has_gradient(module) == (component == "embedding")
    assert _has_gradient(objective.individual_losses) == (component == "ensemble")
    assert _has_gradient(objective.embedding_loss) == (component == "embedding")


def test_ensemble_restricts_each_pa_objective_to_its_assigned_subset():
    head, objective, features, valid, labels = _fixture()
    outputs = head.training_outputs(features, valid)
    outputs["assignment"] = torch.tensor([0, 0, 0, 1, 1, 2, 2, 2])
    components = objective.components(outputs, labels)
    expected = sum(
        objective.individual_losses[k](
            outputs["individual"][outputs["assignment"] == k, k],
            labels[outputs["assignment"] == k],
        )
        for k in range(3)
    )
    torch.testing.assert_close(components["ensemble"], expected)
    torch.testing.assert_close(
        components["total"],
        expected + 0.1 * components["reconstruction"] + 10 * components["embedding"],
    )
    components["ensemble"].backward()
    assert not _has_gradient(objective.individual_losses[3])


def test_inference_is_unit_length_batch_independent_and_matches_training_embedding():
    head, _, features, valid, _ = _fixture()
    head.eval()
    batch = head(features, valid)
    singleton = torch.cat(
        [head(features[i : i + 1], valid[i : i + 1]) for i in range(8)]
    )
    torch.testing.assert_close(batch, singleton)
    permutation = torch.tensor([7, 2, 1, 5, 0, 6, 4, 3])
    torch.testing.assert_close(
        head(features[permutation], valid[permutation]), batch[permutation]
    )
    torch.testing.assert_close(batch.norm(dim=-1), torch.ones(8, dtype=torch.double))
    torch.testing.assert_close(
        batch,
        torch.nn.functional.normalize(
            head.training_outputs(features, valid)["embedding"], dim=-1
        ),
    )


def test_default_head_has_four_128_branches_and_512_retrieval_dimensions():
    head = DRMLHead(512)
    assert len(head.individual) == len(head.relation_a) == len(head.relation_b) == 4
    assert head(
        torch.randn(2, 1, 1, 1, 512), torch.ones(2, 1, 1, 1, dtype=torch.bool)
    ).shape == (2, 512)


def test_invalid_class_mapping_and_scalar_loss_bypass_are_rejected():
    head, objective, features, valid, labels = _fixture()
    with pytest.raises(ValueError, match="global integer"):
        objective.components(head.training_outputs(features, valid), labels + 3)
    with pytest.raises(ValueError, match="requires feature training"):
        objective(torch.ones(8, 8), labels)


def _training_fixture():
    from pose_embed.benchmark.config import load_benchmark
    from pose_embed.benchmark.losses import build_loss
    from pose_embed.benchmark.model import MotionRetrievalModel
    from pose_embed.benchmark.training import build_optimizer, resolve_recipe

    class Encoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(3, 3)

        def get_representation(self, poses):
            return self.linear(poses)

    torch.manual_seed(31)
    model = MotionRetrievalModel(
        Encoder(), method_id="drml", representation_dimension=3, embedding_dimension=8
    ).double()
    parameters = DRMLParameters(branch_dimension=2).model_dump()
    criterion = build_loss("drml", parameters | {"embedding_dimension": 8}, 3).double()
    training = load_benchmark().training.model_copy(update={"encoder_mode": "finetune"})
    recipe = resolve_recipe("drml", parameters, training, 8)
    optimizer = build_optimizer(model, criterion, recipe, "main")
    poses = torch.randn(8, 1, 2, 2, 3, dtype=torch.double)
    poses[..., 2] = 1
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 0, 1])
    return model, criterion, optimizer, poses, labels


def test_unassigned_branch_skips_adam_momentum_and_weight_decay(monkeypatch):
    from pose_embed.benchmark.runner import optimizer_step

    model, criterion, optimizer, poses, labels = _training_fixture()
    original = model.head.training_outputs
    branch = 1

    def forced_assignment(features, mask):
        outputs = original(features, mask)
        outputs["assignment"].fill_(branch)
        return outputs

    monkeypatch.setattr(model.head, "training_outputs", forced_assignment)
    optimizer_step(model, criterion, optimizer, poses, labels)
    first_head = copy.deepcopy(model.head.individual[1].state_dict())
    first_proxy = criterion.individual_losses[1].proxies.detach().clone()
    branch = 0
    optimizer_step(model, criterion, optimizer, poses, labels)
    for key, value in model.head.individual[1].state_dict().items():
        assert torch.equal(value, first_head[key])
    assert torch.equal(first_proxy, criterion.individual_losses[1].proxies)
    assert criterion.branch_steps.tolist() == [1, 1, 0, 0]
    assert criterion.training_steps.item() == 2
    assert optimizer.state[model.head.individual[1].weight]["step"].item() == 1


def test_model_criterion_and_optimizer_reload_produce_identical_next_update():
    from pose_embed.benchmark.runner import optimizer_step

    model, criterion, optimizer, poses, labels = _training_fixture()
    optimizer_step(model, criterion, optimizer, poses, labels)
    restored_model, restored_criterion, restored_optimizer, _, _ = _training_fixture()
    restored_model.load_state_dict(copy.deepcopy(model.state_dict()))
    restored_criterion.load_state_dict(copy.deepcopy(criterion.state_dict()))
    restored_optimizer.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    loss = optimizer_step(model, criterion, optimizer, poses, labels)
    restored_loss = optimizer_step(
        restored_model, restored_criterion, restored_optimizer, poses, labels
    )
    assert loss == restored_loss
    for live, restored in [(model, restored_model), (criterion, restored_criterion)]:
        for key, value in live.state_dict().items():
            torch.testing.assert_close(
                value, restored.state_dict()[key], rtol=0, atol=0
            )
