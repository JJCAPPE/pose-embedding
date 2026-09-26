"""Motion adaptation of licensed AVSL feature construction and graph inference.

Adapted from zbr17/AVSL revision fd2686e4f94a93da3c97c1b2067df9601f2803a0,
models/avsl_embedder.py and collectors/avsl_collector.py.
Copyright (c) 2021 Borui Zhang. MIT license: third_party/licenses/AVSL-MIT.txt.
Changes: motion depth capture, confidence masks, checkpointed initialization,
explicit training updates, attribution and immutable chunked retrieval scorer.
"""

from __future__ import annotations

import copy
import math
from contextlib import nullcontext
from typing import Literal

import numpy as np
import torch
import torch.nn.functional as F
from pydantic import Field
from torch import nn

from pose_embed.benchmark.config import StrictModel


class AVSLParameters(StrictModel):
    recipe: Literal["zhang2022_cub_motion_v1"] = "zhang2022_cub_motion_v1"
    depths: tuple[Literal[3], Literal[4], Literal[5]] = (3, 4, 5)
    temporal_bins: Literal[9] = 9
    topk: int = Field(default=128, ge=1)
    momentum: float = Field(default=0.5, ge=0, lt=1)
    probability_scale: float = Field(default=10.0, gt=0)
    proxy_alpha: float = Field(default=16.0, gt=0)
    positive_margin: float = Field(default=1.8, ge=0)
    negative_margin: float = Field(default=2.2, gt=0)
    level_weights: tuple[float, float, float] = (0.5, 1.0, 0.5)
    backbone_learning_rate: float = Field(default=1e-5, gt=0)
    head_learning_rate: float = Field(default=5.5e-4, gt=0)
    collector_learning_rate: float = Field(default=1.1e-4, gt=0)
    weight_decay: float = Field(default=1e-4, ge=0)
    warmup_epochs: int = Field(default=5, ge=0)
    decay_epochs: int = Field(default=10, ge=1)
    decay_factor: float = Field(default=0.5, gt=0, le=1)
    gradient_clip_norm: float = Field(default=10.0, gt=0)
    cam_normalization: Literal["source_row_min_l1_sample_std"] = (
        "source_row_min_l1_sample_std"
    )
    max_ties: Literal["first_valid_flat_index"] = "first_valid_flat_index"
    empty_relation: Literal["source_zero_column"] = "source_zero_column"


def motionbert_levels(encoder, poses, *, train_encoder):
    """One real DSTformer pass, with live fused depth-3/4 and final depth-5."""
    if poses.ndim != 5 or min(poses.shape) < 1 or poses.shape[-1] != 3:
        raise ValueError("AVSL requires nonempty [B,P,T,J,3] motion")
    if (
        len(getattr(encoder, "blocks_st", ())) != 5
        or len(getattr(encoder, "blocks_ts", ())) != 5
        or not getattr(encoder, "att_fuse", False)
    ):
        raise ValueError("AVSL requires the declared five-depth fused DSTformer")
    batch, people, frames, joints, channels = poses.shape
    captured = {3: [], 4: []}

    def capture(depth):
        def hook(_module, inputs):
            captured[depth].append(inputs[0])

        return hook

    hooks = [
        encoder.blocks_st[depth].register_forward_pre_hook(capture(depth))
        for depth in (3, 4)
    ]
    try:
        with nullcontext() if train_encoder else torch.no_grad():
            final = encoder.get_representation(
                poses.reshape(batch * people, frames, joints, channels)
            )
    finally:
        for hook in hooks:
            hook.remove()
    levels = []
    for depth in (3, 4):
        if len(captured[depth]) != 1 or captured[depth][0].shape != (
            batch * people * frames,
            joints,
            encoder.dim_feat,
        ):
            raise ValueError(
                "captured motion depth does not match declared architecture"
            )
        levels.append(captured[depth][0].reshape(batch, people, frames, joints, -1))
    if final.ndim != 4 or final.shape[:3] != (batch * people, frames, joints):
        raise ValueError("final motion representation must align with input tokens")
    return (*levels, final.reshape(batch, people, frames, joints, -1))


def motion_grid(features, valid, bins=9):
    """Disjoint normalized-time means; rows are person/bin, columns are joints."""
    if features.ndim != 5 or valid.shape != features.shape[:-1]:
        raise ValueError("motion features and confidence validity must align")
    if valid.dtype != torch.bool or valid.device != features.device:
        raise ValueError("validity must be boolean on the feature device")
    frames = features.shape[2]
    values, masks = [], []
    for i in range(bins):
        start, stop = i * frames // bins, (i + 1) * frames // bins
        mask = valid[:, :, start:stop]
        count = mask.sum(2)
        value = features[:, :, start:stop].masked_fill(~mask[..., None], 0).sum(2)
        values.append(value / count.clamp_min(1)[..., None])
        masks.append(count > 0)
    return torch.stack(values, 2).flatten(1, 2), torch.stack(masks, 2).flatten(1, 2)


