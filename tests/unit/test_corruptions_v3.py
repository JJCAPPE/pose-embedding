from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import torch

from pose_embed.corruptions.fallback import (
    collect_torso_fallback_v3,
    validate_torso_fallback_v3,
    write_torso_fallback_v3,
)
from pose_embed.corruptions.pose import (
    apply_corruption_v3,
    corruption_randomness_v3,
    torso_scale_v3,
)


def _pose(scale: float = 2.0) -> torch.Tensor:
    pose = torch.zeros(2, 100, 17, 3)
    pose[0, ..., 2] = 1
    pose[0, :, [4, 1], 1] = scale
    return pose


def _id(action: int) -> str:
    return f"S001C001P001R001A{action:03}"


def test_v3_randomness_exact_domain_without_severity() -> None:
    unsigned, seed = corruption_randomness_v3(_id(3), "frame_mask")
    digest = hashlib.sha256(b"protocol-v3\0S001C001P001R001A003\0frame_mask").digest()
    assert unsigned == int.from_bytes(digest[:8], "big")
    assert seed == unsigned & (2**63 - 1)


@pytest.mark.parametrize("family", ["coordinate_jitter", "joint_mask", "frame_mask"])
def test_v3_zero_is_bitwise_copy_without_scale(family: str) -> None:
    pose = torch.zeros(2, 100, 17, 3)
    pose[0, :, 0, 0] = -0.0
    output = apply_corruption_v3(pose, family=family, severity=0, sample_id="a")
    assert output.numpy().tobytes() == pose.numpy().tobytes()
    assert output.data_ptr() != pose.data_ptr()


def test_v3_jitter_uses_shared_cpu_field_and_exact_missingness() -> None:
    pose = _pose()
    pose[0, :, 3, 2] = 0
    pose[0, :, 3, 0] = -0.0
    original = pose.clone()
    _, seed = corruption_randomness_v3("paired", "coordinate_jitter")
    generator = torch.Generator(device="cpu").manual_seed(seed)
    field = torch.randn((2, 100, 17, 2), generator=generator, dtype=torch.float32)
    for fraction in (0.01, 0.025, 0.05):
        result = apply_corruption_v3(
            pose, family="coordinate_jitter", severity=fraction, sample_id="paired"
        )
        # Joint 0 is at the origin, making the scaled field directly observable.
        assert torch.equal(result[0, :, 0, :2], field[0, :, 0] * 2 * fraction)
        assert result[..., 2].numpy().tobytes() == pose[..., 2].numpy().tobytes()
        absent = pose[..., 2] <= 0
        assert result[absent].numpy().tobytes() == pose[absent].numpy().tobytes()
        assert torch.equal(
            result,
            apply_corruption_v3(
                pose, family="coordinate_jitter", severity=fraction, sample_id="paired"
            ),
        )
    assert torch.equal(pose, original)


def test_v3_torso_uses_lower_median_and_positive_four_joint_support() -> None:
    pose = _pose(0)
    pose[0, :, [4, 1], 1] = torch.arange(1, 101, dtype=torch.float32)[:, None]
    assert torso_scale_v3(pose) == 50
    pose[0, 0, 11, 2] = 0
    assert torso_scale_v3(pose) == 51
    pose[..., 2] = 0
    assert torso_scale_v3(pose) is None
    pose[0, :, 0, 2] = 1
    with pytest.raises(ValueError, match="fallback"):
        apply_corruption_v3(
            pose, family="coordinate_jitter", severity=0.01, sample_id="fallback"
        )
    result = apply_corruption_v3(
        pose,
        family="coordinate_jitter",
        severity=0.01,
        sample_id="fallback",
        fallback_scale=2.0,
    )
    assert not torch.equal(result[0, :, 0, :2], pose[0, :, 0, :2])
    assert torch.equal(result[:, :, 1:], pose[:, :, 1:])


@pytest.mark.parametrize("sample_id", [f"nested-{i}" for i in range(20)])
def test_v3_joint_and_frame_masks_are_nested_across_both_people(sample_id: str) -> None:
    pose = torch.ones(2, 100, 17, 3)
    for family, severities, dimensions in (
        ("joint_mask", (3, 6, 8), (0, 1, 3)),
        ("frame_mask", (10, 25, 40), (0, 2, 3)),
    ):
        previous: set[int] = set()
        for severity in severities:
            result = apply_corruption_v3(
                pose, family=family, severity=severity, sample_id=sample_id
            )
            masked = set(torch.where((result == 0).all(dim=dimensions))[0].tolist())
            assert len(masked) == severity
            assert previous <= masked
            assert result.shape == pose.shape
            if family == "frame_mask":
                assert max(masked) - min(masked) == severity - 1
            previous = masked
    assert torch.equal(pose, torch.ones_like(pose))


@pytest.mark.parametrize("unsigned", [0, 2**64 - 1])
def test_v3_frame_boundary_intervals(monkeypatch: pytest.MonkeyPatch, unsigned: int):
    monkeypatch.setattr(
        "pose_embed.corruptions.pose.corruption_randomness_v3",
        lambda *args: (unsigned, unsigned & (2**63 - 1)),
    )
    for length in (10, 25, 40):
        result = apply_corruption_v3(
            torch.ones(2, 100, 17, 3),
            family="frame_mask",
            severity=length,
            sample_id="boundary",
        )
        masked = torch.where((result == 0).all(dim=(0, 2, 3)))[0]
        assert masked.tolist() == (
            list(range(length)) if unsigned == 0 else list(range(100 - length, 100))
        )


