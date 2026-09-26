import ast
import copy
import math
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as F
from torch import nn

from pose_embed.benchmark.avsl import (
    AVSLHead,
    AVSLInference,
    AVSLLoss,
    cam_certainty,
    distance_proxy_anchor,
    linearized_pool,
    motionbert_levels,
)
from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.losses import build_loss
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import optimizer_step
from pose_embed.benchmark.training import (
    advance_optimizer,
    build_optimizer,
    resolve_recipe,
    set_step_learning_rates,
)
from pose_embed.models.motionbert import _encoder_class

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = {"topk": 2}


def source_class(path, name, namespace):
    tree = ast.parse(path.read_text())
    node = next(item for item in tree.body if getattr(item, "name", None) == name)
    exec(
        compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace
    )
    return namespace[name]


@pytest.fixture
def official():
    root = ROOT / ".cache/upstreams/AVSL"
    if not root.exists():
        pytest.skip("fetch the licensed pinned AVSL checkout for source parity")

    class Default:
        def __init__(self, *args, **kwargs):
            pass

    class Base(nn.Module):
        def __init__(self, *args, **kwargs):
            super().__init__()

    namespace = {
        "torch": torch,
        "nn": nn,
        "F": F,
        "init": nn.init,
        "math": math,
        "WithRecorder": Base,
        "_DefaultGlobalCollector": Default,
        "BaseCollector": Base,
    }
    source_class(root / "src/avsl/misc/utils.py", "topk_mask", namespace)
    embedder = source_class(
        root / "src/avsl/models/avsl_embedder.py", "AVSLEmbedder", namespace
    )
    collector = source_class(
        root / "src/avsl/collectors/avsl_collector.py", "AVSLCollector", namespace
    )
    return embedder, collector


@pytest.fixture
def encoder():
    root = (ROOT / ".cache/upstreams/MotionBERT").resolve()
    if not root.exists():
        pytest.skip("fetch pinned MotionBERT for actual architecture checks")
    torch.manual_seed(81)
    return _encoder_class(root)(
        dim_in=3,
        dim_out=3,
        dim_feat=8,
        dim_rep=12,
        depth=5,
        num_heads=2,
        mlp_ratio=2,
        num_joints=2,
        maxlen=9,
        drop_rate=0,
        attn_drop_rate=0,
        drop_path_rate=0,
        att_fuse=True,
    ).double()


def poses():
    generator = torch.Generator().manual_seed(14)
    values = torch.randn(4, 1, 9, 2, 3, dtype=torch.float64, generator=generator)
    values[..., 2] = 1
    return values


def test_source_feature_pooling_cam_certainty_and_relation_parity(official):
    SourceEmbedder, _ = official
    torch.manual_seed(2)
    source = SourceEmbedder(feature_dim_list=[4, 4, 6], output_dim=3).double()
    ours = AVSLHead(4, 6, 9, {"topk": 2}).double()
    features = [torch.randn(2, c, 9, 2, dtype=torch.float64) for c in (4, 4, 6)]
    with torch.no_grad():
        for index, projection in enumerate(ours.projections):
            conv = getattr(source, f"conv1x1_{index}")
            projection.weight.copy_(conv.weight[:, :, 0, 0])
            projection.bias.copy_(conv.bias)
    levels = [feature.permute(0, 2, 3, 1)[:, None] for feature in features]
    descriptors, links = ours.construct(
        levels, torch.ones(2, 1, 9, 2, dtype=torch.bool), compute_relations=True
    )
    embeddings, certainty, source_links = source(features)
    torch.testing.assert_close(
        descriptors["embeddings"],
        torch.stack([F.normalize(x, dim=-1) for x in embeddings], 1).flatten(1),
    )
    torch.testing.assert_close(descriptors["cam_std"], torch.stack(certainty, 1))
    torch.testing.assert_close(links, torch.stack(source_links))


