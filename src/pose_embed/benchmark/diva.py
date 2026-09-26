"""Independent DiVA mathematics and declared motion conventions.

See docs/protocol/diva-motion-adaptation.md. The unlicensed upstream is an
audit reference only; no upstream source is copied or imported here.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field, model_validator
from torch import nn

from pose_embed.benchmark.config import StrictModel
from pose_embed.models.action_head import pool_action_features

TASKS = ("discriminative", "shared", "intra", "sample")


def training_identity(records, labels, stage) -> torch.Tensor:
    encoded = json.dumps(
        {
            "sample_ids": [record.sample_id for record in records],
            "labels": list(labels),
            "stage": stage,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return torch.tensor(list(hashlib.sha256(encoded).digest()), dtype=torch.uint8)


class DiVAParameters(StrictModel):
    recipe: Literal["milbich2020_cub_motion_corrected2021"] = (
        "milbich2020_cub_motion_corrected2021"
    )
    embedding_dimension: int = Field(default=512, gt=4)
    feature_dimension: int = Field(default=8704, gt=0)
    physical_batch_size: int = Field(default=32, ge=9)
    queue_batches: int = Field(default=30, gt=0)
    temperature: float = Field(default=0.1, gt=0)
    momentum: float = Field(default=0.9, ge=0, lt=1)
    margin: float = Field(default=0.2, gt=0)
    beta_initial: float = Field(default=1.2, gt=0)
    beta_learning_rate: float = Field(default=0.0005, gt=0)
    learning_rate: float = Field(default=0.00001, gt=0)
    weight_decay: float = Field(default=0.0005, ge=0)
    auxiliary_weight: float = Field(default=0.3, ge=0)
    decorrelation_weight: float = Field(default=1500, ge=0)
    decorrelation_hidden: int = Field(default=512, gt=0)
    distance_floor: float = Field(default=0.5, gt=0)
    distance_upper: float = Field(default=1.4, gt=0, lt=2)
    rotation_degrees: float = Field(default=5.0, ge=0, le=5)
    scale_delta: float = Field(default=0.1, ge=0, le=0.1)
    translation: float = Field(default=0.05, ge=0, le=0.05)

    @model_validator(mode="after")
    def dimensions_are_valid(self) -> DiVAParameters:
        if self.embedding_dimension % 4 or self.distance_floor >= self.distance_upper:
            raise ValueError(
                "DiVA needs four equal branches and ordered distance bounds"
            )
        return self

    @property
    def branch_dimension(self) -> int:
        return self.embedding_dimension // 4

    @property
    def queue_size(self) -> int:
        return self.physical_batch_size * self.queue_batches


class DiVAHead(nn.Module):
    """Four task projections with fixed CUB inference weighting."""

    def __init__(
        self, embedding_dimension: int, representation_dimension: int, joints: int
    ):
        super().__init__()
        if embedding_dimension % 4 or embedding_dimension <= 4:
            raise ValueError(
                "DiVA retrieval dimension must contain four equal branches"
            )
        self.input_dimension = representation_dimension * joints
        self.projections = nn.ModuleDict(
            {
                task: nn.Linear(self.input_dimension, embedding_dimension // 4)
                for task in TASKS
            }
        )

    def branches(self, features: torch.Tensor) -> dict[str, torch.Tensor]:
        pooled = pool_action_features(features)
        if pooled.shape[1] != self.input_dimension:
            raise ValueError("DiVA token dimension differs from its declared head")
        return {
            task: functional.normalize(layer(pooled), dim=-1)
            for task, layer in self.projections.items()
        }

    def forward_raw(self, features: torch.Tensor) -> torch.Tensor:
        branches = self.branches(features)
        return torch.cat(
            [
                branches[task] * (0.5 if task == "discriminative" else 1.0)
                for task in TASKS
            ],
            dim=1,
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.forward_raw(features), dim=-1)


class _Reverse(torch.autograd.Function):
    @staticmethod
    def forward(context, values):
        return values.view_as(values)

    @staticmethod
    def backward(context, gradient):
        return -gradient


def reverse_gradient(values: torch.Tensor) -> torch.Tensor:
    return _Reverse.apply(values)


def inverse_density_log(
    embeddings: torch.Tensor, candidates: torch.Tensor, floor: float
):
    unit = functional.normalize(embeddings.detach().double(), dim=-1)
    other = functional.normalize(candidates.detach().double(), dim=-1)
    distance = torch.cdist(unit, other).clamp_min(floor)
    sphere = (1 - distance.square() / 4).clamp_min(torch.finfo(unit.dtype).eps)
    dimension = embeddings.shape[-1]
    return (2 - dimension) * distance.log() - (
        dimension - 3
    ) / 2 * sphere.log(), distance


def corrected_dance_weights(
    query: torch.Tensor, memory: torch.Tensor, floor: float, upper: float
):
    """Author-2021 row-normalized inverse density, with explicit distance support."""
    log_density, distances = inverse_density_log(query, memory, floor)
    weights = (log_density - log_density.amax(dim=1, keepdim=True)).exp()
    weights = weights.masked_fill(distances > upper, 0).clamp_min(1e-45)
    return (weights / weights.sum(dim=1, keepdim=True)).to(query.dtype)


def dance_loss(
    query: torch.Tensor,
    positive: torch.Tensor,
    memory: torch.Tensor,
    config: DiVAParameters,
):
    query = functional.normalize(query, dim=-1)
    positive = functional.normalize(positive.detach(), dim=-1)
    memory = functional.normalize(memory.detach(), dim=-1)
    weights = corrected_dance_weights(
        query, memory, config.distance_floor, config.distance_upper
    )
    positive_logit = (query * positive).sum(dim=1, keepdim=True)
    negative_logits = (query @ memory.T) * weights
    logits = torch.cat((positive_logit, negative_logits), dim=1) / config.temperature
    return (torch.logsumexp(logits, dim=1) - logits[:, 0]).mean()


def task_triplets(embeddings, labels, task, generator, distance_floor):
    """The paper's class constraints, with no repeated item within a triplet."""
    classes, counts = labels.unique(return_counts=True)
    if len(classes) < 3 or (counts < 3).any():
        raise ValueError(
            "DiVA requires at least three classes and three samples per class"
        )
    labels = labels.detach().cpu()
    same = labels[:, None] == labels[None, :]
    same.fill_diagonal_(False)
    anchors = torch.arange(len(labels))
    density, _ = inverse_density_log(embeddings, embeddings, distance_floor)
    density = density.cpu()

    def draw(mask, weighted):
        probabilities = (
            density.masked_fill(~mask, -torch.inf).softmax(1)
            if weighted
            else mask.double()
        )
        return torch.multinomial(probabilities, 1, generator=generator).flatten()

    if task == "discriminative":
        positive = draw(same, False)
        negative = draw(labels[:, None] != labels[None, :], True)
    elif task == "shared":
        other = labels[:, None] != labels[None, :]
        positive = draw(other, True)
        negative = draw(other & (labels[None, :] != labels[positive, None]), True)
    elif task == "intra":
        positive = draw(same, False)
        remaining = same.clone()
        remaining[anchors, positive] = False
        negative = draw(remaining, False)
    else:
        raise ValueError("unknown DiVA triplet task")
    return torch.stack((anchors, positive, negative), dim=1).to(embeddings.device)


