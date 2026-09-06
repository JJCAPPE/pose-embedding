from __future__ import annotations

import pytest
import torch

from pose_embed.corruptions import (
    apply_corruption,
    consecutive_frame_mask,
    coordinate_jitter,
    joint_mask,
)


def _pose() -> torch.Tensor:
    pose = torch.ones(1, 100, 17, 3)
    pose[:, :, [11, 14], 1] = 0.0
    pose[:, :, [4, 1], 1] = 2.0
    return pose


def test_zero_severity_is_byte_identical_and_returns_copy() -> None:
    pose = _pose()
    result = apply_corruption(
        pose, family="coordinate_jitter", severity=0, sample_id="sample"
    )
    assert torch.equal(result, pose)
    assert result.data_ptr() != pose.data_ptr()


def test_jitter_is_paired_by_sample_and_preserves_confidence() -> None:
    pose = _pose()
    pose[:, :, 3, :] = 0
    first = coordinate_jitter(pose, fraction=0.025, sample_id="sample-a")
    second = coordinate_jitter(pose, fraction=0.025, sample_id="sample-a")
    other = coordinate_jitter(pose, fraction=0.025, sample_id="sample-b")

    assert torch.equal(first, second)
    assert not torch.equal(first[..., :2], other[..., :2])
    assert torch.equal(first[..., 2], pose[..., 2])
    assert torch.equal(first[:, :, 3], pose[:, :, 3])


def test_joint_and_frame_masks_affect_exact_requested_extent() -> None:
    pose = _pose()
    joints = joint_mask(pose, count=6, sample_id="sample")
    completely_zero_joints = (joints == 0).all(dim=(0, 1, 3))
    assert int(completely_zero_joints.sum()) == 6

    frames = consecutive_frame_mask(pose, count=25, sample_id="sample")
    completely_zero_frames = (frames == 0).all(dim=(0, 2, 3))
    indexes = torch.where(completely_zero_frames)[0]
    assert len(indexes) == 25
    assert int(indexes[-1] - indexes[0]) == 24
    assert torch.equal(pose, _pose())


def test_count_corruptions_reject_fractional_severity() -> None:
    with pytest.raises(ValueError, match="integer"):
        apply_corruption(_pose(), family="joint_mask", severity=3.5, sample_id="sample")


def test_corruptions_reject_missing_confidence_even_at_zero_severity() -> None:
    with pytest.raises(ValueError, match="x, y, confidence"):
        apply_corruption(
            _pose()[..., :2],
            family="coordinate_jitter",
            severity=0,
            sample_id="sample",
        )
