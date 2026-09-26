"""Independent DRML-PA motion adaptation of Zheng et al. (ICCV 2021), Eqs. 2–10.

No source from the unlicensed DRML repository is copied or adapted here.
"""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as functional
from pydantic import Field
from pytorch_metric_learning.losses import ProxyAnchorLoss
from torch import nn

from pose_embed.config import StrictModel


class DRMLParameters(StrictModel):
    recipe: Literal["zheng2021_pa_motion_v1"] = "zheng2021_pa_motion_v1"
    branches: Literal[4] = 4
    branch_dimension: int = Field(default=128, gt=0)
    reconstruction_weight: float = Field(default=0.1, gt=0)
    embedding_weight: float = Field(default=10.0, gt=0)
    alpha: float = Field(default=32.0, gt=0)
    margin: float = Field(default=0.1, ge=0, lt=1)
    encoder_learning_rate: float = Field(default=1e-5, gt=0)
    head_learning_rate: float = Field(default=1e-4, gt=0)
    proxy_learning_rate: float = Field(default=1e-4, gt=0)
    pooling: Literal["confidence_valid_token_mean"] = "confidence_valid_token_mean"
    all_invalid_policy: Literal["zero_pooled_feature"] = "zero_pooled_feature"
    assignment_tie: Literal["lowest_branch_index"] = "lowest_branch_index"
    score_normalization: Literal["linear_divided_by_incoming_sum"] = (
        "linear_divided_by_incoming_sum"
    )


