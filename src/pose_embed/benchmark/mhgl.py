"""Independent MHGL architecture and printed Eqs. 1–7 (Ebrahimpour et al., 2022).

No MHGL upstream code is reused. See docs/protocol/mhgl-motion.md for the
explicit depth, token-grid, masking, initialization and equation conventions.
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import Literal

import torch
import torch.nn.functional as F
from pydantic import Field
from torch import nn

from pose_embed.benchmark.config import StrictModel


class MHGLParameters(StrictModel):
    recipe: Literal["ebrahimpour2022_printed_equations_motion_v1"] = (
        "ebrahimpour2022_printed_equations_motion_v1"
    )
    local_depth: Literal[4] = 4
    global_depth: Literal[5] = 5
    local_temporal_bins: Literal[9] = 9
    global_temporal_bins: Literal[3] = 3
    attention_scale: Literal[1.0] = 1.0
    attention_projection: Literal["full_input_channels"] = "full_input_channels"
    positive_scale: float = Field(default=2.0, gt=0)
    negative_scale: float = Field(default=50.0, gt=0)
    similarity_margin: float = Field(default=1.0, ge=0)
    negative_margin_convention: Literal["printed_similarity_plus_sigma"] = (
        "printed_similarity_plus_sigma"
    )
    miner: Literal["none_all_label_pairs"] = "none_all_label_pairs"
    proxy_alpha: float = Field(default=32.0, gt=0)
    proxy_margin: float = Field(default=0.1, ge=0)
    proxy_loss_weight: float = Field(default=0.03, ge=0)
    proxy_initial_std: float = Field(default=1.0, gt=0)
    backbone_learning_rate: float = Field(default=1e-4, gt=0)
    head_learning_rate: float = Field(default=1e-4, gt=0)
    proxy_learning_rate: float = Field(default=1e-2, gt=0)
    initialization: Literal["xavier_uniform_zero_bias"] = "xavier_uniform_zero_bias"
    masking: Literal["confidence_positive_empty_zero"] = (
        "confidence_positive_empty_zero"
    )


def motionbert_levels(encoder, poses, *, train_encoder):
    """One pinned DSTformer pass; capture the fused depth-4 input to depth 5.

    The temporary hook preserves the computation graph. It is removed even if
    the encoder fails. The final output follows norm + pre_logits as upstream.
    """
    if poses.ndim != 5 or any(size == 0 for size in poses.shape):
        raise ValueError("poses must be nonempty [B,P,T,J,3]")
    if poses.shape[-1] != 3:
        raise ValueError("MHGL requires x, y and confidence")
    if (
        not hasattr(encoder, "blocks_st")
        or not hasattr(encoder, "blocks_ts")
        or len(encoder.blocks_st) != 5
        or len(encoder.blocks_ts) != 5
        or not getattr(encoder, "att_fuse", False)
    ):
        raise ValueError("MHGL requires the declared five-depth fused DSTformer")
    batch, people, frames, joints, channels = poses.shape
    captured = []

    def capture(_module, inputs):
        captured.append(inputs[0])

    hook = encoder.blocks_st[4].register_forward_pre_hook(capture)
    try:
        with nullcontext() if train_encoder else torch.no_grad():
            final = encoder.get_representation(
                poses.reshape(batch * people, frames, joints, channels)
            )
    finally:
        hook.remove()
    if len(captured) != 1 or captured[0].shape != (
        batch * people * frames,
        joints,
        encoder.dim_feat,
    ):
        raise ValueError(
            "DSTformer local feature capture does not match its architecture"
        )
    if final.ndim != 4 or final.shape[:3] != (batch * people, frames, joints):
        raise ValueError("DSTformer global feature grid does not align with inputs")
    return (
        captured[0].reshape(batch, people, frames, joints, encoder.dim_feat),
        final.reshape(batch, people, frames, joints, -1),
    )


def temporal_tokens(features, valid_mask, bins):
    """Non-overlapping normalized-time bin means; retain each person and joint."""
    if features.ndim != 5 or valid_mask.shape != features.shape[:-1]:
        raise ValueError("feature maps and confidence masks must align")
    if valid_mask.dtype != torch.bool or valid_mask.device != features.device:
        raise ValueError("validity must be boolean on the feature device")
    frames = features.shape[2]
    values, masks = [], []
    for index in range(bins):
        start, stop = index * frames // bins, (index + 1) * frames // bins
        valid = valid_mask[:, :, start:stop, :]
        count = valid.sum(dim=2)
        summed = (
            features[:, :, start:stop, :, :]
            .masked_fill(~valid[..., None], 0)
            .sum(dim=2)
        )
        values.append(summed / count.clamp_min(1)[..., None])
        masks.append(count > 0)
    return torch.stack(values, dim=2).flatten(1, 3), torch.stack(masks, dim=2).flatten(
        1, 3
    )


def _initialize(module):
    if isinstance(module, nn.Linear):
        nn.init.xavier_uniform_(module.weight)
        if module.bias is not None:
            nn.init.zeros_(module.bias)


class SecondOrderAttention(nn.Module):
    """Paper Eq. 1–2 with scale 1 (no transformer sqrt(d) normalization)."""

    def __init__(self, channels):
        super().__init__()
        self.query = nn.Linear(channels, channels)
        self.key = nn.Linear(channels, channels)
        self.value = nn.Linear(channels, channels)
        self.output = nn.Linear(channels, channels)
        self.apply(_initialize)

    def attention_weights(self, tokens, valid_mask):
        if tokens.ndim != 3 or valid_mask.shape != tokens.shape[:2]:
            raise ValueError("attention requires [B,N,C] tokens and [B,N] validity")
        logits = self.query(tokens) @ self.key(tokens).transpose(-1, -2)
        logits = logits.masked_fill(
            ~valid_mask[:, None, :], torch.finfo(logits.dtype).min
        )
        # All-empty maps stay finite and have exact zero attention mass.
        return logits.softmax(dim=-1) * valid_mask[:, None, :] * valid_mask[:, :, None]

    def forward(self, tokens, valid_mask):
        attention = self.attention_weights(tokens, valid_mask)
        refined = tokens + self.output(attention @ self.value(tokens))
        return refined.masked_fill(~valid_mask[..., None], 0)


class MHGLHead(nn.Module):
    """Separate local/global SOA, average+max, 256+256 projection, unit concat."""

    def __init__(self, *, local_dimension, global_dimension, embedding_dimension=512):
        super().__init__()
        if embedding_dimension < 2 or embedding_dimension % 2:
            raise ValueError("MHGL concatenates two equal embedding halves")
        self.local_attention = SecondOrderAttention(local_dimension)
        self.global_attention = SecondOrderAttention(global_dimension)
        self.local_projection = nn.Linear(local_dimension, embedding_dimension // 2)
        self.global_projection = nn.Linear(global_dimension, embedding_dimension // 2)
        self.local_projection.apply(_initialize)
        self.global_projection.apply(_initialize)

    @staticmethod
    def _pool(tokens, valid):
        count = valid.sum(dim=1, keepdim=True)
        mean = tokens.masked_fill(~valid[..., None], 0).sum(dim=1) / count.clamp_min(1)
        maximum = tokens.masked_fill(~valid[..., None], -torch.inf).amax(dim=1)
        maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
        return mean + maximum

    def branch_features(self, levels, valid_mask):
        local, lmask = temporal_tokens(levels[0], valid_mask, 9)
        global_, gmask = temporal_tokens(levels[1], valid_mask, 3)
        local = self.local_attention(local, lmask)
        global_ = self.global_attention(global_, gmask)
        return (
            self.local_projection(self._pool(local, lmask)),
            self.global_projection(self._pool(global_, gmask)),
        )

    def forward_raw(self, levels, valid_mask):
        return torch.cat(self.branch_features(levels, valid_mask), dim=-1)

    def forward(self, levels, valid_mask):
        return F.normalize(self.forward_raw(levels, valid_mask), dim=-1)


def _log1psumexp(logits, mask, dim):
    shape = list(logits.shape)
    shape[dim] = 1
    return torch.logsumexp(
        torch.cat(
            [logits.masked_fill(~mask, -torch.inf), logits.new_zeros(shape)], dim=dim
        ),
        dim=dim,
    )


class MHGLLoss(nn.Module):
    """Eq. 5–7 on the full architecture's concatenated descriptor."""

    requires_feature_training = True

    def __init__(self, parameters, num_classes, embedding_dimension=512):
        super().__init__()
        self.config = MHGLParameters.model_validate(parameters)
        self.num_classes = num_classes
        self.embedding_dimension = embedding_dimension
        self.proxies = nn.Parameter(
            torch.randn(num_classes, embedding_dimension)
            * self.config.proxy_initial_std
        )

    def components(self, embeddings, labels):
        if embeddings.ndim != 2 or embeddings.shape[1] != self.embedding_dimension:
            raise ValueError("MHGL embedding dimension does not match proxies")
        if (
            labels.shape != (len(embeddings),)
            or labels.dtype != torch.long
            or labels.device != embeddings.device
        ):
            raise ValueError("global int64 labels must align with embeddings")
        if (labels < 0).any() or (labels >= self.num_classes).any():
            raise ValueError("map action labels globally into [0,num_classes)")
        _, counts = labels.unique(return_counts=True)
        if len(counts) < 2 or (counts < 2).any():
            raise ValueError(
                "MHGL requires at least two classes and two samples per class"
            )
        x = F.normalize(embeddings, dim=-1)
        similarity = x @ x.T
        same = labels[:, None] == labels[None, :]
        positive = same & ~torch.eye(
            len(labels), dtype=torch.bool, device=labels.device
        )
        negative = ~same
        p = self.config
        ms = (
            _log1psumexp(
                -p.positive_scale * (similarity - p.similarity_margin), positive, 1
            )
            / p.positive_scale
            + _log1psumexp(
                p.negative_scale * (similarity + p.similarity_margin), negative, 1
            )
            / p.negative_scale
        ).mean()
        proxy_similarity = x @ F.normalize(self.proxies, dim=-1).T
        targets = F.one_hot(labels, self.num_classes).bool()
        pa_positive = _log1psumexp(
            -p.proxy_alpha * (proxy_similarity - p.proxy_margin), targets, 0
        )
        pa_negative = _log1psumexp(
            p.proxy_alpha * (proxy_similarity + p.proxy_margin), ~targets, 0
        )
        pa = pa_positive.sum() / targets.any(dim=0).sum() + pa_negative.mean()
        return {
            "multi_similarity": ms,
            "proxy_anchor": pa,
            "total": ms + p.proxy_loss_weight * pa,
        }

    def forward(self, embeddings, labels):
        return self.components(embeddings, labels)["total"]

    def training_loss(self, model, poses, labels):
        if model.method_id != "mhgl" or not isinstance(model.head, MHGLHead):
            raise ValueError(
                "MHGL requires both intermediate feature branches and SOA heads"
            )
        return self(model(poses), labels)