def test_source_hierarchical_distance_parity_and_gradient_separation(official):
    _, SourceCollector = official
    torch.manual_seed(1)
    source = SourceCollector(
        feature_dim_list=[4, 4, 4],
        embed_dim=4,
        num_classes=3,
        topk_corr=2,
        use_proxy=True,
    ).double()
    ours = AVSLInference(4, PARAMETERS).double()
    links = torch.randn(2, 4, 4, dtype=torch.float64)
    ours.update_relations(links)
    source.update_links(list(links))
    embeddings = torch.randn(4, 3, 4, dtype=torch.float64, requires_grad=True)
    targets = torch.randn(3, 3, 4, dtype=torch.float64, requires_grad=True)
    cert = torch.rand_like(embeddings) * 0.1
    target_cert = torch.rand_like(targets) * 0.1
    expected = source.compute_all_mat(
        list(embeddings.unbind(1)),
        list(targets.unbind(1)),
        list(cert.unbind(1)),
        list(target_cert.unbind(1)),
    )[0]
    actual = ours.distances(embeddings.detach(), targets.detach(), cert, target_cert)
    torch.testing.assert_close(actual, expected)
    actual.sum().backward()
    assert embeddings.grad is None and targets.grad is None
    assert ours.coefficient.grad.abs().sum() > 0 and ours.bias.grad.abs().sum() > 0


def test_linearization_masked_pool_identity_ties_and_empty():
    features = torch.tensor(
        [[[[2.0, 1.0], [2.0, 3.0]], [[99.0, 99.0], [0.0, -1.0]]]], dtype=torch.float64
    )
    valid = torch.tensor([[[True, True], [False, True]]])
    pooled, linearized = linearized_pool(features, valid)
    expected = torch.tensor([[2 + 4 / 3, 3 + 1]], dtype=torch.float64)
    torch.testing.assert_close(pooled, expected)
    torch.testing.assert_close(linearized.sum((1, 2)) / 3, pooled)
    assert linearized[0, 0, 0, 0] == 8  # first of equal maxima
    assert linearized[0, 0, 1, 0] == 2
    empty = torch.zeros_like(valid)
    zero_pool, zero_linearized = linearized_pool(features, empty)
    assert not zero_pool.any() and not zero_linearized.any()
    assert not cam_certainty(zero_linearized, empty).any()
    head = AVSLHead(2, 2, 6, {"topk": 1}).double()
    result = head.forward_descriptors([features[:, None]] * 3, empty[:, None])
    assert not result["embeddings"].any() and not result["cam_std"].any()


def test_attribution_reconstructs_distance_and_known_reliability_limits():
    inference = AVSLInference(2, {"topk": 1}).double()
    inference.update_relations(torch.eye(2, dtype=torch.float64).repeat(2, 1, 1))
    first = torch.tensor([[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]], dtype=torch.float64)
    second = torch.tensor([[[0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]]], dtype=torch.float64)
    certainty = torch.zeros_like(first)
    distance, weights, nodes = inference.distances(
        first, second, certainty, certainty, attribution=True
    )
    torch.testing.assert_close(distance, (weights * nodes).sum((2, 3)))
    torch.testing.assert_close(
        weights.sum((2, 3)),
        torch.tensor([[2.0]], dtype=torch.float64),
        atol=3e-8,
        rtol=0,
    )
    with torch.no_grad():
        inference.bias.fill_(100)
    torch.testing.assert_close(
        inference.distances(first, second, certainty, certainty), nodes[:, :, 2].sum(-1)
    )
    with torch.no_grad():
        inference.bias.fill_(-100)
    torch.testing.assert_close(
        inference.distances(first, second, certainty, certainty),
        nodes[:, :, 0].sum(-1),
        atol=5e-8,
        rtol=0,
    )