def test_v3_masks_do_not_replace_already_missing_joints() -> None:
    pose = torch.ones(2, 100, 17, 3)
    result = apply_corruption_v3(
        pose, family="joint_mask", severity=3, sample_id="absent"
    )
    assert torch.equal(
        result,
        apply_corruption_v3(
            result, family="joint_mask", severity=3, sample_id="absent"
        ),
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_v3_rejects_nonfinite_sources_even_at_zero_severity(value: float) -> None:
    pose = _pose()
    pose[1, 0, 0, 0] = value
    with pytest.raises(ValueError, match="finite"):
        apply_corruption_v3(pose, family="joint_mask", severity=0, sample_id="bad")


@pytest.mark.parametrize("severity", [-1, 1, 3.5, float("nan"), True])
def test_v3_rejects_undeclared_levels(severity: float) -> None:
    with pytest.raises(ValueError, match="declared"):
        apply_corruption_v3(
            _pose(), family="joint_mask", severity=severity, sample_id="bad"
        )


def _fallback_samples() -> list[tuple[str, torch.Tensor]]:
    samples = [
        (_id(action), _pose(scale))
        for action, scale in zip((3, 4, 5, 6), (1, 2, 50, 100), strict=True)
    ]
    # Only one person/frame contributes for the largest scale: never weight
    # sample-level medians by their number of valid person/frame observations.
    samples[-1][1][0, 1:, :, 2] = 0
    samples.append((_id(9), torch.zeros(2, 100, 17, 3)))
    return samples


def _collect(samples=None):
    samples = _fallback_samples() if samples is None else samples
    return collect_torso_fallback_v3(
        iter(samples),
        expected_sample_ids=[sample_id for sample_id, _ in samples],
        source_inventory_sha256="a" * 64,
        source_manifest_sha256="b" * 64,
        preprocessing_sha256="c" * 64,
    )


def test_v3_fallback_lower_median_manifest_binding_and_immutable_record(tmp_path: Path):
    record = _collect()
    assert record["fallback_scale"] == 2
    assert record["contributing_count"] == 4
    assert record["sample_count"] == 5
    assert record["fallback_required_count"] == 1
    assert (
        validate_torso_fallback_v3(
            record,
            expected_sample_ids=[sample_id for sample_id, _ in _fallback_samples()],
        )
        == 2
    )
    destination = tmp_path / "fallback.json"
    write_torso_fallback_v3(destination, record)
    assert validate_torso_fallback_v3(json.loads(destination.read_text())) == 2
    with pytest.raises(ValueError, match="overwrite immutable"):
        write_torso_fallback_v3(destination, record)
    with pytest.raises(ValueError, match="source_inventory"):
        validate_torso_fallback_v3(record, source_inventory_sha256="d" * 64)
    for key, replacement in (
        ("fallback_scale", 3.0),
        ("contributing_count", 5),
        ("sample_scales", [1.0, 2.0, 3.0, 4.0]),
        ("contributing_sample_ids", [_id(i) for i in (9, 4, 5, 6)]),
    ):
        mutated = deepcopy(record)
        mutated[key] = replacement
        with pytest.raises(ValueError):
            validate_torso_fallback_v3(mutated)


@pytest.mark.parametrize("action", [1, 2, 7, 8, 115, 116])
def test_v3_fallback_rejects_novel_and_validation_actions(action: int) -> None:
    with pytest.raises(ValueError, match="80-action"):
        _collect([(_id(action), _pose())])


def test_v3_fallback_rejects_missing_out_of_order_and_nonfinite_sources() -> None:
    kwargs = {
        "expected_sample_ids": [_id(3), _id(4)],
        "source_inventory_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64,
        "preprocessing_sha256": "c" * 64,
    }
    with pytest.raises(ValueError, match="missing"):
        collect_torso_fallback_v3([(_id(3), _pose())], **kwargs)
    with pytest.raises(ValueError, match="ordered"):
        collect_torso_fallback_v3([(_id(4), _pose())], **kwargs)
    with pytest.raises(ValueError, match="no positive"):
        _collect([(_id(3), torch.zeros(2, 100, 17, 3))])
    broken = _pose()
    broken[0, 0, 0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        _collect([(_id(3), broken)])


def test_v3_corruptions_repeat_in_fresh_processes() -> None:
    script = """
import hashlib
import torch
from pose_embed.corruptions.pose import apply_corruption_v3
p = torch.ones(2,100,17,3)
p[:,:,[4,1],1] = 2
cells = [('coordinate_jitter', .025), ('joint_mask', 8), ('frame_mask', 40)]
for family, severity in cells:
    q = apply_corruption_v3(p, family=family, severity=severity, sample_id='fresh')
    print(hashlib.sha256(q.numpy().tobytes()).hexdigest())
"""
    first = subprocess.check_output([sys.executable, "-c", script], text=True)
    second = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert first == second
    assert len(first.splitlines()) == 3