def optimizer_recipe(parameters, training, *, profile=False):
    """Published fast proxies, with the benchmark's declared budget and decay."""
    config = MHGLParameters.model_validate(parameters)
    return config.model_dump(mode="json") | {
        "optimizer": "AdamW",
        "optimizer_epsilon": 1e-8,
        "weight_decay": training.weight_decay,
        "encoder_mode": training.encoder_mode,
        "warmup_steps": 0,
        "minimum_selected_step": 1,
        "schedule": "benchmark_steps_validation_r_at_1_selection",
        "profile_phase": "main_capacity" if profile else None,
    }


def build_mhgl_optimizer(model, criterion, recipe):
    """Persist distinct backbone/head/proxy learning rates and parameter names."""
    groups = []
    for name, module, prefix, rate in (
        ("encoder", model.encoder, "model.encoder.", recipe["backbone_learning_rate"]),
        ("head", model.head, "model.head.", recipe["head_learning_rate"]),
        ("proxies", criterion, "criterion.", recipe["proxy_learning_rate"]),
    ):
        named = [
            (prefix + key, value)
            for key, value in module.named_parameters()
            if name != "encoder" or not key.startswith("head.")
        ]
        groups.append(
            {
                "name": name,
                "params": [value for _, value in named],
                "param_names": [key for key, _ in named],
                "lr": rate if name != "encoder" or model.train_encoder else 0.0,
            }
        )
    return torch.optim.AdamW(
        groups, eps=recipe["optimizer_epsilon"], weight_decay=recipe["weight_decay"]
    )


