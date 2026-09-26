"""Actual optimizer recipes and full warmup boundaries for benchmark adapters."""

from __future__ import annotations

import math

import torch

from pose_embed.benchmark.avsl import (
    build_avsl_optimizer,
)
from pose_embed.benchmark.avsl import (
    learning_rates as avsl_learning_rates,
)
from pose_embed.benchmark.avsl import (
    optimizer_recipe as avsl_optimizer_recipe,
)
from pose_embed.benchmark.config import BenchmarkTraining
from pose_embed.benchmark.diva import DiVAParameters
from pose_embed.benchmark.drml import DRMLParameters
from pose_embed.benchmark.hist import HISTParameters
from pose_embed.benchmark.proxy_nca_plus import ProxyNCAPlusParameters


def resolve_recipe(
    method_id: str,
    parameters: dict,
    training: BenchmarkTraining,
    num_records: int,
    selection_num_records: int | None = None,
    profile: bool = False,
) -> dict:
    """Scale the declared method's rates together, preserving their ratios."""
    recipe = _resolve_recipe(
        method_id, parameters, training, num_records, selection_num_records, profile
    )
    return {
        key: value * training.learning_rate_scale
        if key.endswith("learning_rate")
        else value
        for key, value in recipe.items()
    } | {"learning_rate_scale": training.learning_rate_scale}


def _resolve_recipe(
    method_id: str,
    parameters: dict,
    training: BenchmarkTraining,
    num_records: int,
    selection_num_records: int | None = None,
    profile: bool = False,
) -> dict:
    """Bind recipe constants and data-dependent warmup before executing a run.

    The total update budget includes warmup. Selection excludes steps that would
    fall within warmup when the selected run is retrained on all auxiliary data.
    """
    if num_records < 1:
        raise ValueError("training requires at least one record")
    if method_id == "proxy_anchor_avsl":
        return avsl_optimizer_recipe(
            parameters, training, num_records, selection_num_records, profile=profile
        )
    common = {
        "encoder_mode": training.encoder_mode,
        "warmup_steps": 0,
        "minimum_selected_step": 1,
        "profile_phase": "main_capacity" if profile else None,
    }
    if method_id == "mhgl":
        from pose_embed.benchmark.mhgl import optimizer_recipe

        return optimizer_recipe(parameters, training, profile=profile) | {
            "named_optimizer_state": True
        }
    if method_id == "s2sd":
        from pose_embed.benchmark.s2sd import S2SDParameters

        config = S2SDParameters.model_validate(parameters)
        return common | {
            **config.model_dump(mode="json"),
            "optimizer": "AdamW",
            "optimizer_epsilon": 1e-8,
            "learning_rate": training.learning_rate,
            "weight_decay": training.weight_decay,
            "named_optimizer_state": True,
            "minimum_selected_step": config.feature_delay + 1,
            "profile_phase": "post_feature_delay_capacity" if profile else None,
            "profile_counter_offset": config.feature_delay if profile else 0,
        }
    if method_id == "diva":
        config = DiVAParameters.model_validate(parameters)
        if (
            training.physical_batch_size != config.physical_batch_size
            or training.classes_per_batch < 3
            or training.samples_per_class < 3
        ):
            raise ValueError(
                "DiVA needs its declared physical batch with P>=3 and K>=3"
            )
        return (
            common
            | config.model_dump(mode="json")
            | {
                "optimizer": "Adam",
                "optimizer_epsilon": 1e-8,
                "schedule": "constant_lr_validation_r_at_1_selection",
                "memory_bootstrap": "first_seeded_training_batches",
            }
        )
    if method_id == "hist":
        config = HISTParameters.model_validate(parameters)
        epoch_steps = math.ceil(num_records / training.physical_batch_size)
        final_epoch_steps = math.ceil(
            (selection_num_records or num_records) / training.physical_batch_size
        )
        return common | {
            **config.model_dump(mode="json"),
            "optimizer": "Adam",
            "optimizer_epsilon": 1e-8,
            "epoch_steps": epoch_steps,
            "warmup_steps": config.warmup_epochs * epoch_steps,
            "minimum_selected_step": config.warmup_epochs
            * max(epoch_steps, final_epoch_steps)
            + 1,
            "main_optimizer_state": "preserved_after_warmup",
            "schedule": "main_epochs_step_decay",
            "profile_phase": "post_warmup_capacity" if profile else None,
            "profile_executes_warmup": False if profile else None,
        }
    if method_id == "drml":
        config = DRMLParameters.model_validate(parameters)
        return common | {
            **config.model_dump(mode="json"),
            "optimizer": "AdamW",
            "optimizer_epsilon": 1e-8,
            "weight_decay": training.weight_decay,
            "named_optimizer_state": True,
            "schedule": "constant_lr_validation_r_at_1_selection",
        }
    if method_id not in {"proxy_nca_pp", "proxy_nca_metrix"}:
        return common | {
            "optimizer": "AdamW",
            "learning_rate": training.learning_rate,
            "weight_decay": training.weight_decay,
        }
    if method_id == "proxy_nca_metrix":
        from pose_embed.benchmark.metrix import MetrixNCAParameters

        parameters = MetrixNCAParameters.model_validate(parameters).model_dump(
            include=set(ProxyNCAPlusParameters.model_fields)
        )
    config = ProxyNCAPlusParameters.model_validate(parameters)
    epoch_steps = math.ceil(num_records / training.physical_batch_size)
    selection_epoch_steps = math.ceil(
        (selection_num_records or num_records) / training.physical_batch_size
    )
    return common | {
        **config.model_dump(mode="json"),
        "optimizer": "Adam",
        "weight_decay": 0.0,
        "epoch_steps": epoch_steps,
        "warmup_steps": config.warmup_epochs * epoch_steps,
        "minimum_selected_step": config.warmup_epochs
        * max(epoch_steps, selection_epoch_steps)
        + 1,
        "main_optimizer_state": "fresh_after_warmup",
        "schedule": "constant_lr_validation_r_at_1_selection",
        "profile_phase": "post_warmup_capacity" if profile else None,
        "profile_executes_warmup": False if profile else None,
    }