def margin_loss(embeddings, labels, triplets, beta, margin):
    anchor, positive, negative = triplets.unbind(1)
    positive_distance = (
        (embeddings[anchor] - embeddings[positive]).square().sum(1) + 1e-8
    ).sqrt()
    negative_distance = (
        (embeddings[anchor] - embeddings[negative]).square().sum(1) + 1e-8
    ).sqrt()
    boundary = beta[labels[anchor]]
    attractive = functional.relu(positive_distance - boundary + margin)
    repulsive = functional.relu(boundary - negative_distance + margin)
    active = torch.logical_or(attractive > 0, repulsive > 0).sum().clamp_min(1)
    return (attractive + repulsive).sum() / active


def motion_views(
    poses: torch.Tensor, generator: torch.Generator, config: DiVAParameters
):
    """Two whole-trajectory affine camera views preserving temporal/joint identity."""
    if poses.ndim != 5 or poses.shape[-1] != 3 or not torch.isfinite(poses).all():
        raise ValueError("DiVA views require finite [B,P,T,J,3] x/y/confidence poses")
    views = []
    for _ in range(2):
        random = torch.rand(len(poses), 4, generator=generator, dtype=torch.float64).to(
            poses
        )
        angle = (2 * random[:, 0] - 1) * config.rotation_degrees * math.pi / 180
        scale = 1 + (2 * random[:, 1] - 1) * config.scale_delta
        shift = (2 * random[:, 2:] - 1) * config.translation
        rotation = torch.stack(
            (angle.cos(), -angle.sin(), angle.sin(), angle.cos()), dim=1
        ).reshape(-1, 2, 2)
        coordinates = torch.einsum("bptjc,bdc->bptjd", poses[..., :2], rotation)
        coordinates = (
            coordinates * scale[:, None, None, None, None]
            + shift[:, None, None, None, :]
        )
        view = poses.clone()
        view[..., :2] = torch.where(poses[..., 2:3] > 0, coordinates, poses[..., :2])
        views.append(view)
    return tuple(views)