def linearized_pool(features, valid):
    """Source first-max linearization, extended to confidence-valid tokens."""
    flat, mask = features.flatten(1, 2), valid.flatten(1, 2)
    count = mask.sum(1, keepdim=True)
    clean = flat.masked_fill(~mask[..., None], 0)
    maximum, index = flat.masked_fill(~mask[..., None], -torch.inf).max(1)
    maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
    spike = torch.zeros_like(flat).scatter(
        1, index[:, None, :], (maximum * count)[:, None, :]
    )
    linearized = (clean + spike).reshape_as(features)
    pooled = clean.sum(1) / count.clamp_min(1) + maximum
    return pooled, linearized


def cam_certainty(cams, valid):
    """Pinned source row-min/L1/unbiased-std convention, masking empty rows."""
    minimum = cams.masked_fill(~valid[..., None], torch.inf).amin(2, keepdim=True)
    minimum = torch.where(
        valid.any(2, keepdim=True)[..., None], minimum, torch.zeros_like(minimum)
    )
    shifted = (cams - minimum).masked_fill(~valid[..., None], 0).flatten(1, 2)
    normalized = F.normalize(shifted, p=1, dim=1)
    mask = valid.flatten(1, 2)[..., None]
    count = mask.sum(1)
    mean = normalized.sum(1) / count.clamp_min(1)
    variance = ((normalized - mean[:, None]).square() * mask).sum(1)
    return torch.sqrt(variance / (count - 1).clamp_min(1))


class AVSLInference(nn.Module):
    """Checkpointed relation graph, learned reliability and exact attribution."""

    def __init__(self, dimension, parameters=None):
        super().__init__()
        self.config = AVSLParameters.model_validate(parameters or {})
        if self.config.topk > dimension:
            raise ValueError("AVSL topk cannot exceed per-level dimension")
        self.dimension = dimension
        self.coefficient = nn.Parameter(torch.ones(2, dimension))
        self.bias = nn.Parameter(torch.zeros(2, dimension))
        self.register_buffer("relations", torch.zeros(2, dimension, dimension))
        self.register_buffer("updates", torch.zeros((), dtype=torch.long))

    @torch.no_grad()
    def update_relations(self, relations):
        if not self.training:
            raise ValueError("AVSL relation updates are training-only")
        if (
            relations.shape != self.relations.shape
            or not torch.isfinite(relations).all()
        ):
            raise ValueError("AVSL requires finite adjacent-level relation matrices")
        if self.updates.item() == 0:
            self.relations.copy_(relations)
        else:
            self.relations.lerp_(relations, 1 - self.config.momentum)
        self.updates.add_(1)

    def normalized_relations(self):
        links = self.relations.relu()
        # Source keeps every edge tied within 1e-8 of the kth largest.
        threshold = (
            links.topk(self.config.topk, dim=1).values.amin(1, keepdim=True) - 1e-8
        )
        selected = links * (links >= threshold)
        return selected / (selected.sum(1, keepdim=True) + 1e-8)

    def distances(self, first, second, cert_first, cert_second, *, attribution=False):
        """Input [N,3,D]; result [N,M], lower means closer. No state mutation."""
        if any(
            x.ndim != 3 or x.shape[1:] != (3, self.dimension) for x in (first, second)
        ):
            raise ValueError("AVSL requires three complete per-level descriptors")
        if cert_first.shape != first.shape or cert_second.shape != second.shape:
            raise ValueError("AVSL certainty and embedding shapes must match")
        nodes = (
            F.normalize(first, dim=-1)[:, None] - F.normalize(second, dim=-1)[None]
        ).square()
        links = self.normalized_relations()
        probabilities = torch.sigmoid(
            self.config.probability_scale
            * (
                cert_first[:, None, 1:] * cert_second[None, :, 1:] * self.coefficient
                + self.bias
            )
        )
        corrected = nodes[:, :, 0]
        for level in range(2):
            p = probabilities[:, :, level]
            corrected = p * nodes[:, :, level + 1] + (1 - p) * (
                corrected @ links[level]
            )
        distance = corrected.sum(-1)
        if not attribution:
            return distance
        influence = torch.ones_like(corrected)
        coefficients = [None, None, None]
        for level in (1, 0):
            p = probabilities[:, :, level]
            coefficients[level + 1] = influence * p
            influence = (influence * (1 - p)) @ links[level].T
        coefficients[0] = influence
        return distance, torch.stack(coefficients, dim=2), nodes


