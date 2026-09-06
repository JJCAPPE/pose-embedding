"""Locked v1 corruptions for `[M,T,17,C]` or `[T,17,C]` query tensors."""

from __future__ import annotations

import hashlib
import random
from decimal import Decimal
from typing import Literal

import torch

CorruptionFamily = Literal["coordinate_jitter", "joint_mask", "frame_mask"]

# MotionBERT H36M17 arms, legs, and central chain. Group order is randomized per
# sample; joints within a group remain proximal-to-distal.
_JOINT_GROUPS = (
    (11, 12, 13),
    (14, 15, 16),
    (1, 2, 3),
    (4, 5, 6),
    (0, 7, 8, 9, 10),
)


def stable_corruption_seed(sample_id: str, family: str, severity: int | float) -> int:
    """Derive a process-independent 63-bit seed from corruption identity."""
    canonical_severity = format(Decimal(str(severity)).normalize(), "f")
    payload = f"protocol-v1\0{sample_id}\0{family}\0{canonical_severity}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def _canonical_shape(poses: torch.Tensor) -> tuple[torch.Tensor, bool]:
    if poses.ndim == 3:
        poses = poses.unsqueeze(0)
        squeezed = True
    elif poses.ndim == 4:
        squeezed = False
    else:
        raise ValueError("poses must have shape [T,J,C] or [M,T,J,C]")
    if poses.shape[2:] != (17, 3):
        raise ValueError(
            "v1 corruptions require H36M17 joints with x, y, confidence channels"
        )
    return poses, squeezed


def _restore_shape(poses: torch.Tensor, squeezed: bool) -> torch.Tensor:
    return poses.squeeze(0) if squeezed else poses


def _median_torso_scale(poses: torch.Tensor) -> torch.Tensor:
    xy = poses[..., :2]
    shoulder_center = (xy[:, :, 11] + xy[:, :, 14]) / 2
    hip_center = (xy[:, :, 4] + xy[:, :, 1]) / 2
    scales = torch.linalg.vector_norm(shoulder_center - hip_center, dim=-1)
    torso_confidence = poses[..., 2][..., [11, 14, 4, 1]]
    valid = (torso_confidence > 0).all(dim=-1)
    finite_positive = scales[valid & torch.isfinite(scales) & (scales > 0)]
    if finite_positive.numel() == 0:
        raise ValueError("cannot compute a positive median torso scale")
    return finite_positive.median()


def coordinate_jitter(
    poses: torch.Tensor,
    *,
    fraction: float,
    sample_id: str,
) -> torch.Tensor:
    """Add deterministic xy Gaussian noise scaled by median torso length."""
    canonical, squeezed = _canonical_shape(poses)
    if fraction < 0:
        raise ValueError("jitter fraction must be nonnegative")
    if fraction == 0:
        return _restore_shape(canonical.clone(), squeezed)
    scale = _median_torso_scale(canonical)
    generator = torch.Generator(device=canonical.device)
    generator.manual_seed(
        stable_corruption_seed(sample_id, "coordinate_jitter", fraction)
    )
    result = canonical.clone()
    noise = torch.randn(
        result[..., :2].shape,
        dtype=result.dtype,
        device=result.device,
        generator=generator,
    )
    observed = result[..., 2:3] > 0
    result[..., :2] += noise * observed * scale * fraction
    return _restore_shape(result, squeezed)


def _select_limb_first_joints(count: int, seed: int) -> tuple[int, ...]:
    if count < 0 or count > 17:
        raise ValueError("joint mask count must lie in [0, 17]")
    rng = random.Random(seed)
    groups = list(_JOINT_GROUPS)
    rng.shuffle(groups)
    selected: list[int] = []
    for group in groups:
        ordered = list(group)
        for joint in ordered:
            if joint not in selected:
                selected.append(joint)
            if len(selected) == count:
                return tuple(selected)
    remaining = [joint for joint in range(17) if joint not in selected]
    rng.shuffle(remaining)
    return tuple((selected + remaining)[:count])


def joint_mask(
    poses: torch.Tensor,
    *,
    count: int,
    sample_id: str,
    value: float = 0.0,
) -> torch.Tensor:
    """Mask exactly ``count`` complete trajectories, including confidence."""
    canonical, squeezed = _canonical_shape(poses)
    if count == 0:
        return _restore_shape(canonical.clone(), squeezed)
    joints = _select_limb_first_joints(
        count,
        stable_corruption_seed(sample_id, "joint_mask", count),
    )
    result = canonical.clone()
    result[:, :, list(joints), :] = value
    return _restore_shape(result, squeezed)


def consecutive_frame_mask(
    poses: torch.Tensor,
    *,
    count: int,
    sample_id: str,
    value: float = 0.0,
) -> torch.Tensor:
    """Mask one deterministic consecutive frame block across all people/joints."""
    canonical, squeezed = _canonical_shape(poses)
    if count == 0:
        return _restore_shape(canonical.clone(), squeezed)
    frames = canonical.shape[1]
    if count < 0 or count > frames:
        raise ValueError(f"frame mask count must lie in [0, {frames}]")
    seed = stable_corruption_seed(sample_id, "frame_mask", count)
    start = random.Random(seed).randrange(frames - count + 1)
    result = canonical.clone()
    result[:, start : start + count, :, :] = value
    return _restore_shape(result, squeezed)


def apply_corruption(
    poses: torch.Tensor,
    *,
    family: CorruptionFamily,
    severity: int | float,
    sample_id: str,
    masking_value: float = 0.0,
) -> torch.Tensor:
    """Dispatch one declared corruption; severity zero is always an exact copy."""
    _canonical_shape(poses)
    if severity == 0:
        return poses.clone()
    if family == "coordinate_jitter":
        return coordinate_jitter(poses, fraction=float(severity), sample_id=sample_id)
    if family == "joint_mask":
        if float(severity) != int(severity):
            raise ValueError("joint-mask severity must be an integer count")
        return joint_mask(
            poses, count=int(severity), sample_id=sample_id, value=masking_value
        )
    if family == "frame_mask":
        if float(severity) != int(severity):
            raise ValueError("frame-mask severity must be an integer count")
        return consecutive_frame_mask(
            poses, count=int(severity), sample_id=sample_id, value=masking_value
        )
    raise ValueError(f"unsupported corruption family: {family}")
