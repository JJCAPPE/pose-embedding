"""Verify named Adam states against the independently reconstructed recipe."""

from __future__ import annotations

import torch


def verify_named_adam(checkpoint, expected_groups, *, epsilon=1e-8):
    """Groups declare exact names, rates, decay and update counts per parameter."""
    optimizer = checkpoint.get("optimizer", {})
    groups = optimizer.get("param_groups", [])
    states = optimizer.get("state", {})
    tensors = {
        **{"model." + key: value for key, value in checkpoint["model"].items()},
        **{"criterion." + key: value for key, value in checkpoint["criterion"].items()},
    }
    if len(groups) != len(expected_groups):
        raise ValueError("checkpoint optimizer groups are incomplete")
    seen_ids, seen_names, expected_states = set(), set(), set()
    for group, expected in zip(groups, expected_groups, strict=True):
        names, indices = group.get("param_names", []), group.get("params", [])
        if (
            names != expected["param_names"]
            or len(names) != len(indices)
            or group.get("name") != expected["name"]
            or group.get("lr") != expected["lr"]
            or group.get("weight_decay") != expected["weight_decay"]
            or group.get("eps") != epsilon
            or tuple(group.get("betas", [])) != (0.9, 0.999)
            or group.get("amsgrad") is not False
            or group.get("maximize") is not False
        ):
            raise ValueError("checkpoint optimizer recipe or parameter names differ")
        for name, index in zip(names, indices, strict=True):
            if (
                type(index) is not int
                or index in seen_ids
                or name in seen_names
                or name not in tensors
            ):
                raise ValueError("checkpoint optimizer parameter mapping is invalid")
            seen_ids.add(index)
            seen_names.add(name)
            updates = expected["updates"]
            if isinstance(updates, dict):
                updates = updates[name]
            if updates == 0:
                if index in states:
                    raise ValueError("inactive parameter has optimizer moments")
                continue
            expected_states.add(index)
            state = states.get(index, {})
            if (
                set(state) != {"step", "exp_avg", "exp_avg_sq"}
                or not all(
                    isinstance(value, torch.Tensor) and torch.isfinite(value).all()
                    for value in state.values()
                )
                or state["step"].numel() != 1
                or state["step"].item() != updates
                or state["exp_avg"].shape != tensors[name].shape
                or state["exp_avg_sq"].shape != tensors[name].shape
                or state["exp_avg"].dtype != tensors[name].dtype
                or state["exp_avg_sq"].dtype != tensors[name].dtype
                or (state["exp_avg_sq"] < 0).any()
            ):
                raise ValueError("checkpoint optimizer moments or update count differ")
    if set(states) != expected_states:
        raise ValueError("checkpoint optimizer has unknown or missing moments")
