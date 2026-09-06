from __future__ import annotations

from pathlib import Path

import pytest

from pose_embed.config import load_protocol
from pose_embed.data import ManifestRecord, build_manifest_records, parse_ntu_sample_id
from pose_embed.data.manifest import verify_manifests


def test_ntu_parser_exposes_synchronized_performance_identity() -> None:
    first = parse_ntu_sample_id("/data/S001C001P002R002A115.skeleton")
    second = parse_ntu_sample_id("S001C003P002R002A115.npy")

    assert first.sample_id == "S001C001P002R002A115"
    assert first.performance_id == second.performance_id
    assert first.camera != second.camera


@pytest.mark.parametrize(
    "sample_id",
    [
        "S033C001P001R001A001",
        "S001C004P001R001A001",
        "S001C001P107R001A001",
        "S001C001P001R003A001",
    ],
)
def test_ntu_parser_rejects_ids_outside_dataset_ranges(sample_id: str) -> None:
    with pytest.raises(ValueError, match="must be in"):
        parse_ntu_sample_id(sample_id)


def test_manifest_builder_excludes_anchor_camera_views_from_primary(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    synchronized = "S001C001P008R001A001"
    independent = "S002C001P002R001A001"
    anchors = list(protocol.dataset.official_one_shot_exemplars)
    records = build_manifest_records(
        [
            *anchors,
            synchronized,
            independent,
            "S001C001P003R001A002",
            "S001C001P004R001A003",
        ],
        anchors,
        protocol,
    )

    primary = {row.sample_id for row in records if row.split == "novel_query_primary"}
    official = {row.sample_id for row in records if row.split == "novel_query_official"}
    assert primary == {independent}
    assert official == {synchronized, independent}
    summary = verify_manifests(records, protocol)
    assert summary["records"] == len(records)


def test_manifest_builder_rejects_nonofficial_one_shot_exemplars(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    samples = [*protocol.dataset.official_one_shot_exemplars]
    samples[0] = "S001C001P001R001A001"

    with pytest.raises(ValueError, match="official one-shot exemplars"):
        build_manifest_records(samples, samples, protocol)


def test_manifest_verifier_rejects_primary_anchor_performance_leakage(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    rows = [
        ManifestRecord(
            sample_id="S001C001P001R001A001",
            split="novel_anchor",
            is_anchor=True,
        ),
        ManifestRecord(
            sample_id="S001C002P001R001A001",
            split="novel_query_primary",
        ),
    ]

    with pytest.raises(ValueError, match="shares the anchor performance"):
        verify_manifests(rows, protocol)


def test_manifest_file_check_enforces_declared_checksum(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    filename = "S001C001P001R001A003.bin"
    (tmp_path / filename).write_bytes(b"licensed fixture")
    row = ManifestRecord(
        sample_id="S001C001P001R001A003",
        relative_path=filename,
        split="development_train",
        sha256="0" * 64,
    )
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_manifests([row], protocol, data_root=tmp_path, check_files=True)


def test_complete_manifest_validation_rejects_partial_fixture(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    row = ManifestRecord(
        sample_id="S001C001P001R001A003",
        split="development_train",
    )

    with pytest.raises(ValueError, match="missing splits"):
        verify_manifests([row], protocol, require_complete=True)


def test_parser_and_manifest_reject_sample_aliases_and_unsafe_paths(
    protocol_path: Path,
) -> None:
    with pytest.raises(ValueError, match="canonical NTU sample filename"):
        parse_ntu_sample_id("copy-S001C001P001R001A003.npy")
    with pytest.raises(ValueError, match="normalized"):
        ManifestRecord(
            sample_id="S001C001P001R001A003",
            relative_path="../S001C001P001R001A003.npy",
            split="development_train",
        )
    with pytest.raises(ValueError, match="identify sample_id"):
        ManifestRecord(
            sample_id="S001C001P001R001A003",
            relative_path="S001C001P001R001A004.npy",
            split="development_train",
        )
    with pytest.raises(ValueError, match="canonical NTU sample filename"):
        ManifestRecord(
            sample_id="S001C001P001R001A003",
            relative_path="ntu120_hrnet.pkl",
            split="development_train",
            sha256="a" * 64,
        )

    protocol = load_protocol(protocol_path)
    rows = [
        ManifestRecord(
            sample_id="S001C001P001R001A003",
            relative_path=path,
            split=split,
        )
        for path, split in (
            ("first/S001C001P001R001A003.npy", "development_train"),
            ("second/S001C001P001R001A003.npy", "final_train"),
        )
    ]
    with pytest.raises(ValueError, match="path aliases"):
        verify_manifests(rows, protocol)
