from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from pose_embed.artifacts import FeatureSidecar, validate_feature_artifact
from pose_embed.config import load_protocol
from pose_embed.data import ManifestRecord
from pose_embed.features import extract_fixture_features
from pose_embed.provenance import sha256_file


def _training_fixture(tmp_path: Path) -> tuple[Path, Path]:
    sample_ids = np.asarray(
        [
            "S001C001P001R001A003",
            "S002C001P001R001A003",
            "S003C001P001R001A003",
            "S004C001P001R001A003",
            "S001C001P002R001A004",
            "S002C001P002R001A004",
            "S003C001P002R001A004",
            "S004C001P002R001A004",
        ]
    )
    input_path = tmp_path / "poses.npz"
    np.savez(
        input_path,
        poses=np.ones((8, 1, 6, 17, 3), dtype=np.float32),
        labels=np.asarray([3] * 4 + [4] * 4),
        sample_ids=sample_ids,
    )
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=str(sample_id), split="development_train"
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )
    return input_path, manifest_path


def test_feature_sidecar_is_required_hash_complete_and_tamper_evident(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    input_path, manifest_path = _training_fixture(tmp_path)
    output_path = tmp_path / "features.npz"
    extract_fixture_features(
        input_path,
        output_path,
        protocol_path=protocol_path,
        manifest_path=manifest_path,
        role="training",
        split="development_train",
        embedding_dimension=6,
    )

    protocol = load_protocol(protocol_path)
    sidecar = validate_feature_artifact(
        output_path,
        protocol=protocol,
        manifest_path=manifest_path,
        allow_fixture=True,
    )
    assert sidecar.role == "training"
    assert sidecar.shape == (8, 6)
    assert sidecar.dtype == "float32"
    assert sidecar.scientific_use_allowed is False
    for digest in (
        sidecar.protocol_sha256,
        sidecar.manifest_sha256,
        sidecar.sample_order_sha256,
        sidecar.preprocessing_sha256,
        sidecar.upstream_sha256,
        sidecar.encoder_checkpoint_sha256,
        sidecar.artifact_sha256,
    ):
        assert len(digest) == 64

    with pytest.raises(ValueError, match="scientific use"):
        validate_feature_artifact(
            output_path, protocol=protocol, manifest_path=manifest_path
        )

    with output_path.open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="artifact hash"):
        validate_feature_artifact(
            output_path,
            protocol=protocol,
            manifest_path=manifest_path,
            allow_fixture=True,
        )


def test_feature_sidecar_cannot_cross_label_backend_or_array_stage(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    input_path, manifest_path = _training_fixture(tmp_path)
    output_path = tmp_path / "features.npz"
    extract_fixture_features(
        input_path,
        output_path,
        protocol_path=protocol_path,
        manifest_path=manifest_path,
        role="training",
        split="development_train",
        embedding_dimension=6,
    )
    sidecar = validate_feature_artifact(
        output_path,
        protocol=load_protocol(protocol_path),
        manifest_path=manifest_path,
        allow_fixture=True,
    )

    wrong_backend_method = sidecar.model_dump()
    wrong_backend_method["role"] = "gallery_clean"
    wrong_backend_method["split"] = "development_validation"
    wrong_backend_method["method"] = "frozen_encoder_cache"
    wrong_backend_method["training_seed"] = 7
    with pytest.raises(ValueError, match="backend"):
        FeatureSidecar.model_validate(wrong_backend_method)

    wrong_array_stage = sidecar.model_dump()
    wrong_array_stage["array_key"] = "embeddings"
    with pytest.raises(ValueError, match="pre-head"):
        FeatureSidecar.model_validate(wrong_array_stage)


def test_missing_feature_sidecar_fails_closed(
    protocol_path: Path, tmp_path: Path
) -> None:
    artifact = tmp_path / "orphan.npz"
    np.savez(artifact, features=np.eye(2), labels=[1, 2], sample_ids=["a", "b"])

    with pytest.raises(ValueError, match="sidecar"):
        validate_feature_artifact(
            artifact,
            protocol=load_protocol(protocol_path),
            manifest_path=tmp_path / "missing.jsonl",
            allow_fixture=True,
        )


def test_extraction_rejects_unregistered_corruption_before_writing(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    poses = tmp_path / "query-poses.npz"
    manifest = tmp_path / "query-manifest.jsonl"
    output = tmp_path / "invalid-corruption.npz"
    sample_ids = ["S001C001P001R001A002", "S002C001P002R001A002"]
    np.savez(
        poses,
        poses=np.ones((2, 1, 6, 17, 3), dtype=np.float32),
        labels=np.asarray([2, 2]),
        sample_ids=sample_ids,
    )
    manifest.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id,
                split="development_validation",
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="absent from protocol"):
        extract_fixture_features(
            poses,
            output,
            protocol_path=protocol_path,
            manifest_path=manifest,
            role="query_corrupted",
            split="development_validation",
            corruption_family="coordinate_jitter",
            corruption_severity=0.03,
        )
    assert not output.exists()


def test_feature_validation_rejects_nonfinite_arrays(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    input_path, manifest_path = _training_fixture(tmp_path)
    output_path = tmp_path / "features.npz"
    extract_fixture_features(
        input_path,
        output_path,
        protocol_path=protocol_path,
        manifest_path=manifest_path,
        role="training",
        split="development_train",
        embedding_dimension=6,
    )
    with np.load(output_path, allow_pickle=False) as archive:
        payload = {key: np.asarray(archive[key]) for key in archive.files}
    payload["features"] = payload["features"].copy()
    payload["features"][0, 0] = np.nan
    np.savez(output_path, **payload)
    sidecar_path = output_path.with_suffix(f"{output_path.suffix}.manifest.json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    sidecar["artifact_sha256"] = sha256_file(output_path)
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

    with pytest.raises(ValueError, match="finite"):
        validate_feature_artifact(
            output_path,
            protocol=load_protocol(protocol_path),
            manifest_path=manifest_path,
            allow_fixture=True,
        )
