"""Published-equation fixtures and actual tiny pinned DSTformer depth tests."""

import pytest
import torch
import torch.nn.functional as F

from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.mhgl import (
    MHGLHead,
    MHGLLoss,
    SecondOrderAttention,
    build_mhgl_optimizer,
    motionbert_levels,
    optimizer_recipe,
    temporal_tokens,
)
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.runner import _checkpoint_state, optimizer_step
from pose_embed.models.motionbert import _encoder_class


@pytest.fixture
def encoder(repository_root):
    root = (repository_root / ".cache/upstreams/MotionBERT").resolve()
    if not (root / "lib/model/DSTformer.py").is_file():
        pytest.skip("fetch pinned MotionBERT to run real architecture fixture")
    model = _encoder_class(root)(
        dim_feat=8,
        dim_rep=12,
        depth=5,
        num_heads=2,
        mlp_ratio=2,
        num_joints=2,
        maxlen=9,
        att_fuse=True,
    ).double()
    model.head.requires_grad_(False)
    return model


def poses():
    generator = torch.Generator().manual_seed(4)
    value = torch.randn(4, 2, 9, 2, 3, generator=generator, dtype=torch.float64)
    value[..., 2] = 1
    return value


def test_two_real_depths_match_fused_penultimate_and_final_representation(encoder):
    values = poses()
    captured = {}
    hooks = []
    for name, module in [
        ("st", encoder.blocks_st[3]),
        ("ts", encoder.blocks_ts[3]),
        ("alpha", encoder.ts_attn[3]),
    ]:

        def capture(_module, _inputs, output, name=name):
            captured[name] = output

        hooks.append(module.register_forward_hook(capture))
    original = encoder.get_representation
    calls = []

    def forward(value):
        calls.append(value)
        output = original(value)
        captured["global"] = output
        return output

    encoder.get_representation = forward
    try:
        local, global_ = motionbert_levels(encoder, values, train_encoder=True)
    finally:
        for hook in hooks:
            hook.remove()
    weights = captured["alpha"].softmax(dim=-1)
    fused = captured["st"] * weights[:, :, :1] + captured["ts"] * weights[:, :, 1:]
    torch.testing.assert_close(local, fused.reshape(4, 2, 9, 2, 8), rtol=0, atol=0)
    torch.testing.assert_close(
        global_, captured["global"].reshape(4, 2, 9, 2, 12), rtol=0, atol=0
    )
    assert len(calls) == 1 and not encoder.blocks_st[4]._forward_pre_hooks
    assert local.requires_grad and global_.requires_grad
    local.square().sum().backward()
    assert encoder.blocks_st[3].attn_s.qkv.weight.grad.abs().sum() > 0
    assert encoder.blocks_st[4].attn_s.qkv.weight.grad is None
    encoder.zero_grad(set_to_none=True)
    _, global_ = motionbert_levels(encoder, values, train_encoder=True)
    global_.square().sum().backward()
    assert encoder.blocks_st[4].attn_s.qkv.weight.grad.abs().sum() > 0
    assert encoder.pre_logits.fc.weight.grad.abs().sum() > 0


def test_hook_cleanup_on_failure_and_architecture_mismatch(encoder, monkeypatch):
    def fail(_):
        raise RuntimeError("fixture forward failure")

    monkeypatch.setattr(encoder, "get_representation", fail)
    with pytest.raises(RuntimeError, match="fixture"):
        motionbert_levels(encoder, poses(), train_encoder=True)
    assert not encoder.blocks_st[4]._forward_pre_hooks
    encoder.att_fuse = False
    with pytest.raises(ValueError, match="five-depth"):
        motionbert_levels(encoder, poses(), train_encoder=True)


def test_temporal_bins_keep_joint_person_identity_masks_and_empty_bins():
    values = torch.arange(1, 13, dtype=torch.float64).reshape(1, 2, 3, 2, 1)
    valid = torch.ones(values.shape[:-1], dtype=torch.bool)
    valid[0, 0, 1, 0] = False
    result, mask = temporal_tokens(values, valid, 2)
    expected = torch.tensor(
        [1.0, 2.0, 5.0, 5.0, 7.0, 8.0, 10.0, 11.0], dtype=torch.float64
    )
    torch.testing.assert_close(result.flatten(), expected)
    assert mask.all()
    result, mask = temporal_tokens(values, valid, 6)
    assert torch.equal(
        result.masked_select(~mask[..., None]), torch.zeros(13, dtype=torch.float64)
    )
    assert (~mask).sum() == 12 + 1


