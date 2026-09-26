"""Independent R-Margin + MSDFA implementation from Roth et al. (ICML 2021).

The explicit source conventions and motion pooling adaptation are recorded in
docs/protocol/s2sd-motion-adaptation.md. No upstream code is imported or copied.
"""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field, model_validator
from torch import nn

from pose_embed.benchmark.config import StrictModel


class S2SDParameters(StrictModel):
    recipe: Literal["roth2021_rmargin_msdfa_cub_motion"] = (
        "roth2021_rmargin_msdfa_cub_motion"
    )
    embedding_dimension: int = Field(default=512, gt=1)
    feature_dimension: int = Field(default=8704, gt=1)
    target_dimensions: tuple[int, ...] = (512, 1024, 1536, 2048)
    temperature: float = Field(default=1.0, gt=0)
    distillation_weight: float = Field(default=50.0, ge=0)
    feature_weight: float = Field(default=50.0, ge=0)
    feature_delay: int = Field(default=1000, ge=0)
    margin: float = Field(default=0.2, gt=0)
    beta_initial: float = Field(default=1.2, gt=0)
    beta_learning_rate: float = Field(default=0.0005, gt=0)
    switch_probability: float = Field(default=0.4, ge=0, le=1)
    distance_floor: float = Field(default=0.5, gt=0, lt=2)

    @model_validator(mode="after")
    def teacher_dimensions_are_ordered(self) -> S2SDParameters:
        dimensions = self.target_dimensions
        if (
            len(dimensions) != 4
            or tuple(sorted(set(dimensions))) != dimensions
            or dimensions[0] < self.embedding_dimension
        ):
            raise ValueError(
                "S2SD requires four increasing teacher dimensions >= student"
            )
        return self


def distance_weighted_probabilities(
    embeddings: torch.Tensor, labels: torch.Tensor, distance_floor: float = 0.5
) -> torch.Tensor:
    """Detached inverse hypersphere density over other-class candidates.

    The source's 1.4 upper cutoff is inactive. The sphere endpoint is bounded
    only at machine epsilon to keep antipodal vectors numerically defined.
    """
    unit = functional.normalize(embeddings.detach().double(), dim=-1)
    distances = torch.cdist(unit, unit).clamp_min(distance_floor)
    dimension = embeddings.shape[1]
    sphere = (1 - distances.square() / 4).clamp_min(torch.finfo(unit.dtype).eps)
    log_weights = (2 - dimension) * distances.log() - (dimension - 3) / 2 * sphere.log()
    negative = labels[:, None] != labels[None, :]
    if not negative.any(dim=1).all():
        raise ValueError("R-Margin requires a negative candidate for every anchor")
    return log_weights.masked_fill(~negative, -torch.inf).softmax(dim=1)


class RegularizedMarginLoss(nn.Module):
    """Distance-weighted R-Margin, with a private checkpointed sampling stream."""

    def __init__(self, config: S2SDParameters, num_classes: int, seed: int):
        super().__init__()
        self.config = config
        self.beta = nn.Parameter(torch.full((num_classes,), config.beta_initial))
        self.register_buffer(
            "rng_state", torch.Generator().manual_seed(seed).get_state()
        )

    def sample_triplets(
        self, embeddings: torch.Tensor, labels: torch.Tensor
    ) -> torch.Tensor:
        labels_cpu = labels.detach().cpu()
        positive = labels_cpu[:, None] == labels_cpu[None, :]
        positive.fill_diagonal_(False)
        if not positive.any(dim=1).all():
            raise ValueError("R-Margin requires another same-class sample per anchor")
        probabilities = distance_weighted_probabilities(
            embeddings, labels, self.config.distance_floor
        ).cpu()
        generator = torch.Generator().set_state(self.rng_state.cpu())
        anchors = torch.arange(len(labels))
        selected_positive = torch.multinomial(
            positive.double(), 1, generator=generator
        ).flatten()
        selected_negative = torch.multinomial(
            probabilities, 1, generator=generator
        ).flatten()
        switched = (
            torch.rand(len(labels), generator=generator)
            < self.config.switch_probability
        )
        # R-Margin's switch pushes a within-class pair apart: the positive slot
        # becomes the anchor itself, while a distinct positive is used as negative.
        negatives = torch.where(switched, selected_positive, selected_negative)
        positives = torch.where(switched, anchors, selected_positive)
        if self.training:
            self.rng_state.copy_(generator.get_state().to(self.rng_state.device))
        return torch.stack((anchors, positives, negatives), dim=1).to(labels.device)

    def sampled_loss(
        self, embeddings: torch.Tensor, labels: torch.Tensor, triplets: torch.Tensor
    ) -> torch.Tensor:
        anchor, positive, negative = triplets.unbind(dim=1)
        positive_distance = (
            (embeddings[anchor] - embeddings[positive]).square().sum(1) + 1e-8
        ).sqrt()
        negative_distance = (
            (embeddings[anchor] - embeddings[negative]).square().sum(1) + 1e-8
        ).sqrt()
        boundaries = self.beta[labels[anchor]]
        attractive = functional.relu(
            positive_distance - boundaries + self.config.margin
        )
        repulsive = functional.relu(boundaries - negative_distance + self.config.margin)
        # The audited PyTorch>=1.2 source adds boolean tensors before sum:
        # it counts active triplets (union), not two active pairs per triplet.
        count = torch.logical_or(attractive > 0, repulsive > 0).sum().clamp_min(1)
        return (attractive + repulsive).sum() / count

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        unit = functional.normalize(embeddings, dim=-1)
        return self.sampled_loss(unit, labels, self.sample_triplets(unit, labels))


