from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
import pytest

from pose_embed.cli import main
from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.inventory import (
    NTUInventoryRecord,
    build_split_manifests,
    inspect_ntu_aggregate,
    load_inventory,
    verify_split_manifests,
    write_manifest_bundle,
)
from pose_embed.protocol import (
    EvaluationPlan,
    load_evaluation_plan,
    validate_evaluation_manifests,
)


def _annotation(
    sample_id: str,
    *,
    pose_tracks: int = 1,
    frames: int = 2,
) -> dict[str, object]:
    action = int(sample_id[-3:])
    return {
        "frame_dir": sample_id,
        "label": action - 1,
        "img_shape": (1080, 1920),
        "original_shape": (1080, 1920),
        "total_frames": frames,
        "keypoint": np.ones((pose_tracks, frames, 17, 2), dtype=np.float16),
        "keypoint_score": np.ones((pose_tracks, frames, 17), dtype=np.float16),
    }


def _write_source_files(
    root: Path,
    annotations: list[dict[str, object]],
    *,
    missing_ids: tuple[str, ...] = (),
    missing_header: str = "",
) -> Path:
    aggregate_path = root / "ntu120_hrnet.pkl"
    sample_ids = [str(row["frame_dir"]) for row in annotations]
    with aggregate_path.open("wb") as stream:
        pickle.dump(
            {
                "annotations": annotations,
                "split": {
                    "xsub_train": sample_ids,
                    "xsub_val": [],
                    "xset_train": sample_ids,
                    "xset_val": [],
                },
            },
            stream,
        )
    missing_path = root / "missing.txt"
    missing_payload = (
        missing_header + "".join(f"{sample_id}\n" for sample_id in missing_ids)
    ).encode()
    missing_path.write_bytes(missing_payload)
    metadata_path = root / "source.json"
    metadata_path.write_text(
        json.dumps(
            {
                "filename": aggregate_path.name,
                "bytes": aggregate_path.stat().st_size,
                "sha256": hashlib.sha256(aggregate_path.read_bytes()).hexdigest(),
                "format_validation": {"annotation_count": len(annotations)},
                "official_missing_skeletons": {
                    "filename": missing_path.name,
                    "bytes": missing_path.stat().st_size,
                    "sha256": hashlib.sha256(missing_payload).hexdigest(),
                    "count": len(missing_ids),
                    "present_in_aggregate": 0,
                },
                "protocol_count_status": {
                    "nominal_capture_count": len(annotations) + len(missing_ids),
                    "usable_annotation_count": len(annotations),
                },
            }
        ),
        encoding="utf-8",
    )
    return metadata_path


def _complete_annotations(protocol_path: Path) -> list[dict[str, object]]:
    protocol = load_protocol(protocol_path)
    novel_actions = set(protocol.dataset.novel_actions)
    anchors = {
        int(sample_id[-3:]): sample_id
        for sample_id in protocol.dataset.official_one_shot_exemplars
    }
    annotations: list[dict[str, object]] = []
    for action in range(1, 121):
        if action not in novel_actions:
            annotations.append(
                _annotation(f"S002C001P{((action - 1) % 106) + 1:03d}R001A{action:03d}")
            )
            continue
        anchor = anchors[action]
        annotations.extend(
            [
                _annotation(anchor),
                _annotation(anchor.replace("C003", "C001")),
                _annotation(anchor.replace("C003", "C002")),
                _annotation(f"S002C001P009R002A{action:03d}"),
            ]
        )
    return sorted(annotations, key=lambda row: str(row["frame_dir"]))