def test_momentum_checkpoint_initialization_and_frozen_inference():
    state = AVSLInference(2, {"topk": 1}).double()
    first, second = (
        torch.eye(2, dtype=torch.float64).repeat(2, 1, 1),
        torch.ones(2, 2, 2, dtype=torch.float64),
    )
    state.update_relations(first)
    state.update_relations(second)
    torch.testing.assert_close(state.relations, (first + second) / 2)
    restored = AVSLInference(2, {"topk": 1}).double()
    restored.load_state_dict(copy.deepcopy(state.state_dict()))
    restored.update_relations(first)
    torch.testing.assert_close(restored.relations, 0.75 * first + 0.25 * second)
    assert restored.updates.item() == 3
    restored.eval()
    with pytest.raises(ValueError, match="training-only"):
        restored.update_relations(first)


def test_distance_proxy_anchor_hand_equation_and_all_proxy_denominator():
    distance = torch.tensor(
        [[0.3, 2.1, 1.0], [0.5, 1.8, 1.3], [2.0, 0.4, 1.8], [2.3, 0.2, 2.0]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 0, 1, 1])
    positive, negative = [], []
    for proxy in range(3):
        pos = distance[labels == proxy, proxy]
        neg = distance[labels != proxy, proxy]
        if len(pos):
            positive.append(torch.log1p(torch.exp(16 * (pos - 1.8)).sum()))
        negative.append(torch.log1p(torch.exp(-16 * (neg - 2.2)).sum()))
    loss = distance_proxy_anchor(distance, labels)
    torch.testing.assert_close(
        loss, torch.stack(positive).mean() + torch.stack(negative).mean()
    )
    loss.backward()
    assert distance.grad[:, 2].abs().sum() > 0


def test_training_losses_have_disjoint_gradient_paths():
    torch.manual_seed(2)
    head = AVSLHead(4, 6, 12, PARAMETERS).double()
    loss = AVSLLoss(PARAMETERS, 3, 12).double()
    levels = [
        torch.randn(4, 1, 9, 2, c, dtype=torch.float64, requires_grad=True)
        for c in (4, 4, 6)
    ]
    descriptors, links = head.construct(
        levels, torch.ones(4, 1, 9, 2, dtype=torch.bool), compute_relations=True
    )
    head.inference.update_relations(links)
    components = loss.components(
        descriptors, torch.tensor([0, 0, 1, 1]), head.inference
    )
    components["inference"].backward(retain_graph=True)
    assert all(x.grad is None for x in levels)
    assert all(p.weight.grad is None for p in head.projections)
    assert loss.proxies.grad is None
    assert head.inference.coefficient.grad.abs().sum() > 0
    head.inference.zero_grad(set_to_none=True)
    components["construction"].backward()
    assert all(x.grad.abs().sum() > 0 for x in levels)
    assert all(p.weight.grad.abs().sum() > 0 for p in head.projections)
    assert loss.proxies.grad.abs().sum() > 0
    assert head.inference.coefficient.grad is None


def test_actual_depth_capture_one_pass_gradients_and_hook_cleanup(encoder, monkeypatch):
    original = encoder.get_representation
    calls = []

    def counted(values):
        calls.append(1)
        return original(values)

    monkeypatch.setattr(encoder, "get_representation", counted)
    observed = {}

    def record(name):
        def hook(_module, _input, output):
            observed[name] = output

        return hook

    hooks = []
    for depth in (2, 3):
        hooks.extend(
            [
                encoder.blocks_st[depth].register_forward_hook(record(f"st{depth}")),
                encoder.blocks_ts[depth].register_forward_hook(record(f"ts{depth}")),
                encoder.ts_attn[depth].register_forward_hook(record(f"alpha{depth}")),
            ]
        )
    levels = motionbert_levels(encoder, poses(), train_encoder=True)
    for hook in hooks:
        hook.remove()
    assert calls == [1]
    for index, depth in enumerate((2, 3)):
        alpha = observed[f"alpha{depth}"].softmax(-1)
        expected = (
            observed[f"st{depth}"] * alpha[..., :1]
            + observed[f"ts{depth}"] * alpha[..., 1:]
        )
        torch.testing.assert_close(levels[index], expected.reshape_as(levels[index]))
    assert [x.shape[-1] for x in levels] == [8, 8, 12]
    levels[0].square().sum().backward(retain_graph=True)
    assert encoder.blocks_st[2].attn_s.qkv.weight.grad.abs().sum() > 0
    assert encoder.blocks_st[3].attn_s.qkv.weight.grad is None
    encoder.zero_grad(set_to_none=True)
    levels[1].square().sum().backward(retain_graph=True)
    assert encoder.blocks_st[3].attn_s.qkv.weight.grad.abs().sum() > 0
    assert encoder.blocks_st[4].attn_s.qkv.weight.grad is None
    encoder.zero_grad(set_to_none=True)
    levels[2].square().sum().backward()
    assert encoder.blocks_st[4].attn_s.qkv.weight.grad.abs().sum() > 0
    assert not encoder.blocks_st[3]._forward_pre_hooks
    assert not encoder.blocks_st[4]._forward_pre_hooks
    with pytest.raises(RuntimeError):
        motionbert_levels(
            encoder, torch.ones(4, 1, 10, 2, 3, dtype=torch.float64), train_encoder=True
        )
    assert not encoder.blocks_st[3]._forward_pre_hooks
    assert not encoder.blocks_st[4]._forward_pre_hooks