def similarity_distillation(
    student: torch.Tensor, teacher: torch.Tensor, temperature: float
) -> torch.Tensor:
    """Row-wise KL(teacher || student), including self, T²-scaled batch mean."""
    source = functional.normalize(student, dim=-1)
    target = functional.normalize(teacher.detach(), dim=-1)
    source_log_probability = functional.log_softmax(
        source @ source.T / temperature, dim=1
    )
    target_probability = functional.softmax(target @ target.T / temperature, dim=1)
    return (
        functional.kl_div(source_log_probability, target_probability, reduction="sum")
        * temperature**2
        / len(student)
    )


def auxiliary_features(
    features: torch.Tensor, valid_mask: torch.Tensor
) -> torch.Tensor:
    """Per-joint valid temporal/person mean plus max, flattened as the common head."""
    if features.ndim != 5 or valid_mask.shape != features.shape[:-1]:
        raise ValueError(
            "S2SD requires token features [B,P,T,J,C] and aligned confidence mask"
        )
    if valid_mask.dtype != torch.bool or valid_mask.device != features.device:
        raise ValueError("S2SD validity mask must be boolean on the feature device")
    count = valid_mask.sum(dim=(1, 2))
    mean = (features * valid_mask[..., None]).sum(dim=(1, 2)) / count.clamp_min(1)[
        ..., None
    ]
    maximum = features.masked_fill(~valid_mask[..., None], -torch.inf).amax(dim=(1, 2))
    maximum = torch.where(count[..., None] > 0, maximum, 0)
    return (mean + maximum).flatten(start_dim=1)