class DiVALoss(nn.Module):
    requires_feature_training = True

    def __init__(self, config: DiVAParameters, num_classes: int):
        super().__init__()
        self.config = config
        self.num_classes = num_classes
        self.boundaries = nn.ParameterDict(
            {
                task: nn.Parameter(torch.full((num_classes,), config.beta_initial))
                for task in TASKS[:3]
            }
        )
        self.decorators = nn.ModuleDict(
            {
                task: nn.Sequential(
                    nn.Linear(config.branch_dimension, config.decorrelation_hidden),
                    nn.ReLU(),
                    nn.Linear(config.decorrelation_hidden, config.branch_dimension),
                )
                for task in TASKS[1:]
            }
        )
        self.register_buffer(
            "queue", torch.zeros(config.queue_size, config.branch_dimension)
        )
        self.register_buffer(
            "queue_indices", torch.full((config.queue_size,), -1, dtype=torch.long)
        )
        self.register_buffer(
            "queue_labels", torch.full((config.queue_size,), -1, dtype=torch.long)
        )
        self.register_buffer("queue_position", torch.zeros((), dtype=torch.long))
        self.register_buffer("queue_count", torch.zeros((), dtype=torch.long))
        self.register_buffer("completed_steps", torch.zeros((), dtype=torch.long))
        self.register_buffer("training_identity", torch.zeros(32, dtype=torch.uint8))
        self.register_buffer(
            "rng_state", torch.Generator().manual_seed(torch.initial_seed()).get_state()
        )
        self.register_buffer(
            "training_labels", torch.empty(0, dtype=torch.long), persistent=False
        )
        self._batch_indices = None
        self._pending = None

    def configure_training(self, records, labels, stage):
        expected = {"development": "development_train", "final": "final_train"}.get(
            stage
        )
        if (
            expected is None
            or not records
            or any(record.split != expected for record in records)
        ):
            raise ValueError(
                "DiVA memory must use only the verified current training partition"
            )
        if len(records) != len(labels) or len(
            {record.sample_id for record in records}
        ) != len(records):
            raise ValueError("DiVA training identities and labels must align uniquely")
        mapping = {
            action: index
            for index, action in enumerate(
                sorted({record.ntu.action for record in records})
            )
        }
        if (
            list(labels) != [mapping[record.ntu.action] for record in records]
            or len(mapping) != self.num_classes
        ):
            raise ValueError("DiVA queue requires the global training action mapping")
        identity = training_identity(records, labels, stage).to(
            self.training_identity.device
        )
        if self.training_identity.any() and not torch.equal(
            identity, self.training_identity
        ):
            raise ValueError("DiVA memory cannot change its bound training partition")
        self.training_identity.copy_(identity)
        self.training_labels = torch.tensor(
            labels, dtype=torch.long, device=self.queue.device
        )

    def _indices(self, indices):
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.queue.device)
        if (
            indices.shape != (self.config.physical_batch_size,)
            or not self.training_labels.numel()
            or (indices < 0).any()
            or (indices >= len(self.training_labels)).any()
            or len(indices.unique()) != len(indices)
        ):
            raise ValueError(
                "DiVA memory indices must identify one physical training batch"
            )
        return indices

    def _generator(self):
        return torch.Generator().set_state(self.rng_state.cpu())

    def _save_generator(self, generator):
        self.rng_state.copy_(generator.get_state().to(self.rng_state.device))

    def _enqueue(self, keys, indices):
        positions = (
            torch.arange(len(keys), device=self.queue.device) + self.queue_position
        ) % self.config.queue_size
        self.queue[positions] = keys.detach()
        self.queue_indices[positions] = indices
        self.queue_labels[positions] = self.training_labels[indices]
        self.queue_position.copy_(
            (self.queue_position + len(keys)) % self.config.queue_size
        )
        self.queue_count.copy_(
            (self.queue_count + len(keys)).clamp_max(self.config.queue_size)
        )

    @torch.no_grad()
    def bootstrap(self, model, poses, indices):
        indices = self._indices(indices)
        if (
            self.completed_steps.item()
            or self.queue_count.item() == self.config.queue_size
        ):
            raise ValueError("DiVA memory bootstrap is immutable once filled")
        if len(poses) != len(indices):
            raise ValueError("DiVA bootstrap poses and training indices must align")
        generator = self._generator()
        _, view = motion_views(poses, generator, self.config)
        keys = model.momentum_embedding(view)
        self._enqueue(keys, indices)
        self._save_generator(generator)

    def set_training_batch(self, indices):
        if self._pending is not None:
            raise ValueError("DiVA previous update has not completed")
        self._batch_indices = self._indices(indices)

    def objective_components(self, branches, labels, keys, generator):
        losses = {}
        for task in TASKS[:3]:
            triplets = task_triplets(
                branches[task], labels, task, generator, self.config.distance_floor
            )
            losses[task] = margin_loss(
                branches[task],
                labels,
                triplets,
                self.boundaries[task],
                self.config.margin,
            )
        losses["sample"] = dance_loss(
            branches["sample"], keys, self.queue.clone(), self.config
        )
        disc = reverse_gradient(branches["discriminative"])
        terms = []
        for task, network in self.decorators.items():
            mapped = functional.normalize(
                network(reverse_gradient(branches[task])), dim=-1
            )
            terms.append((disc * mapped).square().mean())
        losses["decorrelation"] = (
            -self.config.decorrelation_weight * torch.stack(terms).sum()
        )
        return losses

    def training_loss(self, model, poses, labels):
        if not self.training or not model.training:
            raise ValueError("DiVA memory updates are forbidden during evaluation")
        if (
            self.queue_count.item() != self.config.queue_size
            or self._batch_indices is None
        ):
            raise ValueError(
                "DiVA requires a bootstrapped training queue and bound batch"
            )
        if (
            len(poses) != self.config.physical_batch_size
            or labels.dtype != torch.long
            or not torch.equal(labels, self.training_labels[self._batch_indices])
        ):
            raise ValueError("DiVA labels differ from the bound training identities")
        if self._pending is not None:
            raise ValueError("DiVA optimizer update must finish before another forward")
        generator = self._generator()
        query_view, key_view = motion_views(poses, generator, self.config)
        branches = model.head.branches(model.forward_features(query_view))
        with torch.no_grad():
            keys = model.momentum_embedding(key_view)
        parts = self.objective_components(branches, labels, keys, generator)
        self._pending = (keys.detach(), self._batch_indices.clone())
        self._save_generator(generator)
        return (
            parts["discriminative"]
            + self.config.auxiliary_weight * sum(parts[task] for task in TASKS[1:])
            + parts["decorrelation"]
        )

    @torch.no_grad()
    def after_optimizer_step(self, model):
        if self._pending is None:
            raise ValueError("DiVA requires a training forward before committing state")
        model.update_momentum(self.config.momentum)
        self._enqueue(*self._pending)
        self.completed_steps.add_(1)
        self._pending = None
        self._batch_indices = None

    def parameter_groups(self, learning_rate, weight_decay):
        return [
            {
                "name": "diva_decorrelation",
                "params": list(self.decorators.parameters()),
                "lr": learning_rate,
                "weight_decay": weight_decay,
            },
            {
                "name": "diva_boundaries",
                "params": list(self.boundaries.parameters()),
                "lr": self.config.beta_learning_rate,
                "weight_decay": 0.0,
            },
        ]

    def validate_checkpoint_state(self, state, selected_step):
        for name, expected in {
            "completed_steps": selected_step,
            "queue_count": self.config.queue_size,
            "queue_position": (selected_step * self.config.physical_batch_size)
            % self.config.queue_size,
        }.items():
            if state[name].dtype != torch.long or state[name].item() != expected:
                raise ValueError(
                    "DiVA memory counter or position differs from selected update"
                )
        if not torch.allclose(
            state["queue"].norm(dim=1),
            torch.ones_like(state["queue"].norm(dim=1)),
            atol=1e-5,
            rtol=1e-5,
        ):
            raise ValueError("DiVA memory keys must be unit embeddings")
        if (
            state["queue_indices"].dtype != torch.long
            or (state["queue_indices"] < 0).any()
            or state["queue_labels"].dtype != torch.long
            or (state["queue_labels"] < 0).any()
            or (state["queue_labels"] >= self.num_classes).any()
        ):
            raise ValueError("DiVA memory identities/labels are invalid")
        try:
            if state["rng_state"].dtype != torch.uint8:
                raise ValueError("DiVA sampling state must contain bytes")
            torch.Generator().set_state(state["rng_state"].cpu())
        except RuntimeError as exc:
            raise ValueError("DiVA sampling state is invalid") from exc