def _synthetic_protocol(protocol_path: Path, metadata_path: Path) -> ProtocolConfig:
    protocol = load_protocol(protocol_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    missing = metadata["official_missing_skeletons"]
    source_contract = protocol.dataset.source_contract.model_copy(
        update={
            "aggregate_relative_path": metadata["filename"],
            "aggregate_bytes": metadata["bytes"],
            "aggregate_sha256": metadata["sha256"],
            "missing_list_relative_path": missing["filename"],
            "missing_list_bytes": missing["bytes"],
            "missing_list_sha256": missing["sha256"],
            "missing_sample_count": missing["count"],
            "nominal_capture_count": metadata["protocol_count_status"][
                "nominal_capture_count"
            ],
        }
    )
    return protocol.model_copy(
        update={
            "dataset": protocol.dataset.model_copy(
                update={
                    "expected_source_sample_count": metadata["format_validation"][
                        "annotation_count"
                    ],
                    "source_contract": source_contract,
                }
            )
        }
    )


def test_aggregate_hash_is_verified_before_pickle_loading(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    aggregate = tmp_path / "ntu120_hrnet.pkl"
    aggregate.write_bytes(b"not a pickle")
    metadata_path = tmp_path / "source.json"
    metadata_path.write_text(
        json.dumps(
            {
                "filename": aggregate.name,
                "bytes": aggregate.stat().st_size,
                "sha256": "0" * 64,
                "format_validation": {"annotation_count": 1},
                "official_missing_skeletons": {
                    "filename": "missing.txt",
                    "bytes": 0,
                    "sha256": "0" * 64,
                    "count": 0,
                    "present_in_aggregate": 0,
                },
                "protocol_count_status": {
                    "nominal_capture_count": 1,
                    "usable_annotation_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="aggregate SHA-256 mismatch"):
        inspect_ntu_aggregate(tmp_path, metadata_path, load_protocol(protocol_path))


def test_aggregate_annotations_become_normalized_inventory_records(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    metadata_path = _write_source_files(
        tmp_path,
        [_annotation("S001C002P003R002A004", pose_tracks=2, frames=3)],
    )

    inventory = inspect_ntu_aggregate(
        tmp_path, metadata_path, load_protocol(protocol_path)
    )

    assert len(inventory.records) == 1
    assert inventory.records[0].model_dump(mode="json") == {
        "sample_id": "S001C002P003R002A004",
        "annotation_index": 0,
        "setup": 1,
        "camera": 2,
        "performer": 3,
        "repetition": 2,
        "action": 4,
        "label": 3,
        "pose_track_count": 2,
        "nonempty_track_count": 2,
        "total_frames": 3,
        "keypoint_shape": [2, 3, 17, 2],
        "keypoint_score_shape": [2, 3, 17],
        "image_shape": [1080, 1920],
        "original_shape": [1080, 1920],
    }


def test_inventory_record_rejects_identity_metadata_drift() -> None:
    with pytest.raises(ValueError, match="identity metadata"):
        NTUInventoryRecord(
            sample_id="S001C002P003R002A004",
            annotation_index=0,
            setup=1,
            camera=2,
            performer=3,
            repetition=2,
            action=5,
            label=3,
            pose_track_count=1,
            nonempty_track_count=1,
            total_frames=2,
            keypoint_shape=(1, 2, 17, 2),
            keypoint_score_shape=(1, 2, 17),
            image_shape=(1080, 1920),
            original_shape=(1080, 1920),
        )


def test_aggregate_inventory_rejects_duplicate_identifiers(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    duplicate = _annotation("S001C001P001R001A001")
    metadata_path = _write_source_files(tmp_path, [duplicate, duplicate.copy()])

    with pytest.raises(ValueError, match="duplicate annotation sample IDs"):
        inspect_ntu_aggregate(tmp_path, metadata_path, load_protocol(protocol_path))


def test_split_builder_materializes_all_seven_exact_views(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)

    manifests = build_split_manifests(inventory.records, protocol)

    assert {name: len(rows) for name, rows in manifests.items()} == {
        "development-train.jsonl": 80,
        "development-validation.jsonl": 20,
        "final-train.jsonl": 100,
        "official-novel.jsonl": 80,
        "novel-anchor.jsonl": 20,
        "novel-query-primary.jsonl": 20,
        "novel-query-official.jsonl": 60,
    }
    ids = {
        name: {record.sample_id for record in rows} for name, rows in manifests.items()
    }
    assert ids["final-train.jsonl"] == (
        ids["development-train.jsonl"] | ids["development-validation.jsonl"]
    )
    assert ids["official-novel.jsonl"] == (
        ids["novel-anchor.jsonl"] | ids["novel-query-official.jsonl"]
    )
    assert ids["novel-query-primary.jsonl"] < ids["novel-query-official.jsonl"]


def test_split_verifier_rejects_unstable_query_order(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)
    manifests = build_split_manifests(inventory.records, protocol)
    manifests["novel-query-official.jsonl"].reverse()

    with pytest.raises(ValueError, match="stable source order"):
        verify_split_manifests(inventory.records, manifests, protocol)


def test_split_verifier_rejects_wrong_class_membership(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)
    manifests = build_split_manifests(inventory.records, protocol)
    train = manifests["development-train.jsonl"]
    validation = manifests["development-validation.jsonl"]
    train[0], validation[0] = validation[0], train[0]

    with pytest.raises(ValueError, match="action set"):
        verify_split_manifests(inventory.records, manifests, protocol)


def test_split_verifier_rejects_missing_and_duplicate_anchors(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)

    missing = build_split_manifests(inventory.records, protocol)
    missing["novel-anchor.jsonl"].pop()
    with pytest.raises(ValueError, match="one anchor"):
        verify_split_manifests(inventory.records, missing, protocol)

    duplicated = build_split_manifests(inventory.records, protocol)
    duplicated["novel-anchor.jsonl"][-1] = duplicated["novel-anchor.jsonl"][0]
    with pytest.raises(ValueError, match="duplicate sample IDs"):
        verify_split_manifests(inventory.records, duplicated, protocol)


def test_split_verifier_rejects_incomplete_source_coverage(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)
    manifests = build_split_manifests(inventory.records, protocol)
    manifests["official-novel.jsonl"].pop()

    with pytest.raises(ValueError, match="complete source inventory"):
        verify_split_manifests(inventory.records, manifests, protocol)


def test_split_verifier_rejects_query_under_and_over_exclusion(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    extra_primary_id = f"S003C001P010R002A{protocol.dataset.novel_actions[0]:03d}"
    annotations = [*_complete_annotations(protocol_path), _annotation(extra_primary_id)]
    annotations.sort(key=lambda row: str(row["frame_dir"]))
    metadata_path = _write_source_files(tmp_path, annotations)
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)

    under_excluded = build_split_manifests(inventory.records, protocol)
    synchronized = next(
        row
        for row in under_excluded["novel-query-official.jsonl"]
        if row.ntu.performance_id
        == under_excluded["novel-anchor.jsonl"][0].ntu.performance_id
    )
    under_excluded["novel-query-primary.jsonl"].append(
        synchronized.model_copy(update={"split": "novel_query_primary"})
    )
    with pytest.raises(ValueError, match="shares an official anchor performance"):
        verify_split_manifests(inventory.records, under_excluded, protocol)

    over_excluded = build_split_manifests(inventory.records, protocol)
    over_excluded["novel-query-primary.jsonl"] = [
        row
        for row in over_excluded["novel-query-primary.jsonl"]
        if row.sample_id != extra_primary_id
    ]
    with pytest.raises(ValueError, match="omits a non-anchor performance"):
        verify_split_manifests(inventory.records, over_excluded, protocol)


def test_manifest_bundle_is_byte_stable_and_checksummed(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)
    protocol = _synthetic_protocol(protocol_path, metadata_path)
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_summary = write_manifest_bundle(inventory, protocol, first)
    second_summary = write_manifest_bundle(inventory, protocol, second)

    assert sorted(path.name for path in first.iterdir()) == sorted(
        path.name for path in second.iterdir()
    )
    for first_path in first.iterdir():
        assert first_path.read_bytes() == (second / first_path.name).read_bytes()
    assert first_summary == second_summary
    assert load_inventory(first / "source-inventory.jsonl") == list(inventory.records)
    assert first_summary["inventory_metadata"] == {
        "pose_track_counts": {"1": 180},
        "nonempty_track_counts": {"1": 180},
        "total_frames": {"minimum": 2, "maximum": 2},
        "keypoint_tail_shape": [17, 2],
        "keypoint_score_tail_shape": [17],
    }
    for filename, file_summary in first_summary["files"].items():
        payload = (first / filename).read_bytes()
        assert payload.endswith(b"\n")
        assert hashlib.sha256(payload).hexdigest() == file_summary["sha256"]

    with pytest.raises(ValueError, match="already exists"):
        write_manifest_bundle(inventory, protocol, first)


def test_aggregate_inventory_is_accepted_by_the_locked_evaluation_validator(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    inventory = inspect_ntu_aggregate(tmp_path, metadata_path, protocol)
    protocol = _synthetic_protocol(protocol_path, metadata_path)
    output = tmp_path / "bundle"
    summary = write_manifest_bundle(inventory, protocol, output)
    manifests = build_split_manifests(inventory.records, protocol)
    source_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    def binding(filename: str) -> dict[str, object]:
        rows = manifests[filename]
        return {
            "relative_path": filename,
            "sha256": summary["files"][filename]["sha256"],
            "sample_count": len(rows),
            "sample_ids": [row.sample_id for row in rows],
        }

    plan_payload = load_evaluation_plan("configs/evaluation-plan.v1.yaml").model_dump(
        mode="json"
    )
    plan_payload.update(
        {
            "status": "locked",
            "source_inventory_manifest": {
                "kind": "ntu_aggregate_inventory",
                "relative_path": "source-inventory.jsonl",
                "sha256": summary["files"]["source-inventory.jsonl"]["sha256"],
                "sample_count": len(inventory.records),
                "sample_ids": [record.sample_id for record in inventory.records],
                "aggregate_source": {
                    "aggregate_relative_path": source_metadata["filename"],
                    "aggregate_bytes": source_metadata["bytes"],
                    "aggregate_sha256": source_metadata["sha256"],
                    "missing_list_relative_path": source_metadata[
                        "official_missing_skeletons"
                    ]["filename"],
                    "missing_list_bytes": source_metadata["official_missing_skeletons"][
                        "bytes"
                    ],
                    "missing_list_sha256": source_metadata[
                        "official_missing_skeletons"
                    ]["sha256"],
                    "missing_sample_count": source_metadata[
                        "official_missing_skeletons"
                    ]["count"],
                    "nominal_capture_count": source_metadata["protocol_count_status"][
                        "nominal_capture_count"
                    ],
                },
            },
            "anchor_manifest": binding("novel-anchor.jsonl"),
            "official_query_manifest": binding("novel-query-official.jsonl"),
            "primary_query_manifest": binding("novel-query-primary.jsonl"),
        }
    )
    plan = EvaluationPlan.model_validate(plan_payload)

    validation = validate_evaluation_manifests(
        protocol,
        plan,
        output,
        data_root=tmp_path,
        check_source_files=True,
    )

    assert validation.source_file_count == 2
    assert validation.source_files_verified is True

    for field, changed in (
        ("aggregate_relative_path", "other.pkl"),
        ("aggregate_bytes", source_metadata["bytes"] + 1),
        ("aggregate_sha256", "0" * 64),
        ("missing_list_relative_path", "other.txt"),
        (
            "missing_list_bytes",
            source_metadata["official_missing_skeletons"]["bytes"] + 1,
        ),
        ("missing_list_sha256", "0" * 64),
    ):
        altered = json.loads(json.dumps(plan_payload))
        altered["source_inventory_manifest"]["aggregate_source"][field] = changed
        with pytest.raises(ValueError, match="physical inputs"):
            validate_evaluation_manifests(
                protocol,
                EvaluationPlan.model_validate(altered),
                output,
                check_source_files=False,
            )

    altered = json.loads(json.dumps(plan_payload))
    altered["source_inventory_manifest"]["kind"] = "manifest_records"
    altered["source_inventory_manifest"]["aggregate_source"] = None
    with pytest.raises(ValueError, match="aggregate-aware"):
        validate_evaluation_manifests(
            protocol,
            EvaluationPlan.model_validate(altered),
            output,
            check_source_files=False,
        )

    (tmp_path / "ntu120_hrnet.pkl").write_bytes(b"altered")
    with pytest.raises(ValueError, match="byte count mismatch"):
        validate_evaluation_manifests(
            protocol, plan, output, data_root=tmp_path, check_source_files=True
        )


def test_inventory_rejects_present_samples_in_official_missing_list(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    sample_id = "S001C001P001R001A001"
    metadata_path = _write_source_files(
        tmp_path,
        [_annotation(sample_id)],
        missing_ids=(sample_id,),
    )

    with pytest.raises(ValueError, match="present in both"):
        inspect_ntu_aggregate(tmp_path, metadata_path, load_protocol(protocol_path))


def test_inventory_rejects_invalid_pose_track_metadata(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    metadata_path = _write_source_files(
        tmp_path,
        [_annotation("S001C001P001R001A001", pose_tracks=0)],
    )

    with pytest.raises(ValueError, match="one or two pose tracks"):
        inspect_ntu_aggregate(tmp_path, metadata_path, load_protocol(protocol_path))


def test_inventory_parses_the_official_missing_list_header(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    missing_id = "S001C001P001R001A002"
    metadata_path = _write_source_files(
        tmp_path,
        [_annotation("S001C001P001R001A001")],
        missing_ids=(missing_id,),
        missing_header="Official missing samples follow.\n\n",
    )

    inventory = inspect_ntu_aggregate(
        tmp_path, metadata_path, load_protocol(protocol_path)
    )

    assert inventory.missing_sample_ids == (missing_id,)


def test_data_generate_cli_rejects_noncontract_source_bundle(
    protocol_path: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metadata_path = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    output_dir = tmp_path / "bundle"

    exit_code = main(
        [
            "data",
            "generate",
            "--data-root",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--source-metadata",
            str(metadata_path),
            "--config",
            str(protocol_path),
        ]
    )

    assert exit_code == 2
    assert "locked source contract" in capsys.readouterr().err
    assert not output_dir.exists()