def phase_for_step(recipe: dict, step: int) -> str:
    if step < 1:
        raise ValueError("training steps are one-based")
    if recipe["profile_phase"] is not None:
        return "main"
    return "warmup" if step <= recipe["warmup_steps"] else "main"


def build_optimizer(model, criterion, recipe: dict, phase: str):
    """Create a fresh optimizer at warmup/main boundaries; never omit proxies."""
    if phase not in {"warmup", "main"}:
        raise ValueError("unknown training phase")
    model.set_encoder_trainable(
        recipe["encoder_mode"] == "finetune" and phase == "main"
    )
    if recipe.get("recipe") == "milbich2020_cub_motion_corrected2021":
        groups = []
        for name, module in (("encoder", model.encoder), ("head", model.head)):
            named = [
                (f"model.{name}.{key}", value)
                for key, value in module.named_parameters()
                if value.requires_grad
            ]
            groups.append(
                {
                    "name": name,
                    "params": [value for _, value in named],
                    "param_names": [key for key, _ in named],
                    "lr": recipe["learning_rate"],
                }
            )
        names = {
            id(value): "criterion." + key for key, value in criterion.named_parameters()
        }
        for group in criterion.parameter_groups(
            recipe["learning_rate"], recipe["weight_decay"]
        ):
            group["param_names"] = [names[id(value)] for value in group["params"]]
            if group["name"] == "diva_boundaries":
                group["lr"] = recipe["beta_learning_rate"]
            groups.append(group)
        return torch.optim.Adam(
            groups,
            lr=recipe["learning_rate"],
            weight_decay=recipe["weight_decay"],
            eps=recipe["optimizer_epsilon"],
        )
    if recipe.get("recipe") == "zhang2022_cub_motion_v1":
        return build_avsl_optimizer(model, criterion, recipe)
    if recipe.get("recipe") == "ebrahimpour2022_printed_equations_motion_v1":
        from pose_embed.benchmark.mhgl import build_mhgl_optimizer

        return build_mhgl_optimizer(model, criterion, recipe)
    if recipe.get("recipe") == "roth2021_rmargin_msdfa_cub_motion":
        from pose_embed.benchmark.s2sd import build_s2sd_optimizer

        return build_s2sd_optimizer(model, criterion, recipe)
    if recipe["optimizer"] == "AdamW" and not recipe.get("named_optimizer_state"):
        parameters = [
            p for p in [*model.parameters(), *criterion.parameters()] if p.requires_grad
        ]
        return torch.optim.AdamW(
            parameters,
            lr=recipe["learning_rate"],
            weight_decay=recipe["weight_decay"],
        )
    if recipe.get("recipe") == "lim2022_cub_motion":
        groups = []
        for name, module, prefix, rate in (
            ("encoder", model.encoder, "model.encoder.", recipe["head_learning_rate"]),
            ("head", model.head, "model.head.", recipe["head_learning_rate"]),
            (
                "distributions",
                criterion.loss.distributions,
                "criterion.loss.distributions.",
                recipe["distribution_learning_rate"],
            ),
            (
                "graph",
                criterion.loss.graph,
                "criterion.loss.graph.",
                recipe["graph_learning_rate"],
            ),
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
                    "lr": 0.0
                    if name == "encoder" and not model.train_encoder
                    else rate,
                }
            )
        return torch.optim.Adam(
            groups, eps=recipe["optimizer_epsilon"], weight_decay=recipe["weight_decay"]
        )
    groups = []
    components = (
        ("encoder", model.encoder, "model.encoder."),
        ("head", model.head, "model.head."),
        ("proxies", criterion, "criterion."),
    )
    for name, module, prefix in components:
        named = [
            (prefix + key, value)
            for key, value in module.named_parameters()
            if name != "encoder" or not key.startswith("head.")
        ]
        learning_rate = (
            recipe["proxy_learning_rate"]
            if name == "proxies"
            else recipe["head_learning_rate"]
        )
        if name == "encoder":
            learning_rate = recipe.get("encoder_learning_rate", learning_rate)
        if name == "encoder" and not model.train_encoder:
            learning_rate = 0.0
        groups.append(
            {
                "name": name,
                "params": [value for _, value in named],
                "param_names": [key for key, _ in named],
                "lr": learning_rate,
            }
        )
    optimizer_class = (
        torch.optim.AdamW if recipe["optimizer"] == "AdamW" else torch.optim.Adam
    )
    return optimizer_class(
        groups,
        lr=recipe["head_learning_rate"],
        eps=recipe["optimizer_epsilon"],
        weight_decay=recipe["weight_decay"],
    )