def verify_mhgl_optimizer(checkpoint, recipe, encoder_parameters):
    from pose_embed.benchmark.optimizer_state import verify_named_adam

    step = checkpoint["selected_step"]
    active = recipe["encoder_mode"] == "finetune"
    if checkpoint.get("training_state") != {
        "phase": "main",
        "step": step,
        "warmup_updates": 0,
        "main_updates": step,
        "encoder_trainable": active,
    }:
        raise ValueError("MHGL optimizer phase state differs")
    groups = []
    for name, names, rate, updates in (
        (
            "encoder",
            [
                "model.encoder." + k
                for k in encoder_parameters
                if not k.startswith("head.")
            ],
            recipe["backbone_learning_rate"] if active else 0.0,
            step if active else 0,
        ),
        (
            "head",
            ["model." + k for k in checkpoint["model"] if k.startswith("head.")],
            recipe["head_learning_rate"],
            step,
        ),
        ("proxies", ["criterion.proxies"], recipe["proxy_learning_rate"], step),
    ):
        groups.append(
            {
                "name": name,
                "param_names": names,
                "lr": rate,
                "weight_decay": recipe["weight_decay"],
                "updates": updates,
            }
        )
    verify_named_adam(checkpoint, groups, epsilon=recipe["optimizer_epsilon"])
