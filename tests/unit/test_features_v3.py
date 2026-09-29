from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
import torch.nn.functional as functional
import yaml

from pose_embed.artifacts import FeatureSidecar, validate_feature_artifact
from pose_embed.config import load_protocol
from pose_embed.corruptions.pose import apply_corruption_v3
from pose_embed.features import extract_fixture_features
from pose_embed.motionbert_features import (
    extraction_condition,
    validate_motionbert_cache,
)


def _fixture(tmp_path: Path, *, own_scale: bool = True, resolved: bool = False):
    protocol_path = Path("configs/protocol.v3.yaml")
    if resolved:
        document = yaml.safe_load(protocol_path.read_text())
        document["status"] = "resolved"
        binding = {"relative_path": "study-v3/fixture", "sha256": "a" * 64}
        document["preparation"] = {
            "auxiliary_container": binding,
            "fallback_evidence": binding,
            "fallback_value": 2.5,
            "source_inventory": binding,
            "identities": binding,
            "encoder_checkpoint_sha256": "a" * 64,
            "upstream_sha256": {
                key: "a" * 64
                for key in ("upstream_sha256", "config_sha256", "license_sha256")
            },
        }
        protocol_path = tmp_path / "fixture-protocol.v3.yaml"
        protocol_path.write_text(yaml.safe_dump(document))
    pose = torch.ones(2, 100, 17, 3)
    pose[..., 0] = torch.arange(100, dtype=torch.float32)[None, :, None]
    pose[..., 1] = torch.arange(17, dtype=torch.float32)[None, None, :]
    if not own_scale:
        pose[:, :, [11, 14, 4, 1], 2] = 0
    sample_id = "S001C001P001R001A002"
    source = tmp_path / "poses.npz"
    np.savez(
        source,
        poses=pose[None].numpy(),
        labels=np.asarray([2]),
        sample_ids=np.asarray([sample_id]),
    )
    manifest = tmp_path / "query.jsonl"
    manifest.write_text(
        json.dumps({"sample_id": sample_id, "split": "development_validation"}) + "\n"
    )
    return source, manifest, protocol_path, pose, sample_id


@pytest.mark.parametrize(
    "family,severity",
    [("coordinate_jitter", 0.025), ("joint_mask", 8), ("frame_mask", 25)],
)
def test_v3_fixture_features_use_exact_versioned_operators(tmp_path, family, severity):
    source, manifest, protocol_path, pose, sample_id = _fixture(tmp_path)
    output = tmp_path / "features.npz"
    payload = extract_fixture_features(
        source,
        output,
        protocol_path=protocol_path,
        manifest_path=manifest,
        role="query_corrupted",
        split="development_validation",
        embedding_dimension=8,
        corruption_family=family,
        corruption_severity=severity,
    )
    corrupted = apply_corruption_v3(
        pose, family=family, severity=severity, sample_id=sample_id
    )
    with np.load(output) as archive:
        projection = torch.from_numpy(archive["fixture_projection"])
        expected = functional.normalize(
            corrupted.mean(dim=(0, 1)).flatten()[None] @ projection, dim=1
        )
        np.testing.assert_array_equal(archive["features"], expected.numpy())
    assert payload["scientific_use_allowed"] is False
    protocol = load_protocol(protocol_path)
    with pytest.raises(ValueError, match="not approved for scientific"):
        validate_feature_artifact(output, protocol=protocol, manifest_path=manifest)
    validate_feature_artifact(
        output, protocol=protocol, manifest_path=manifest, allow_fixture=True
    )
    for changes in (
        {"scientific_use_allowed": True},
        {"role": "training"},
        {"split": "novel_anchor"},
        {"condition": "clean"},
    ):
        invalid = deepcopy(payload) | changes
        with pytest.raises(ValueError):
            FeatureSidecar.model_validate(invalid)


def test_v3_fixture_fallback_is_the_protocol_bound_value(tmp_path):
    source, manifest, protocol_path, pose, sample_id = _fixture(
        tmp_path, own_scale=False, resolved=True
    )
    output = tmp_path / "features.npz"
    extract_fixture_features(
        source,
        output,
        protocol_path=protocol_path,
        manifest_path=manifest,
        role="query_corrupted",
        split="development_validation",
        embedding_dimension=8,
        corruption_family="coordinate_jitter",
        corruption_severity=0.05,
    )
    expected_pose = apply_corruption_v3(
        pose,
        family="coordinate_jitter",
        severity=0.05,
        sample_id=sample_id,
        fallback_scale=2.5,
    )
    with np.load(output) as archive:
        expected = functional.normalize(
            expected_pose.mean(dim=(0, 1)).flatten()[None]
            @ torch.from_numpy(archive["fixture_projection"]),
            dim=1,
        )
        np.testing.assert_array_equal(archive["features"], expected.numpy())


def test_v3_fixture_missing_scale_cannot_invent_unresolved_fallback(tmp_path):
    source, manifest, protocol_path, _, _ = _fixture(tmp_path, own_scale=False)
    output = tmp_path / "features.npz"
    with pytest.raises(ValueError, match="frozen fallback"):
        extract_fixture_features(
            source,
            output,
            protocol_path=protocol_path,
            manifest_path=manifest,
            role="query_corrupted",
            split="development_validation",
            corruption_family="coordinate_jitter",
            corruption_severity=0.05,
        )
    assert not output.exists()


@pytest.mark.parametrize(
    "family,severity",
    [
        ("coordinate_jitter", 0.01),
        ("coordinate_jitter", 0.025),
        ("coordinate_jitter", 0.05),
        ("joint_mask", 3),
        ("joint_mask", 6),
        ("joint_mask", 8),
        ("frame_mask", 10),
        ("frame_mask", 25),
        ("frame_mask", 40),
    ],
)
def test_all_nine_v3_motionbert_query_conditions_are_exact(family, severity):
    assert (
        extraction_condition(
            load_protocol("configs/protocol.v3.yaml"),
            role="query_corrupted",
            split="development_validation",
            family=family,
            severity=severity,
        )
        == f"{family}:{severity:g}"
    )


@pytest.mark.parametrize(
    "role,split,condition",
    [
        ("query_corrupted", "development_validation", "coordinate_jitter:0.02"),
        ("query_corrupted", "development_validation", "frame_mask:10.0"),
        ("query_corrupted", "development_validation", "clean"),
        ("gallery_clean", "development_validation", "joint_mask:3"),
        ("training", "development_train", "joint_mask:3"),
        ("query_corrupted", "novel_query_primary", "joint_mask:3"),
    ],
)
def test_v3_motionbert_cache_rejects_role_and_condition_misuse_before_provenance(
    monkeypatch, role, split, condition
):
    monkeypatch.setattr("pose_embed.protocol_v3.require_v3_design", lambda _: None)
    sidecar = SimpleNamespace(
        provenance={}, role=role, split=split, condition=condition
    )
    with pytest.raises(ValueError, match="(condition|novel extraction)"):
        validate_motionbert_cache(
            sidecar, load_protocol("configs/protocol.v3.yaml"), "unused-manifest"
        )