class AVSLHead(nn.Module):
    def __init__(
        self,
        local_dimension,
        global_dimension,
        embedding_dimension=1536,
        parameters=None,
    ):
        super().__init__()
        if embedding_dimension % 3 or embedding_dimension < 3:
            raise ValueError("AVSL stores three equal-sized level embeddings")
        self.dimension = embedding_dimension // 3
        self.config = AVSLParameters.model_validate(parameters or {})
        self.projections = nn.ModuleList(
            nn.Linear(channels, self.dimension)
            for channels in (local_dimension, local_dimension, global_dimension)
        )
        for projection in self.projections:
            nn.init.kaiming_normal_(projection.weight, mode="fan_out")
            nn.init.zeros_(projection.bias)
        self.inference = AVSLInference(self.dimension, self.config.model_dump())

    def construct(self, levels, valid, *, compute_relations=False):
        if len(levels) != 3:
            raise ValueError("AVSL needs three distinct encoder levels")
        embeddings, certainties, cams = [], [], []
        for features, projection in zip(levels, self.projections, strict=True):
            grid, mask = motion_grid(features, valid, self.config.temporal_bins)
            pooled, _ = linearized_pool(grid, mask)
            embedding = projection(pooled)
            embedding = embedding.masked_fill(~mask.any(dim=(1, 2))[:, None], 0)
            embeddings.append(F.normalize(embedding, dim=-1))
            # Published Eq.10: inference loss cannot update backbone/projections.
            with torch.no_grad():
                _, linearized = linearized_pool(grid.detach(), mask)
                cam = projection(linearized).masked_fill(~mask[..., None], 0)
                cams.append(cam)
                certainties.append(cam_certainty(cam, mask))
        descriptors = {
            "embeddings": torch.stack(embeddings, 1).flatten(1),
            "cam_std": torch.stack(certainties, 1),
        }
        if not compute_relations:
            return descriptors
        with torch.no_grad():
            normalized = [F.normalize(cam.flatten(1, 2), dim=1) for cam in cams]
            links = torch.stack(
                [
                    torch.einsum("bnc,bnd->cd", normalized[i], normalized[i + 1])
                    / len(valid)
                    for i in range(2)
                ]
            )
        return descriptors, links

    def forward_descriptors(self, levels, valid):
        return self.construct(levels, valid)

    def forward(self, *_args, **_kwargs):
        raise ValueError(
            "AVSL requires structured descriptors and its hierarchical scorer"
        )

    def make_retrieval_scorer(self, query, gallery):
        if self.inference.updates.item() == 0:
            raise ValueError("AVSL has no trained relation graph")
        snapshot = copy.deepcopy(self.inference).cpu().double().eval()
        snapshot.requires_grad_(False)
        device = snapshot.coefficient.device
        dtype = snapshot.coefficient.dtype

        def tensors(values):
            embeddings = np.asarray(values["embeddings"])
            certainty = np.asarray(values["cam_std"])
            if embeddings.ndim != 2 or embeddings.shape[1] != 3 * self.dimension:
                raise ValueError("AVSL retrieval descriptors require all three levels")
            if certainty.shape != (len(embeddings), 3, self.dimension):
                raise ValueError("AVSL retrieval descriptor certainty is missing")
            if not np.isfinite(embeddings).all() or not np.isfinite(certainty).all():
                raise ValueError("AVSL retrieval descriptors must be finite")
            return torch.tensor(embeddings, dtype=dtype).reshape(
                -1, 3, self.dimension
            ), torch.tensor(certainty, dtype=dtype)

        qe, qc = tensors(query)
        ge, gc = tensors(gallery)

        @torch.no_grad()
        def score_rows(query_indices, gallery_indices, excluded_gallery_indices=None):
            qids = np.asarray(query_indices, dtype=np.int64)
            gids = np.asarray(gallery_indices, dtype=np.int64)
            output = np.empty((len(qids), len(gids)), dtype=np.float64)
            # Bound the [Q,G,3,D] intermediates independently of evaluator chunks.
            for q in range(0, len(qids), 8):
                for g in range(0, len(gids), 128):
                    qi, gi = qids[q : q + 8], gids[g : g + 128]
                    value = snapshot.distances(
                        qe[qi].to(device),
                        ge[gi].to(device),
                        qc[qi].to(device),
                        gc[gi].to(device),
                    )
                    output[q : q + len(qi), g : g + len(gi)] = -value.cpu().numpy()
            return output

        return score_rows


