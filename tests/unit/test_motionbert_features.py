from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from pose_embed.config import load_protocol
from pose_embed.data.manifest import ManifestRecord
from pose_embed.motionbert_features import (
    extract_motionbert_features,
    validate_selected_manifest,
    write_feature_npz,
)
from pose_embed.provenance import sha256_file, write_immutable_json


def test_npz_is_byte_identical_and_published_without_overwrite(tmp_path: Path) -> None:
    features = np.arange(3 * 8704, dtype=np.float32).reshape(3, 8704)
    labels = np.asarray([3, 4, 5], dtype=np.int64)
    ids = np.asarray([f"S001C001P001R001A{label:03d}" for label in labels])
    first, second = tmp_path / "first.npz", tmp_path / "second.npz"
    write_feature_npz(first, features, labels, ids)
    write_feature_npz(second, features, labels, ids)
    assert sha256_file(first) == sha256_file(second)
    with np.load(first, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["features"], features)
    with pytest.raises(ValueError, match="overwrite"):
        write_feature_npz(first, features + 1, labels, ids)
    assert sha256_file(first) == sha256_file(second)
    assert not list(tmp_path.glob(".*"))


def test_invalid_json_is_never_published(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    with pytest.raises(ValueError):
        write_immutable_json(output, {"metric": float("nan")})
    assert not output.exists()
    assert not list(tmp_path.iterdir())


def test_training_manifest_must_be_the_complete_ordered_split(
    tmp_path: Path, protocol_path: Path
) -> None:
    records = [
        ManifestRecord(
            sample_id=f"S001C001P001R001A{action:03d}", split="development_train"
        )
        for action in (3, 4)
    ]
    manifest = tmp_path / "training.jsonl"
    manifest.write_text(records[0].model_dump_json() + "\n")
    with pytest.raises(ValueError, match="complete ordered split"):
        validate_selected_manifest(
            {"development-train.jsonl": records},
            load_protocol(protocol_path),
            manifest,
            role="training",
            split="development_train",
        )


@pytest.mark.parametrize(
    "split,role",
    [
        ("novel_anchor", "gallery_clean"),
        ("novel_query_primary", "query_clean"),
        ("development_validation", "query_corrupted"),
    ],
)
def test_week3_refuses_novel_or_corrupted_extraction_before_loading(
    tmp_path: Path, protocol_path: Path, split: str, role: str
) -> None:
    with pytest.raises(ValueError, match="clean auxiliary"):
        extract_motionbert_features(
            tmp_path / "absent.pkl",
            tmp_path / "features.npz",
            protocol_path=protocol_path,
            manifest_path=tmp_path / "absent.jsonl",
            manifest_set_path=tmp_path / "absent.json",
            parity_evidence_path=tmp_path / "parity.json",
            role=role,
            split=split,
        )
    assert not (tmp_path / "features.npz").exists()


def test_legacy_extraction_rejects_v2_opening_before_input_loading(
    tmp_path: Path, protocol_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    ledger = tmp_path / "benchmark-v2/locks/test-opening.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="forbidden after benchmark v2 opening"):
        extract_motionbert_features(
            tmp_path / "absent.pkl",
            tmp_path / "features.npz",
            protocol_path=protocol_path,
            manifest_path=tmp_path / "absent.jsonl",
            manifest_set_path=tmp_path / "absent.json",
            parity_evidence_path=tmp_path / "parity.json",
            role="training",
            split="development_train",
        )
    assert not (tmp_path / "features.npz").exists()
