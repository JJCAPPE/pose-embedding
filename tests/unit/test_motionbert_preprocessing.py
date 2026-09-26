from __future__ import annotations

import numpy as np
import pytest

from pose_embed.config import load_protocol
from pose_embed.data.motionbert import preprocess_annotation


def annotation(people: int = 1, frames: int = 3, dtype=np.float32) -> dict:
    xy = np.arange(people * frames * 17 * 2, dtype=dtype).reshape(people, frames, 17, 2)
    return {
        "keypoint": xy,
        "keypoint_score": np.ones((people, frames, 17), dtype=dtype),
        "total_frames": frames,
        "img_shape": (480, 640),
    }


@pytest.mark.parametrize("people", [1, 2])
@pytest.mark.parametrize("frames", [1, 3, 100, 153])
@pytest.mark.parametrize("dtype", [np.float16, np.float32])
def test_preprocessing_shape_sampling_padding_and_repeatability(
    protocol_path, people, frames, dtype
) -> None:
    raw = annotation(people, frames, dtype)
    original = raw["keypoint"].copy()
    protocol = load_protocol(protocol_path)
    result, stages = preprocess_annotation(raw, protocol, return_stages=True)

    assert result.shape == (2, 100, 17, 3)
    assert result.dtype == np.float32
    assert np.isfinite(result).all()
    assert np.array_equal(result, preprocess_annotation(raw, protocol))
    assert np.array_equal(original, raw["keypoint"])
    np.testing.assert_array_equal(
        stages["temporal_indices"], np.arange(100) * frames // 100
    )
    np.testing.assert_array_equal(
        stages["camera_normalization"], original / 640 * 2 - 1
    )
    if people == 1:
        assert np.count_nonzero(stages["single_person_padding"][1]) == 0
        assert np.count_nonzero(result[1, ..., 2]) == 0


def test_joint_mapping_uses_declared_coordinates_and_minimum_confidence(
    protocol_path,
) -> None:
    raw = annotation()
    raw["keypoint_score"][:] = np.arange(17) / 20
    _, stages = preprocess_annotation(
        raw, load_protocol(protocol_path), return_stages=True
    )
    camera = stages["camera_normalization"]
    mapped = stages["coordinate_mapping"]
    scores = stages["confidence_mapping"]

    np.testing.assert_array_equal(
        mapped[..., 0, :], (camera[..., 11, :] + camera[..., 12, :]) * 0.5
    )
    np.testing.assert_array_equal(
        mapped[..., 8, :], (camera[..., 5, :] + camera[..., 6, :]) * 0.5
    )
    np.testing.assert_array_equal(
        mapped[..., 7, :], (mapped[..., 0, :] + mapped[..., 8, :]) * 0.5
    )
    np.testing.assert_array_equal(mapped[..., 9, :], camera[..., 0, :])
    for joint, expected_source in {0: 11, 7: 5, 8: 5, 10: 1, 13: 9, 16: 10}.items():
        np.testing.assert_array_equal(
            scores[..., joint], raw["keypoint_score"][..., expected_source]
        )


def test_tracking_keeps_confidence_with_swapped_people(protocol_path) -> None:
    raw = annotation(people=2)
    raw["keypoint"][:] = 0
    raw["keypoint"][0, :, :, 0] = np.array([0, 100, 0])[:, None]
    raw["keypoint"][1, :, :, 0] = np.array([100, 0, 100])[:, None]
    raw["keypoint_score"][0] = np.array([0.2, 0.9, 0.4])[:, None]
    raw["keypoint_score"][1] = np.array([0.8, 0.3, 0.7])[:, None]
    _, stages = preprocess_annotation(
        raw, load_protocol(protocol_path), return_stages=True
    )

    np.testing.assert_array_equal(stages["tracking_indices"], [[0, 1, 0], [1, 0, 1]])
    np.testing.assert_array_equal(
        stages["person_tracking"][0, :, :, 0], -np.ones((3, 17))
    )
    np.testing.assert_allclose(
        stages["confidence_mapping"][..., 9], [[0.2, 0.3, 0.4], [0.8, 0.9, 0.7]]
    )


def test_spatial_crop_uses_positive_confidence_bbox(protocol_path) -> None:
    raw = annotation()
    raw["keypoint"][:] = 100
    raw["keypoint"][..., 0, :] = [0, 0]
    raw["keypoint"][..., 9, :] = [640, 640]
    raw["keypoint_score"][:] = 0
    raw["keypoint_score"][..., [0, 9]] = 1
    result, stages = preprocess_annotation(
        raw, load_protocol(protocol_path), return_stages=True
    )

    # COCO nose/wrist map to H36M nose/left wrist, the two visible bbox corners.
    np.testing.assert_array_equal(result[0, :, 9, :2], -np.ones((100, 2)))
    np.testing.assert_array_equal(result[0, :, 13, :2], np.ones((100, 2)))
    np.testing.assert_array_equal(
        result[..., 2], stages["single_person_padding"][..., 2]
    )


@pytest.mark.parametrize("all_missing", [False, True])
def test_degenerate_pose_returns_zeros(protocol_path, all_missing) -> None:
    raw = annotation()
    raw["keypoint"][:] = 20
    if all_missing:
        raw["keypoint_score"][:] = 0
    assert not preprocess_annotation(raw, load_protocol(protocol_path)).any()


@pytest.mark.parametrize(
    "field,value",
    [("keypoint", np.nan), ("keypoint_score", -np.inf), ("keypoint_score", np.inf)],
)
def test_preprocessing_rejects_invalid_values(protocol_path, field, value) -> None:
    raw = annotation()
    raw[field].flat[0] = value
    with pytest.raises(ValueError, match="finite|confidence"):
        preprocess_annotation(raw, load_protocol(protocol_path))


def test_confidence_is_clipped_only_at_spatial_normalization(protocol_path) -> None:
    raw = annotation()
    raw["keypoint_score"][..., 0] = 1.25
    result, stages = preprocess_annotation(
        raw, load_protocol(protocol_path), return_stages=True
    )
    assert np.all(stages["confidence_mapping"][..., 9] == 1.25)
    assert np.all(result[0, :, 9, 2] == 1)


def test_preprocessing_rejects_wrong_frame_count(protocol_path) -> None:
    raw = annotation()
    raw["total_frames"] = 4
    with pytest.raises(ValueError, match="nonempty COCO17"):
        preprocess_annotation(raw, load_protocol(protocol_path))