class S2SDLoss(nn.Module):
    """Training-only four-teacher MSDFA; retrieval remains the common student."""

    requires_feature_training = True

    def __init__(self, config: S2SDParameters, num_classes: int):
        super().__init__()
        self.config = config
        self.num_classes = num_classes
        self.teachers = nn.ModuleList(
            nn.Sequential(
                nn.Linear(config.feature_dimension, dimension),
                nn.ReLU(),
                nn.Linear(dimension, dimension),
            )
            for dimension in config.target_dimensions
        )
        seed = torch.initial_seed()
        criteria = [
            RegularizedMarginLoss(
                config, num_classes, (seed + index * 2654435761) % (2**63)
            )
            for index in range(5)
        ]
        self.student_objective = criteria[0]
        self.teacher_objectives = nn.ModuleList(criteria[1:])
        self.register_buffer("completed_steps", torch.zeros((), dtype=torch.long))

    def parameter_groups(self, learning_rate: float, weight_decay: float) -> list[dict]:
        return [
            {
                "params": list(self.teachers.parameters()),
                "lr": learning_rate,
                "weight_decay": weight_decay,
                "name": "s2sd_teachers",
            },
            {
                "params": [
                    self.student_objective.beta,
                    *(loss.beta for loss in self.teacher_objectives),
                ],
                "lr": self.config.beta_learning_rate,
                "weight_decay": 0.0,
                "name": "s2sd_boundaries",
            },
        ]

    def loss_components(
        self, student: torch.Tensor, labels: torch.Tensor, pooled: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        if student.ndim != 2 or student.shape[1] != self.config.embedding_dimension:
            raise ValueError("S2SD student embedding dimension differs from its recipe")
        if pooled.shape != (len(student), self.config.feature_dimension):
            raise ValueError("S2SD auxiliary feature dimension differs from its recipe")
        if (
            labels.shape != (len(student),)
            or labels.dtype != torch.long
            or labels.device != student.device
        ):
            raise ValueError("S2SD needs aligned int64 labels on the embedding device")
        if (
            labels.numel() == 0
            or (labels < 0).any()
            or (labels >= self.num_classes).any()
        ):
            raise ValueError("map S2SD action labels globally into [0, num_classes)")
        if not torch.isfinite(student).all() or not torch.isfinite(pooled).all():
            raise ValueError("S2SD inputs must be finite")
        _, counts = labels.unique(return_counts=True)
        if len(counts) < 2 or (counts < 2).any():
            raise ValueError("S2SD needs at least two classes with two examples each")
        teacher_embeddings = [
            functional.normalize(net(pooled), dim=-1) for net in self.teachers
        ]
        teacher_losses = [
            loss(embeddings, labels)
            for loss, embeddings in zip(
                self.teacher_objectives, teacher_embeddings, strict=True
            )
        ]
        teacher_kl = [
            similarity_distillation(student, embeddings, self.config.temperature)
            for embeddings in teacher_embeddings
        ]
        feature_loss = student.sum() * 0
        if self.completed_steps.item() >= self.config.feature_delay:
            feature_loss = similarity_distillation(
                student, pooled, self.config.temperature
            )
        return {
            "student_margin": self.student_objective(student, labels),
            "teacher_margin": torch.stack(teacher_losses).mean(),
            "teacher_distillation": torch.stack(teacher_kl).mean(),
            "feature_distillation": feature_loss,
        }

    def forward(
        self, student: torch.Tensor, labels: torch.Tensor, pooled: torch.Tensor
    ) -> torch.Tensor:
        parts = self.loss_components(student, labels, pooled)
        value = (parts["student_margin"] + parts["teacher_margin"]) / 2
        value = value + self.config.distillation_weight * parts["teacher_distillation"]
        value = value + self.config.feature_weight * parts["feature_distillation"]
        if self.training:
            self.completed_steps.add_(1)
        return value

    def training_loss(
        self, model: nn.Module, poses: torch.Tensor, labels: torch.Tensor
    ) -> torch.Tensor:
        features = model.forward_features(poses)
        student = model.project_features(features)
        pooled = auxiliary_features(features, poses[..., 2] > 0)
        return self(student, labels, pooled)

    def validate_checkpoint_state(self, state: dict, selected_step: int) -> None:
        if (
            state["completed_steps"].dtype != torch.long
            or state["completed_steps"].item() != selected_step
        ):
            raise ValueError(
                "S2SD distillation counter differs from checkpoint training step"
            )
        for name in [
            "student_objective",
            *(f"teacher_objectives.{index}" for index in range(4)),
        ]:
            rng_state = state[f"{name}.rng_state"]
            if rng_state.dtype != torch.uint8:
                raise ValueError("S2SD checkpoint sampling state must contain bytes")
            try:
                torch.Generator().set_state(rng_state.cpu())
            except RuntimeError as exc:
                raise ValueError("S2SD checkpoint sampling state is invalid") from exc


def build_s2sd_optimizer(model, criterion, recipe):
    groups = []
    for name, named, rate, decay in (
        (
            "encoder",
            [
                ("model.encoder." + k, v)
                for k, v in model.encoder.named_parameters()
                if not k.startswith("head.")
            ],
            recipe["learning_rate"] if model.train_encoder else 0.0,
            recipe["weight_decay"],
        ),
        (
            "head",
            [("model.head." + k, v) for k, v in model.head.named_parameters()],
            recipe["learning_rate"],
            recipe["weight_decay"],
        ),
        (
            "s2sd_teachers",
            [
                ("criterion.teachers." + k, v)
                for k, v in criterion.teachers.named_parameters()
            ],
            recipe["learning_rate"],
            recipe["weight_decay"],
        ),
        (
            "s2sd_boundaries",
            [
                ("criterion." + k, v)
                for k, v in criterion.named_parameters()
                if k.endswith(".beta")
            ],
            recipe["beta_learning_rate"],
            0.0,
        ),
    ):
        groups.append(
            {
                "name": name,
                "params": [v for _, v in named],
                "param_names": [k for k, _ in named],
                "lr": rate,
                "weight_decay": decay,
            }
        )
    return torch.optim.AdamW(groups, eps=recipe["optimizer_epsilon"])


def verify_s2sd_optimizer(checkpoint, recipe, encoder_parameters):
    from pose_embed.benchmark.optimizer_state import verify_named_adam

    step = checkpoint["selected_step"]
    active_encoder = recipe["encoder_mode"] == "finetune"
    expected_state = {
        "phase": "main",
        "step": step,
        "warmup_updates": 0,
        "main_updates": step,
        "encoder_trainable": active_encoder,
    }
    if checkpoint.get("training_state") != expected_state:
        raise ValueError("S2SD optimizer phase state differs")
    groups = []
    for name, names, rate, decay, updates in (
        (
            "encoder",
            [
                "model.encoder." + k
                for k in encoder_parameters
                if not k.startswith("head.")
            ],
            recipe["learning_rate"] if active_encoder else 0.0,
            recipe["weight_decay"],
            step if active_encoder else 0,
        ),
        (
            "head",
            ["model." + k for k in checkpoint["model"] if k.startswith("head.")],
            recipe["learning_rate"],
            recipe["weight_decay"],
            step,
        ),
        (
            "s2sd_teachers",
            [
                "criterion." + k
                for k in checkpoint["criterion"]
                if k.startswith("teachers.")
            ],
            recipe["learning_rate"],
            recipe["weight_decay"],
            step,
        ),
        (
            "s2sd_boundaries",
            ["criterion." + k for k in checkpoint["criterion"] if k.endswith(".beta")],
            recipe["beta_learning_rate"],
            0.0,
            step,
        ),
    ):
        groups.append(
            {
                "name": name,
                "param_names": names,
                "lr": rate,
                "weight_decay": decay,
                "updates": updates,
            }
        )
    verify_named_adam(checkpoint, groups, epsilon=recipe["optimizer_epsilon"])