def test_full_step_schedule_checkpoint_and_custom_scorer(encoder):
    model = MotionRetrievalModel(
        encoder,
        method_id="proxy_anchor_avsl",
        method_parameters=PARAMETERS,
        representation_dimension=12,
        embedding_dimension=12,
        joints=2,
    ).double()
    loss = AVSLLoss(PARAMETERS, 3, 12).double()
    config = load_benchmark().training.model_copy(update={"encoder_mode": "finetune"})
    recipe = resolve_recipe("proxy_anchor_avsl", PARAMETERS, config, 64, 96)
    assert recipe["warmup_steps"] == 10 and recipe["minimum_selected_step"] == 16
    optimizer = build_optimizer(model, loss, recipe, "warmup")
    assert not model.train_encoder
    optimizer_step(model, loss, optimizer, poses(), torch.tensor([0, 0, 1, 1]))
    assert encoder.pre_logits.fc.weight.grad is None
    assert model.head.inference.updates.item() == 1
    for parameters in (
        model.head.projections.parameters(),
        [*model.head.inference.parameters(), *loss.parameters()],
    ):
        norm = torch.sqrt(
            sum(p.grad.square().sum() for p in parameters if p.grad is not None)
        )
        assert norm <= 10.00001
    moments = copy.deepcopy(optimizer.state_dict())
    assert advance_optimizer(model, loss, optimizer, recipe, "main") is optimizer
    set_step_learning_rates(optimizer, recipe, 11)
    assert optimizer.param_groups[0]["lr"] == 1e-5
    assert moments["state"].keys() == optimizer.state_dict()["state"].keys()
    optimizer_step(model, loss, optimizer, poses(), torch.tensor([0, 0, 1, 1]))
    assert encoder.pre_logits.fc.weight.grad.abs().sum() > 0
    set_step_learning_rates(optimizer, recipe, 21)
    assert optimizer.param_groups[0]["lr"] == 5e-6
    checkpoint = copy.deepcopy(
        {
            "model": model.state_dict(),
            "criterion": loss.state_dict(),
            "optimizer": optimizer.state_dict(),
        }
    )
    model.eval()
    with pytest.raises(ValueError, match="hierarchical"):
        model(poses())
    with torch.no_grad():
        descriptors = model.retrieval_descriptors(poses())
    arrays = {key: value.numpy() for key, value in descriptors.items()}
    score = model.head.make_retrieval_scorer(arrays, arrays)
    reference = score(np.arange(4), np.arange(4), [[], [], [], []])
    np.testing.assert_allclose(reference, reference.T, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(
        reference, np.concatenate([score([i], np.arange(4)) for i in range(4)])
    )
    with torch.no_grad():
        model.head.inference.bias.add_(100)
        model.head.inference.relations.zero_()
    np.testing.assert_array_equal(score(np.arange(4), np.arange(4)), reference)
    # A fresh scorer reads the new state, proving the original is an immutable snapshot.
    assert not np.allclose(
        model.head.make_retrieval_scorer(arrays, arrays)(np.arange(4), np.arange(4)),
        reference,
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    loss.load_state_dict(checkpoint["criterion"], strict=True)
    optimizer.load_state_dict(checkpoint["optimizer"])
    np.testing.assert_array_equal(
        model.head.make_retrieval_scorer(arrays, arrays)(np.arange(4), np.arange(4)),
        reference,
    )


def test_staged_factory_enforces_full_dimension_and_capacity_profile(monkeypatch):
    from pose_embed.benchmark import losses

    # The full descriptor/scorer path is integrated in the motion registry.
    monkeypatch.setattr(
        losses, "SUPPORTED_METHODS", losses.SUPPORTED_METHODS | {"proxy_anchor_avsl"}
    )
    loss = build_loss("proxy_anchor_avsl", {}, 3)
    assert loss.requires_feature_training and loss.proxies.shape == (3, 3, 512)
    with pytest.raises(ValueError, match="3 x 512"):
        build_loss("proxy_anchor_avsl", {"embedding_dimension": 512}, 3)
    recipe = resolve_recipe(
        "proxy_anchor_avsl", {}, load_benchmark().training, 320, 640, profile=True
    )
    assert recipe["warmup_steps"] == 50 and recipe["minimum_selected_step"] == 101
    assert recipe["profile_phase"] == "post_warmup_capacity"
    assert recipe["profile_executes_warmup"] is False


@pytest.mark.parametrize("profile", [False, True])
@pytest.mark.parametrize("fault", ["counter", "rate", "moment"])
def test_named_checkpoint_verification_after_warmup_or_capacity_profile(
    encoder, profile, fault
):
    from pose_embed.benchmark.avsl import verify_avsl_optimizer
    from pose_embed.benchmark.runner import _checkpoint_state
    from pose_embed.benchmark.training import phase_for_step

    parameters = PARAMETERS | {"warmup_epochs": 1}
    training = load_benchmark().training.model_copy(
        update={
            "encoder_mode": "finetune",
            "classes_per_batch": 2,
            "learning_rate_scale": 0.5,
        }
    )
    recipe = resolve_recipe(
        "proxy_anchor_avsl", parameters, training, 8, 16, profile=profile
    )
    assert recipe["minimum_selected_step"] == 3
    model = MotionRetrievalModel(
        encoder,
        method_id="proxy_anchor_avsl",
        method_parameters=parameters,
        representation_dimension=12,
        embedding_dimension=24,
        joints=2,
    ).double()
    criterion = AVSLLoss(parameters, 2, 24).double()
    phase = phase_for_step(recipe, 1)
    optimizer = build_optimizer(model, criterion, recipe, phase)
    values = torch.randn(4, 2, 9, 2, 3, dtype=torch.float64)
    values[..., 2] = 1
    for step in (1, 2):
        next_phase = phase_for_step(recipe, step)
        if phase != next_phase:
            phase = next_phase
            optimizer = advance_optimizer(model, criterion, optimizer, recipe, phase)
        set_step_learning_rates(optimizer, recipe, step)
        optimizer_step(model, criterion, optimizer, values, torch.tensor([0, 0, 1, 1]))
    state = _checkpoint_state(model, criterion, optimizer, recipe, 2, phase)
    state["selected_step"] = 2
    names = tuple(name for name, _ in encoder.named_parameters())
    verify_avsl_optimizer(state, recipe, names)
    if fault == "counter":
        state["model"]["head.inference.updates"].add_(1)
    elif fault == "rate":
        state["optimizer"]["param_groups"][2]["lr"] *= 2
    else:
        next(iter(state["optimizer"]["state"].values()))["step"].add_(1)
    with pytest.raises(ValueError, match="optimizer|counter"):
        verify_avsl_optimizer(state, recipe, names)
