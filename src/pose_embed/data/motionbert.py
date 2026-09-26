"""Deterministic HRNet preprocessing for the locked MotionBERT convention.

The camera, tracking, coordinate mapping, sampling and crop operations are
adapted from MotionBERT by Zhu et al. (ICCV 2023), commit
705d3a95354db8bdb696b3492e47a3b5537174ff, lib/data/dataset_action.py and
lib/utils/utils_data.py, licensed under Apache-2.0:
https://www.apache.org/licenses/LICENSE-2.0

Changes: remove random augmentation; track confidence with each person and
map it with the protocol's minimum-source rule; validate inputs and expose
intermediate stages for parity. See THIRD_PARTY_NOTICES.md.
"""

from __future__ import annotations

from typing import Any, Literal, overload

import numpy as np

from pose_embed.config import ProtocolConfig


@overload
def preprocess_annotation(
    annotation: dict[str, Any],
    protocol: ProtocolConfig,
    *,
    return_stages: Literal[False] = False,
) -> np.ndarray: ...


@overload
def preprocess_annotation(
    annotation: dict[str, Any],
    protocol: ProtocolConfig,
    *,
    return_stages: Literal[True],
) -> tuple[np.ndarray, dict[str, np.ndarray]]: ...


def preprocess_annotation(
    annotation: dict[str, Any], protocol: ProtocolConfig, *, return_stages: bool = False
) -> np.ndarray | tuple[np.ndarray, dict[str, np.ndarray]]:
    """Produce a float32 `[2,100,17,3]` tensor without changing the annotation."""
    xy = np.asarray(annotation["keypoint"])
    confidence = np.asarray(annotation["keypoint_score"])
    if (
        xy.ndim != 4
        or xy.shape[0] not in {1, 2}
        or xy.shape[1] < 1
        or xy.shape[2:] != (17, 2)
        or confidence.shape != xy.shape[:3]
        or annotation["total_frames"] != xy.shape[1]
    ):
        raise ValueError(
            "annotation must contain one or two nonempty COCO17 pose tracks"
        )
    if (
        xy.dtype.kind != "f"
        or confidence.dtype.kind != "f"
        or not np.isfinite(xy).all()
        or not np.isfinite(confidence).all()
    ):
        raise ValueError(
            "coordinates and confidence must be finite floating-point arrays"
        )
    image_shape = np.asarray(annotation["img_shape"])
    if (
        image_shape.shape != (2,)
        or not np.isfinite(image_shape).all()
        or np.any(image_shape <= 0)
    ):
        raise ValueError("annotation image dimensions must be two positive values")
    people, frames = xy.shape[:2]
    stages: dict[str, np.ndarray] = {}

    # Preserve upstream arithmetic precision until its explicit float32 boundary.
    camera = xy / int(max(image_shape)) * 2 - 1
    stages["camera_normalization"] = camera
    indices = np.broadcast_to(np.arange(people)[:, None], (people, frames)).copy()
    if people == 2:
        same = np.linalg.norm(camera[0, 1:] - camera[0, :-1], axis=-1).sum(axis=-1)
        other = np.linalg.norm(camera[0, 1:] - camera[1, :-1], axis=-1).sum(axis=-1)
        swaps = np.cumsum(same > other) % 2
        indices[0, 1:] = swaps
        indices[1, 1:] = 1 - swaps
        tracked = camera[indices, np.arange(frames)].astype(np.float64)
    else:
        tracked = camera.copy()
    stages["tracking_indices"] = indices
    stages["person_tracking"] = tracked
    tracked_confidence = confidence[indices, np.arange(frames)]

    mapped = np.zeros(tracked.shape)
    sources = protocol.input_pipeline.coco_to_h36m_sources
    for joint, members in enumerate(sources):
        if len(members) == 1:
            mapped[:, :, joint] = tracked[:, :, members[0]]
        elif len(members) == 2:
            mapped[:, :, joint] = (
                tracked[:, :, members[0]] + tracked[:, :, members[1]]
            ) * 0.5
    # Preserve the upstream mean operation order for the four-source belly.
    mapped[:, :, 7] = (mapped[:, :, 0] + mapped[:, :, 8]) * 0.5
    mapped_confidence = np.stack(
        [tracked_confidence[:, :, list(members)].min(axis=-1) for members in sources],
        axis=-1,
    )
    stages["coordinate_mapping"] = mapped
    stages["confidence_mapping"] = mapped_confidence
    temporal = np.linspace(
        0, frames, num=protocol.dataset.frames, endpoint=False, dtype=int
    )
    stages["temporal_indices"] = temporal
    sampled = np.concatenate(
        (mapped[:, temporal], mapped_confidence[:, temporal, :, None]), axis=-1
    )
    stages["temporal_sampling"] = sampled
    if people == 1:
        sampled = np.concatenate((sampled, np.zeros_like(sampled)), axis=0)
    padded = sampled.astype(np.float32)
    stages["single_person_padding"] = padded

    result = padded.copy()
    valid = padded[padded[..., 2] > 0, :2]
    if len(valid) < 4:
        result.fill(0)
    else:
        lower, upper = valid.min(axis=0), valid.max(axis=0)
        scale = max(upper - lower)
        if scale == 0:
            result.fill(0)
        else:
            center_offset = (lower + upper - scale) / 2
            result[..., :2] = (
                padded[..., :2] - center_offset.astype(np.float64)
            ) / scale
            result[..., :2] = (result[..., :2] - 0.5) * 2
            result = np.clip(result, -1, 1)
    if not np.isfinite(result).all():
        raise ValueError("preprocessing produced a non-finite tensor")
    stages["spatial_normalization"] = result
    return (result, stages) if return_stages else result