def test_attention_matches_hand_product_scale_one_and_residual():
    module = SecondOrderAttention(2).double()
    with torch.no_grad():
        for layer in [module.query, module.key, module.value, module.output]:
            layer.weight.copy_(torch.eye(2))
            layer.bias.zero_()
    x = torch.tensor(
        [[[1.0, 0.0], [0.0, 2.0]]], dtype=torch.float64, requires_grad=True
    )
    mask = torch.ones(1, 2, dtype=torch.bool)
    expected_attention = torch.stack(
        [
            torch.tensor([1.0, 0.0]).double().softmax(0),
            torch.tensor([0.0, 4.0]).double().softmax(0),
        ]
    )[None]
    torch.testing.assert_close(module.attention_weights(x, mask), expected_attention)
    torch.testing.assert_close(module(x, mask), x + expected_attention @ x)
    assert not torch.allclose(
        expected_attention, (x @ x.transpose(-1, -2) / (2**0.5)).softmax(-1)
    )
    module(x, mask).sum().backward()
    assert x.grad.abs().sum() > 0
    for parameter in module.parameters():
        assert parameter.grad is not None and torch.isfinite(parameter.grad).all()


def test_attention_masks_keys_queries_and_all_invalid_gradients():
    module = SecondOrderAttention(3).double()
    x = torch.randn(2, 4, 3, dtype=torch.float64, requires_grad=True)
    valid = torch.tensor([[True, False, True, False], [False, False, False, False]])
    output = module(x, valid)
    weights = module.attention_weights(x, valid)
    assert torch.equal(output[~valid], torch.zeros(6, 3, dtype=torch.float64))
    torch.testing.assert_close(weights.sum(-1), valid.double())
    output.sum().backward()
    assert torch.isfinite(x.grad).all()
    altered = x.detach().clone()
    altered[~valid] = 10000
    torch.testing.assert_close(module(altered, valid), output.detach())


def test_head_two_separate_branches_and_exact_pooling():
    head = MHGLHead(
        local_dimension=2, global_dimension=3, embedding_dimension=8
    ).double()
    local = torch.randn(2, 2, 9, 2, 2, dtype=torch.float64, requires_grad=True)
    global_ = torch.randn(2, 2, 9, 2, 3, dtype=torch.float64, requires_grad=True)
    valid = torch.ones(2, 2, 9, 2, dtype=torch.bool)
    first, second = head.branch_features((local, global_), valid)
    assert first.shape == second.shape == (2, 4)
    result = head((local, global_), valid)
    torch.testing.assert_close(
        result, F.normalize(torch.cat([first, second], dim=-1), dim=-1)
    )
    result.square().mul(torch.arange(8)).sum().backward()
    assert local.grad.abs().sum() > 0 and global_.grad.abs().sum() > 0
    for name, param in head.named_parameters():
        assert param.grad is not None and torch.isfinite(param.grad).all(), name
    token = torch.tensor([[[1.0, 4.0], [3.0, 2.0], [100.0, 100.0]]])
    torch.testing.assert_close(
        head._pool(token, torch.tensor([[True, True, False]])),
        torch.tensor([[5.0, 7.0]]),
    )


def test_printed_hybrid_equation_hand_reference_no_standard_ms_substitution():
    x = torch.tensor(
        [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0], [-0.6, 0.8]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 0, 1, 1])
    loss = MHGLLoss({}, 3, 2).double()
    with torch.no_grad():
        loss.proxies.copy_(torch.tensor([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]))
    components = loss.components(x, labels)
    similarity = F.normalize(x, dim=-1) @ F.normalize(x, dim=-1).T
    expected = []
    for i in range(4):
        positives = [j for j in range(4) if i != j and labels[i] == labels[j]]
        negatives = [j for j in range(4) if labels[i] != labels[j]]
        pos = (
            torch.log1p(sum(torch.exp(-2 * (similarity[i, j] - 1)) for j in positives))
            / 2
        )
        neg = (
            torch.log1p(sum(torch.exp(50 * (similarity[i, j] + 1)) for j in negatives))
            / 50
        )
        expected.append(pos + neg)
    torch.testing.assert_close(
        components["multi_similarity"], torch.stack(expected).mean()
    )
    cosine = F.normalize(x, dim=-1) @ F.normalize(loss.proxies, dim=-1).T
    positive = []
    negative = []
    for c in range(3):
        positives = [i for i in range(4) if labels[i] == c]
        negatives = [i for i in range(4) if labels[i] != c]
        if positives:
            positive.append(
                torch.log1p(
                    sum(torch.exp(-32 * (cosine[i, c] - 0.1)) for i in positives)
                )
            )
        negative.append(
            torch.log1p(sum(torch.exp(32 * (cosine[i, c] + 0.1)) for i in negatives))
        )
    expected_pa = torch.stack(positive).mean() + torch.stack(negative).mean()
    torch.testing.assert_close(components["proxy_anchor"], expected_pa)
    torch.testing.assert_close(
        components["total"], torch.stack(expected).mean() + 0.03 * expected_pa
    )
    components["total"].backward()
    assert x.grad.abs().sum() > 0 and loss.proxies.grad.abs().sum() > 0