class DRMLHead(nn.Module):
    """Four individual branches and a within-clip directed relation graph."""

    requires_valid_mask = True

    def __init__(self, representation_dimension: int, branch_dimension: int = 128):
        super().__init__()
        if representation_dimension < 1 or branch_dimension < 1:
            raise ValueError("DRML dimensions must be positive")
        self.representation_dimension = representation_dimension
        self.branch_dimension = branch_dimension
        self.individual = nn.ModuleList(
            nn.Linear(representation_dimension, branch_dimension) for _ in range(4)
        )
        self.decoders = nn.ModuleList(
            nn.Linear(branch_dimension, representation_dimension) for _ in range(4)
        )
        self.relation_a = nn.ModuleList(
            nn.Linear(representation_dimension, branch_dimension) for _ in range(4)
        )
        self.relation_b = nn.ModuleList(
            nn.Linear(representation_dimension, branch_dimension) for _ in range(4)
        )
        self.score = nn.Linear(branch_dimension, 1)
        self.updater = nn.Linear(2 * branch_dimension, branch_dimension)

    def pool(self, features: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        if (
            features.ndim != 5
            or any(size == 0 for size in features.shape)
            or features.shape[-1] != self.representation_dimension
            or valid_mask.shape != features.shape[:-1]
            or valid_mask.dtype != torch.bool
            or valid_mask.device != features.device
        ):
            raise ValueError("DRML pooling requires aligned tokens and bool mask")
        count = valid_mask.sum(dim=(1, 2, 3)).clamp_min(1).unsqueeze(-1)
        return (
            features.masked_fill(~valid_mask.unsqueeze(-1), 0).sum(dim=(1, 2, 3))
            / count
        )

    def relation_graph(
        self, individual: torch.Tensor, pooled: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Eqs. 5–8; source j is axis 1 and receiving node i is axis 2."""
        meta_a = torch.stack([layer(pooled) for layer in self.relation_a], dim=1)
        meta_b = torch.stack([layer(pooled) for layer in self.relation_b], dim=1)
        relations = meta_a[:, :, None, :] - meta_b[:, None, :, :]
        scores = self.score(relations).squeeze(-1)
        denominator = scores.sum(dim=1, keepdim=True)
        if not torch.isfinite(denominator).all() or (denominator == 0).any():
            raise ValueError("DRML Eq. 7 has zero or non-finite incoming score sum")
        weights = scores / denominator
        messages = torch.einsum("bji,bjd->bid", weights, individual)
        updated = self.updater(torch.cat([individual, messages], dim=-1))
        return updated.flatten(1), weights, messages

    def training_outputs(
        self, features: torch.Tensor, valid_mask: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        pooled = self.pool(features, valid_mask)
        individual = torch.stack([layer(pooled) for layer in self.individual], dim=1)
        reconstructed = torch.stack(
            [layer(individual[:, k].detach()) for k, layer in enumerate(self.decoders)],
            dim=1,
        )
        # Eq. 2 explicitly trains only P; this is the unsquared L2 norm.
        errors = (reconstructed - pooled.detach()[:, None, :]).norm(dim=-1)
        assignment = errors.detach().argmin(dim=1)
        # Eq. 10 blocks J_emb from both the trunk and the individual branches G.
        embedding, weights, messages = self.relation_graph(
            individual.detach(), pooled.detach()
        )
        return {
            "individual": individual,
            "reconstruction_errors": errors,
            "assignment": assignment,
            "embedding": embedding,
            "weights": weights,
            "messages": messages,
        }

    def forward_raw(
        self, features: torch.Tensor, valid_mask: torch.Tensor
    ) -> torch.Tensor:
        pooled = self.pool(features, valid_mask)
        individual = torch.stack([layer(pooled) for layer in self.individual], dim=1)
        return self.relation_graph(individual.detach(), pooled.detach())[0]

    def forward(self, features: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.forward_raw(features, valid_mask), dim=-1)


class DRMLLoss(nn.Module):
    """Assigned per-branch PA, decoder reconstruction, and final-embedding PA."""

    requires_feature_training = True

    def __init__(self, num_classes: int, parameters: DRMLParameters):
        super().__init__()
        if num_classes < 2:
            raise ValueError("DRML needs at least two global training classes")
        self.parameters_config = parameters
        self.num_classes = num_classes
        self.register_buffer("branch_steps", torch.zeros(4, dtype=torch.long))
        self.register_buffer("training_steps", torch.zeros((), dtype=torch.long))
        self.active_branches = (False,) * 4
        self.assignment_counts = (0,) * 4
        arguments = {
            "num_classes": num_classes,
            "alpha": parameters.alpha,
            "margin": parameters.margin,
        }
        self.individual_losses = nn.ModuleList(
            ProxyAnchorLoss(embedding_size=parameters.branch_dimension, **arguments)
            for _ in range(parameters.branches)
        )
        self.embedding_loss = ProxyAnchorLoss(
            embedding_size=parameters.branches * parameters.branch_dimension,
            **arguments,
        )

    def components(
        self, outputs: dict[str, torch.Tensor], labels: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        individual = outputs["individual"]
        if (
            labels.dtype != torch.long
            or labels.shape != (individual.shape[0],)
            or labels.device != individual.device
            or (labels < 0).any()
            or (labels >= self.num_classes).any()
        ):
            raise ValueError("DRML requires aligned global integer class labels")
        ensemble = individual.new_zeros(())
        for k, objective in enumerate(self.individual_losses):
            selected = outputs["assignment"] == k
            if selected.any():
                ensemble = ensemble + objective(
                    individual[selected, k], labels[selected]
                )
        reconstruction = outputs["reconstruction_errors"].mean()
        embedding = self.embedding_loss(outputs["embedding"], labels)
        total = (
            ensemble
            + self.parameters_config.reconstruction_weight * reconstruction
            + self.parameters_config.embedding_weight * embedding
        )
        return {
            "ensemble": ensemble,
            "reconstruction": reconstruction,
            "embedding": embedding,
            "total": total,
        }

    def training_loss(self, model, poses: torch.Tensor, labels: torch.Tensor):
        if not isinstance(model.head, DRMLHead):
            raise ValueError("DRML training requires the declared relational head")
        features = model.forward_features(poses)
        outputs = model.head.training_outputs(features, poses[..., 2] > 0)
        value = self.components(outputs, labels)["total"]
        self.assignment_counts = tuple(
            torch.bincount(outputs["assignment"], minlength=4).tolist()
        )
        self.active_branches = tuple(count > 0 for count in self.assignment_counts)
        with torch.no_grad():
            self.training_steps.add_(1)
            self.branch_steps.add_(
                torch.tensor(self.active_branches, device=self.branch_steps.device)
            )
        return value

    def after_backward(self, model) -> None:
        # Stack backward creates zero gradients for unassigned branches. Skipping
        # their optimizer step also excludes Adam momentum and weight decay.
        for active, branch in zip(
            self.active_branches, model.head.individual, strict=True
        ):
            if not active:
                for parameter in branch.parameters():
                    parameter.grad = None

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor):
        raise ValueError("DRML requires feature training with its relational head")


def verify_drml_optimizer(checkpoint, recipe, encoder_parameters, history, batch_size):
    """Verify assignment-driven update counts and all named optimizer state."""
    step = checkpoint["selected_step"]
    cumulative = [0] * 4
    for row in history:
        counts = row.get("drml_assignment_counts")
        if (
            not isinstance(counts, list)
            or len(counts) != 4
            or any(type(value) is not int or value < 0 for value in counts)
            or sum(counts) != batch_size
        ):
            raise ValueError("DRML assignment history is incomplete or invalid")
        if row["step"] <= step:
            cumulative = [
                total + (count > 0)
                for total, count in zip(cumulative, counts, strict=True)
            ]
    criterion = checkpoint["criterion"]
    if (
        criterion["training_steps"].item() != step
        or criterion["branch_steps"].tolist() != cumulative
    ):
        raise ValueError("DRML branch update counters differ from assignment history")
    encoder_trainable = recipe["encoder_mode"] == "finetune"
    if checkpoint.get("training_state") != {
        "phase": "main",
        "step": step,
        "warmup_updates": 0,
        "main_updates": step,
        "encoder_trainable": encoder_trainable,
    }:
        raise ValueError("DRML checkpoint optimizer phase is invalid")
    tensors = {
        **{"model." + name: value for name, value in checkpoint["model"].items()},
        **{
            "criterion." + name: value
            for name, value in criterion.items()
            if name not in {"branch_steps", "training_steps"}
        },
    }
    required_names = {
        name for name in tensors if name.startswith(("model.head.", "criterion."))
    } | {
        "model.encoder." + name
        for name in encoder_parameters
        if not name.startswith("head.")
    }
    optimizer = checkpoint.get("optimizer", {})
    groups = optimizer.get("param_groups", [])
    states = optimizer.get("state", {})
    if [group.get("name") for group in groups] != ["encoder", "head", "proxies"]:
        raise ValueError("DRML optimizer groups are invalid")
    seen_names, seen_ids = set(), set()
    for group, prefix, learning_rate in zip(
        groups,
        ["model.encoder.", "model.head.", "criterion."],
        [
            recipe["encoder_learning_rate"] if encoder_trainable else 0.0,
            recipe["head_learning_rate"],
            recipe["proxy_learning_rate"],
        ],
        strict=True,
    ):
        names, indices = group.get("param_names", []), group.get("params", [])
        if (
            not names
            or len(names) != len(indices)
            or group.get("lr") != learning_rate
            or group.get("weight_decay") != recipe["weight_decay"]
            or group.get("eps") != recipe["optimizer_epsilon"]
            or tuple(group.get("betas", [])) != (0.9, 0.999)
            or group.get("amsgrad") is not False
        ):
            raise ValueError("DRML optimizer recipe is invalid")
        for name, index in zip(names, indices, strict=True):
            if (
                name not in required_names
                or not name.startswith(prefix)
                or name in seen_names
                or type(index) is not int
                or index in seen_ids
            ):
                raise ValueError("DRML optimizer parameter mapping is invalid")
            seen_names.add(name)
            seen_ids.add(index)
            updates = step
            for branch_prefix in (
                "model.head.individual.",
                "criterion.individual_losses.",
            ):
                if name.startswith(branch_prefix):
                    updates = cumulative[
                        int(name.removeprefix(branch_prefix).split(".")[0])
                    ]
            if group["name"] == "encoder" and not encoder_trainable:
                updates = 0
            state = states.get(index)
            if updates == 0:
                if state is not None:
                    raise ValueError("DRML optimizer updated an untrained parameter")
                continue
            if (
                not isinstance(state, dict)
                or set(state) != {"step", "exp_avg", "exp_avg_sq"}
                or not all(
                    isinstance(value, torch.Tensor) and torch.isfinite(value).all()
                    for value in state.values()
                )
                or state["step"].numel() != 1
                or state["step"].item() != updates
                or state["exp_avg"].shape != tensors[name].shape
                or state["exp_avg_sq"].shape != tensors[name].shape
                or (state["exp_avg_sq"] < 0).any()
            ):
                raise ValueError("DRML optimizer moments or update count are invalid")
    if seen_names != required_names or not set(states).issubset(seen_ids):
        raise ValueError("DRML optimizer has missing or unknown parameter state")