def distance_proxy_anchor(
    distance, labels, *, alpha=16.0, positive_margin=1.8, negative_margin=2.2
):
    if labels.dtype != torch.long or labels.shape != (len(distance),):
        raise ValueError("AVSL requires one global int64 class label per descriptor")
    if (labels < 0).any() or (labels >= distance.shape[1]).any():
        raise ValueError("AVSL labels must use the global training class map")
    positive = F.one_hot(labels, distance.shape[1]).bool()

    def term(logits, mask):
        return torch.logsumexp(
            torch.cat(
                (
                    logits.masked_fill(~mask, -torch.inf),
                    logits.new_zeros(1, logits.shape[1]),
                ),
                dim=0,
            ),
            dim=0,
        )

    return (
        term(alpha * (distance - positive_margin), positive)[positive.any(0)].mean()
        + term(-alpha * (distance - negative_margin), ~positive).mean()
    )


class AVSLLoss(nn.Module):
    requires_feature_training = True

    def __init__(self, parameters, num_classes, embedding_dimension=1536):
        super().__init__()
        self.config = AVSLParameters.model_validate(parameters)
        if embedding_dimension % 3:
            raise ValueError("AVSL requires three equal projection dimensions")
        self.dimension = embedding_dimension // 3
        self.proxies = nn.Parameter(torch.empty(3, num_classes, self.dimension))
        for proxies in self.proxies:
            nn.init.kaiming_normal_(proxies, a=math.sqrt(5))

    def components(self, descriptors, labels, inference):
        embeddings = descriptors["embeddings"].reshape(-1, 3, self.dimension)
        certainty = descriptors["cam_std"].detach()
        proxies = F.normalize(self.proxies, dim=-1).transpose(0, 1)
        p = self.config

        def objective(distance):
            return distance_proxy_anchor(
                distance,
                labels,
                alpha=p.proxy_alpha,
                positive_margin=p.positive_margin,
                negative_margin=p.negative_margin,
            )

        level_losses = torch.stack(
            [
                objective(
                    (embeddings[:, None, level] - proxies[None, :, level])
                    .square()
                    .sum(-1)
                )
                for level in range(3)
            ]
        )
        # The source assigns every class proxy the batch's mean certainty per level.
        proxy_certainty = certainty.mean((0, 2))[None, :, None].expand_as(proxies)
        final_distance = inference.distances(
            embeddings.detach(), proxies.detach(), certainty, proxy_certainty
        )
        final_loss = objective(final_distance)
        construction = (level_losses * level_losses.new_tensor(p.level_weights)).sum()
        return {
            "levels": level_losses,
            "construction": construction,
            "inference": final_loss,
            "total": construction + final_loss,
        }

    def training_loss(self, model, poses, labels):
        if model.method_id != "proxy_anchor_avsl" or not isinstance(
            model.head, AVSLHead
        ):
            raise ValueError(
                "AVSL needs three-level construction and hierarchical inference"
            )
        if not model.training or not self.training:
            raise ValueError("AVSL relation updates require training mode")
        if model.head.config != self.config:
            raise ValueError(
                "AVSL head and objective must share the same locked recipe"
            )
        if (
            labels.shape != (len(poses),)
            or labels.dtype != torch.long
            or labels.device != poses.device
        ):
            raise ValueError("AVSL requires global int64 labels aligned with motion")
        if (labels < 0).any() or (labels >= self.proxies.shape[1]).any():
            raise ValueError("AVSL labels must use the global training class map")
        _, counts = labels.unique(return_counts=True)
        if len(counts) < 2 or (counts < 2).any():
            raise ValueError("AVSL requires two classes and two samples per class")
        levels = motionbert_levels(
            model.encoder, poses, train_encoder=model.train_encoder
        )
        descriptors, relations = model.head.construct(
            levels, poses[..., 2] > 0, compute_relations=True
        )
        model.head.inference.update_relations(relations)
        return self.components(descriptors, labels, model.head.inference)["total"]

    def clip_gradients(self, model):
        for parameters in (
            model.encoder.parameters(),
            model.head.projections.parameters(),
            [*model.head.inference.parameters(), *self.parameters()],
        ):
            nn.utils.clip_grad_norm_(parameters, self.config.gradient_clip_norm)

    def forward(self, *_args, **_kwargs):
        raise ValueError(
            "AVSL requires feature training and a learned hierarchical scorer"
        )