@pytest.mark.parametrize("frozen", [False, True])
def test_full_real_encoder_step_and_optimizer_restore(encoder, frozen):
    model = MotionRetrievalModel(
        encoder,
        method_id="mhgl",
        representation_dimension=12,
        embedding_dimension=16,
        joints=2,
        train_encoder=not frozen,
    ).double()
    loss = MHGLLoss({}, 3, 16).double()
    training = load_benchmark().training.model_copy(
        update={"encoder_mode": "frozen" if frozen else "finetune"}
    )
    recipe = optimizer_recipe({}, training)
    optimizer = build_mhgl_optimizer(model, loss, recipe)
    assert [g["lr"] for g in optimizer.param_groups] == [
        0 if frozen else 0.0001,
        0.0001,
        0.01,
    ]
    assert len({id(p) for g in optimizer.param_groups for p in g["params"]}) == sum(
        len(g["params"]) for g in optimizer.param_groups
    )
    labels = torch.tensor([0, 0, 1, 1])
    before = loss.proxies.detach().clone()
    value = optimizer_step(model, loss, optimizer, poses(), labels)
    assert value > 0 and not torch.equal(before, loss.proxies)
    assert (encoder.pre_logits.fc.weight.grad is None) == frozen
    assert model.head.local_attention.query.weight.grad.abs().sum() > 0
    assert model.head.global_attention.query.weight.grad.abs().sum() > 0
    assert not encoder.blocks_st[4]._forward_pre_hooks
    restored = build_mhgl_optimizer(model, loss, recipe)
    restored.load_state_dict(optimizer.state_dict())
    assert (
        restored.state_dict()["param_groups"] == optimizer.state_dict()["param_groups"]
    )
    model.eval()
    values = poses()
    checkpoint = {
        "model": {key: value.clone() for key, value in model.state_dict().items()},
        "criterion": {key: value.clone() for key, value in loss.state_dict().items()},
    }
    expected_output = model(values).detach()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        loss.proxies.zero_()
    model.load_state_dict(checkpoint["model"], strict=True)
    loss.load_state_dict(checkpoint["criterion"], strict=True)
    torch.testing.assert_close(model(values), expected_output)
    torch.testing.assert_close(loss.proxies, checkpoint["criterion"]["proxies"])
    torch.testing.assert_close(
        model(values), torch.cat([model(values[i : i + 1]) for i in range(4)])
    )
    assert model(values).shape == (4, 16)


def test_hybrid_requires_architecture_and_global_label_mapping(encoder):
    loss = MHGLLoss({}, 2, 16)
    model = MotionRetrievalModel(
        encoder, representation_dimension=12, joints=2, embedding_dimension=16
    )
    with pytest.raises(ValueError, match="both intermediate"):
        loss.training_loss(model, poses(), torch.tensor([0, 0, 1, 1]))
    with pytest.raises(ValueError, match="globally"):
        loss(torch.randn(4, 16), torch.tensor([3, 3, 4, 4]))


@pytest.mark.parametrize("fault", ["rate", "mapping", "moment"])
def test_mhgl_checkpoint_requires_exact_named_optimizer_state(encoder, fault):
    from pose_embed.benchmark.mhgl import verify_mhgl_optimizer
    from pose_embed.benchmark.training import build_optimizer, resolve_recipe

    model = MotionRetrievalModel(
        encoder,
        method_id="mhgl",
        representation_dimension=12,
        embedding_dimension=16,
        joints=2,
    ).double()
    criterion = MHGLLoss({}, 2, 16).double()
    training = load_benchmark().training.model_copy(update={"encoder_mode": "finetune"})
    recipe = resolve_recipe("mhgl", {}, training, 8)
    optimizer = build_optimizer(model, criterion, recipe, "main")
    optimizer_step(model, criterion, optimizer, poses(), torch.tensor([0, 0, 1, 1]))
    checkpoint = _checkpoint_state(model, criterion, optimizer, recipe, 1, "main")
    checkpoint["selected_step"] = 1
    encoder_names = tuple(name for name, _ in encoder.named_parameters())
    verify_mhgl_optimizer(checkpoint, recipe, encoder_names)
    if fault == "rate":
        checkpoint["optimizer"]["param_groups"][2]["lr"] = 0.0001
    elif fault == "mapping":
        checkpoint["optimizer"]["param_groups"][1]["param_names"][0] = (
            "criterion.proxies"
        )
    else:
        del checkpoint["optimizer"]["state"][
            next(iter(checkpoint["optimizer"]["state"]))
        ]
    with pytest.raises(ValueError, match="optimizer"):
        verify_mhgl_optimizer(checkpoint, recipe, encoder_names)