def advance_optimizer(model, criterion, optimizer, recipe, phase):
    """HIST retains its warmup moments; ProxyNCA++ starts a fresh main optimizer."""
    if recipe.get("main_optimizer_state") == "preserved_after_warmup":
        model.set_encoder_trainable(
            recipe["encoder_mode"] == "finetune" and phase == "main"
        )
        return optimizer
    return build_optimizer(model, criterion, recipe, phase)


def hist_learning_rates(recipe, step):
    main_updates = (
        0
        if recipe["profile_phase"] is not None
        else max(0, step - recipe["warmup_steps"] - 1)
    )
    decays = main_updates // (recipe["epoch_steps"] * recipe["decay_epochs"])
    factor = recipe["decay_factor"] ** decays
    encoder_active = (
        recipe["encoder_mode"] == "finetune" and phase_for_step(recipe, step) == "main"
    )
    return {
        "encoder": recipe["head_learning_rate"] * factor if encoder_active else 0.0,
        "head": recipe["head_learning_rate"] * factor,
        "distributions": recipe["distribution_learning_rate"] * factor,
        "graph": recipe["graph_learning_rate"] * factor,
    }


def set_step_learning_rates(optimizer, recipe, step):
    if recipe.get("recipe") == "zhang2022_cub_motion_v1":
        rates = avsl_learning_rates(recipe, step)
        for group in optimizer.param_groups:
            group["lr"] = rates[group["name"]]
    if recipe.get("recipe") == "lim2022_cub_motion":
        rates = hist_learning_rates(recipe, step)
        for group in optimizer.param_groups:
            group["lr"] = rates[group["name"]]