def optimizer_recipe(
    parameters, training, num_records, selection_num_records=None, *, profile=False
):
    p = AVSLParameters.model_validate(parameters)
    epoch_steps = math.ceil(num_records / training.physical_batch_size)
    final_steps = math.ceil(
        (selection_num_records or num_records) / training.physical_batch_size
    )
    return p.model_dump(mode="json") | {
        "optimizer": "AdamW",
        "named_optimizer_state": True,
        "optimizer_epsilon": 1e-8,
        "encoder_mode": training.encoder_mode,
        "epoch_steps": epoch_steps,
        "warmup_steps": p.warmup_epochs * epoch_steps,
        "minimum_selected_step": p.warmup_epochs * max(epoch_steps, final_steps) + 1,
        "main_optimizer_state": "preserved_after_warmup",
        "schedule": "source_total_epochs_step_decay",
        "profile_phase": "post_warmup_capacity" if profile else None,
        "profile_executes_warmup": False if profile else None,
    }


def build_avsl_optimizer(model, criterion, recipe):
    components = (
        ("encoder", model.encoder, "model.encoder.", recipe["backbone_learning_rate"]),
        (
            "projections",
            model.head.projections,
            "model.head.projections.",
            recipe["head_learning_rate"],
        ),
        (
            "inference",
            model.head.inference,
            "model.head.inference.",
            recipe["collector_learning_rate"],
        ),
        ("proxies", criterion, "criterion.", recipe["collector_learning_rate"]),
    )
    groups = []
    for name, module, prefix, rate in components:
        named = [
            (prefix + key, parameter)
            for key, parameter in module.named_parameters()
            if name != "encoder" or not key.startswith("head.")
        ]
        groups.append(
            {
                "name": name,
                "params": [p for _, p in named],
                "param_names": [n for n, _ in named],
                "lr": rate if name != "encoder" or model.train_encoder else 0.0,
            }
        )
    return torch.optim.AdamW(
        groups, eps=recipe["optimizer_epsilon"], weight_decay=recipe["weight_decay"]
    )


def learning_rates(recipe, step):
    elapsed = 0 if recipe["profile_phase"] is not None else max(0, step - 1)
    factor = recipe["decay_factor"] ** (
        elapsed // (recipe["epoch_steps"] * recipe["decay_epochs"])
    )
    active = recipe["encoder_mode"] == "finetune" and (
        recipe["profile_phase"] is not None or step > recipe["warmup_steps"]
    )
    return {
        "encoder": recipe["backbone_learning_rate"] * factor if active else 0.0,
        "projections": recipe["head_learning_rate"] * factor,
        "inference": recipe["collector_learning_rate"] * factor,
        "proxies": recipe["collector_learning_rate"] * factor,
    }


def verify_avsl_optimizer(checkpoint, recipe, encoder_parameters):
    from pose_embed.benchmark.optimizer_state import verify_named_adam
    from pose_embed.benchmark.training import phase_for_step

    step = checkpoint["selected_step"]
    phase = phase_for_step(recipe, step)
    profiling = recipe["profile_phase"] is not None
    main_steps = step if profiling else max(0, step - recipe["warmup_steps"])
    active = recipe["encoder_mode"] == "finetune" and phase == "main"
    if checkpoint.get("training_state") != {
        "phase": phase,
        "step": step,
        "warmup_updates": 0 if profiling else min(step, recipe["warmup_steps"]),
        "main_updates": main_steps,
        "encoder_trainable": active,
    }:
        raise ValueError("AVSL optimizer/warmup state differs")
    updates = checkpoint["model"]["head.inference.updates"]
    if updates.dtype != torch.long or updates.item() != step:
        raise ValueError("AVSL relation-update counter differs from selected step")
    rates = learning_rates(recipe, step)
    groups = []
    for name, names, count in (
        (
            "encoder",
            [
                "model.encoder." + key
                for key in encoder_parameters
                if not key.startswith("head.")
            ],
            main_steps if active else 0,
        ),
        (
            "projections",
            [
                "model." + key
                for key in checkpoint["model"]
                if key.startswith("head.projections.")
            ],
            step,
        ),
        (
            "inference",
            ["model.head.inference.coefficient", "model.head.inference.bias"],
            step,
        ),
        ("proxies", ["criterion.proxies"], step),
    ):
        groups.append(
            {
                "name": name,
                "param_names": names,
                "lr": rates[name],
                "weight_decay": recipe["weight_decay"],
                "updates": count,
            }
        )
    verify_named_adam(checkpoint, groups, epsilon=recipe["optimizer_epsilon"])
