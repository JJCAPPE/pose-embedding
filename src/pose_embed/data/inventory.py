from __future__ import annotations

import json
import os
import pickle
import shutil
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator

from pose_embed.config import ProtocolConfig
from pose_embed.data.manifest import ManifestRecord, build_manifest_records
from pose_embed.data.ntu import NTUSampleId, parse_ntu_sample_id
from pose_embed.provenance import sha256_file


class NTUInventoryRecord(BaseModel):
    """Normalized metadata for one trusted aggregate annotation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_id: str
    annotation_index: int
    setup: int
    camera: int
    performer: int
    repetition: int
    action: int
    label: int
    pose_track_count: int
    nonempty_track_count: int
    total_frames: int
    keypoint_shape: tuple[int, int, int, int]
    keypoint_score_shape: tuple[int, int, int]
    image_shape: tuple[int, int]
    original_shape: tuple[int, int]

    @model_validator(mode="after")
    def identity_and_body_metadata_are_consistent(self) -> NTUInventoryRecord:
        sample = parse_ntu_sample_id(self.sample_id)
        identity = (
            self.setup,
            self.camera,
            self.performer,
            self.repetition,
            self.action,
        )
        expected_identity = (
            sample.setup,
            sample.camera,
            sample.performer,
            sample.repetition,
            sample.action,
        )
        if sample.sample_id != self.sample_id or identity != expected_identity:
            raise ValueError("inventory identity metadata does not match sample_id")
        if self.label != self.action - 1:
            raise ValueError("inventory label does not match action")
        if self.annotation_index < 0:
            raise ValueError("inventory annotation_index must be nonnegative")
        if self.pose_track_count not in {1, 2}:
            raise ValueError("inventory must contain one or two pose tracks")
        if not 1 <= self.nonempty_track_count <= self.pose_track_count:
            raise ValueError("inventory nonempty-track count is invalid")
        if self.total_frames <= 0:
            raise ValueError("inventory total_frames must be positive")
        if self.keypoint_shape != (
            self.pose_track_count,
            self.total_frames,
            17,
            2,
        ) or self.keypoint_score_shape != (
            self.pose_track_count,
            self.total_frames,
            17,
        ):
            raise ValueError("inventory pose shapes do not match body metadata")
        if any(value <= 0 for value in (*self.image_shape, *self.original_shape)):
            raise ValueError("inventory image shapes must be positive")
        return self

    @property
    def ntu(self) -> NTUSampleId:
        return parse_ntu_sample_id(self.sample_id)


class NTUAggregateInventory(BaseModel):
    """Verified source metadata and its normalized annotation inventory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    records: tuple[NTUInventoryRecord, ...]
    missing_sample_ids: tuple[str, ...]
    aggregate_relative_path: str
    aggregate_bytes: int
    aggregate_sha256: str
    missing_list_relative_path: str
    missing_list_bytes: int
    missing_list_sha256: str
    nominal_capture_count: int
    expected_source_sample_count: int


SPLIT_MANIFEST_FILENAMES = (
    "development-train.jsonl",
    "development-validation.jsonl",
    "final-train.jsonl",
    "official-novel.jsonl",
    "novel-anchor.jsonl",
    "novel-query-primary.jsonl",
    "novel-query-official.jsonl",
)


def _resolve_below(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("source metadata path escapes the data root")
    return candidate


def _shape(value: Any, expected_dimensions: int, *, field: str) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if (
        not isinstance(value, np.ndarray)
        or shape is None
        or len(shape) != expected_dimensions
    ):
        raise ValueError(f"{field} must be a {expected_dimensions}-dimensional ndarray")
    return tuple(int(size) for size in shape)


def load_inventory(path: str | Path) -> list[NTUInventoryRecord]:
    """Load and revalidate a normalized source inventory in declared order."""
    inventory_path = Path(path)
    records: list[NTUInventoryRecord] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(
        inventory_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = NTUInventoryRecord.model_validate_json(line)
        except ValueError as exc:
            raise ValueError(
                f"invalid inventory record at {inventory_path}:{line_number}: {exc}"
            ) from exc
        if record.annotation_index != len(records):
            raise ValueError(
                "inventory annotation indices must be contiguous and ordered"
            )
        if record.sample_id in seen_ids:
            raise ValueError(f"duplicate inventory sample ID: {record.sample_id}")
        seen_ids.add(record.sample_id)
        records.append(record)
    if not records:
        raise ValueError(f"inventory contains no records: {inventory_path}")
    return records


def inspect_ntu_aggregate(
    data_root: str | Path,
    source_metadata_path: str | Path,
    protocol: ProtocolConfig,
) -> NTUAggregateInventory:
    """Verify the trusted container before inspecting its pickle payload."""
    metadata = json.loads(Path(source_metadata_path).read_text(encoding="utf-8"))
    return _inspect_ntu_aggregate_metadata(data_root, metadata, protocol)


def inspect_ntu_aggregate_sources(
    data_root: str | Path,
    protocol: ProtocolConfig,
    *,
    aggregate_relative_path: str,
    aggregate_bytes: int,
    aggregate_sha256: str,
    missing_list_relative_path: str,
    missing_list_bytes: int,
    missing_list_sha256: str,
    missing_sample_count: int,
    usable_annotation_count: int,
    nominal_capture_count: int,
) -> NTUAggregateInventory:
    """Reinspect an aggregate from fields bound by a locked evaluation plan."""
    metadata = {
        "filename": aggregate_relative_path,
        "bytes": aggregate_bytes,
        "sha256": aggregate_sha256,
        "format_validation": {"annotation_count": usable_annotation_count},
        "official_missing_skeletons": {
            "filename": missing_list_relative_path,
            "bytes": missing_list_bytes,
            "sha256": missing_list_sha256,
            "count": missing_sample_count,
        },
        "protocol_count_status": {
            "nominal_capture_count": nominal_capture_count,
            "usable_annotation_count": usable_annotation_count,
        },
    }
    return _inspect_ntu_aggregate_metadata(data_root, metadata, protocol)


def _inspect_ntu_aggregate_metadata(
    data_root: str | Path,
    metadata: Mapping[str, Any],
    protocol: ProtocolConfig,
) -> NTUAggregateInventory:
    root = Path(data_root).resolve()
    aggregate_path = _resolve_below(root, metadata["filename"])
    expected_bytes = metadata["bytes"]
    if aggregate_path.stat().st_size != expected_bytes:
        raise ValueError("source aggregate byte count mismatch")
    if sha256_file(aggregate_path) != metadata["sha256"]:
        raise ValueError("source aggregate SHA-256 mismatch")

    missing_metadata = metadata["official_missing_skeletons"]
    missing_path = _resolve_below(root, missing_metadata["filename"])
    if missing_path.stat().st_size != missing_metadata["bytes"]:
        raise ValueError("official missing-skeleton list byte count mismatch")
    if sha256_file(missing_path) != missing_metadata["sha256"]:
        raise ValueError("official missing-skeleton list SHA-256 mismatch")
    parsed_missing: list[str] = []
    for raw_line in missing_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = parse_ntu_sample_id(line)
        except ValueError:
            if line.lower().startswith("s"):
                raise ValueError(
                    f"malformed ID in official missing-skeleton list: {line!r}"
                ) from None
            continue
        if parsed.sample_id != line:
            raise ValueError("official missing-skeleton IDs must be canonical bare IDs")
        parsed_missing.append(parsed.sample_id)
    missing_sample_ids = tuple(parsed_missing)
    if len(missing_sample_ids) != missing_metadata["count"]:
        raise ValueError("official missing-skeleton count mismatch")
    if len(set(missing_sample_ids)) != len(missing_sample_ids):
        raise ValueError("official missing-skeleton list contains duplicate IDs")

    with aggregate_path.open("rb") as stream:
        payload = pickle.load(stream)  # noqa: S301 - hash-verified trusted input
    annotations = payload["annotations"]
    records: list[NTUInventoryRecord] = []
    seen_ids: set[str] = set()
    for index, annotation in enumerate(annotations):
        sample_id = annotation["frame_dir"]
        sample = parse_ntu_sample_id(sample_id)
        if sample.sample_id != sample_id:
            raise ValueError(f"annotation {index} frame_dir is not a canonical bare ID")
        if sample.sample_id in seen_ids:
            raise ValueError(f"duplicate annotation sample IDs: {sample.sample_id}")
        seen_ids.add(sample.sample_id)
        if annotation["label"] != sample.action - 1:
            raise ValueError(f"label/action mismatch for {sample_id}")
        keypoint_shape = _shape(annotation["keypoint"], 4, field="keypoint")
        score_shape = _shape(annotation["keypoint_score"], 3, field="keypoint_score")
        if keypoint_shape[2:] != (17, 2):
            raise ValueError(f"invalid COCO-17 keypoint shape for {sample_id}")
        if keypoint_shape[0] not in {1, 2}:
            raise ValueError(f"{sample_id} must contain one or two pose tracks")
        if score_shape != keypoint_shape[:3]:
            raise ValueError(f"keypoint score shape mismatch for {sample_id}")
        if annotation["total_frames"] != keypoint_shape[1]:
            raise ValueError(f"total_frames mismatch for {sample_id}")
        if (
            not np.isfinite(annotation["keypoint"]).all()
            or not np.isfinite(annotation["keypoint_score"]).all()
        ):
            raise ValueError(f"non-finite pose values for {sample_id}")
        image_shape = tuple(int(value) for value in annotation["img_shape"])
        original_shape = tuple(int(value) for value in annotation["original_shape"])
        if len(image_shape) != 2 or len(original_shape) != 2:
            raise ValueError(f"invalid image shape for {sample_id}")
        records.append(
            NTUInventoryRecord(
                sample_id=sample.sample_id,
                annotation_index=index,
                setup=sample.setup,
                camera=sample.camera,
                performer=sample.performer,
                repetition=sample.repetition,
                action=sample.action,
                label=annotation["label"],
                pose_track_count=keypoint_shape[0],
                nonempty_track_count=int(
                    np.count_nonzero(
                        np.any(annotation["keypoint_score"] > 0, axis=(1, 2))
                    )
                ),
                total_frames=annotation["total_frames"],
                keypoint_shape=keypoint_shape,
                keypoint_score_shape=score_shape,
                image_shape=image_shape,
                original_shape=original_shape,
            )
        )

    if len(records) != metadata["format_validation"]["annotation_count"]:
        raise ValueError("aggregate annotation count mismatch")
    if len(records) != metadata["protocol_count_status"]["usable_annotation_count"]:
        raise ValueError("aggregate usable-annotation count mismatch")
    overlap = sorted(set(missing_sample_ids) & {record.sample_id for record in records})
    if overlap:
        raise ValueError(
            f"sample IDs are present in both the aggregate and missing list: {overlap}"
        )
    nominal_count = metadata["protocol_count_status"]["nominal_capture_count"]
    if len(records) + len(missing_sample_ids) != nominal_count:
        raise ValueError(
            "usable and missing samples do not account for nominal captures"
        )
    return NTUAggregateInventory(
        records=tuple(records),
        missing_sample_ids=missing_sample_ids,
        aggregate_relative_path=metadata["filename"],
        aggregate_bytes=expected_bytes,
        aggregate_sha256=metadata["sha256"],
        missing_list_relative_path=missing_metadata["filename"],
        missing_list_bytes=missing_metadata["bytes"],
        missing_list_sha256=missing_metadata["sha256"],
        nominal_capture_count=nominal_count,
        expected_source_sample_count=protocol.dataset.expected_source_sample_count,
    )


def build_split_manifests(
    records: Iterable[NTUInventoryRecord],
    protocol: ProtocolConfig,
) -> dict[str, list[ManifestRecord]]:
    """Build the seven stable protocol views from normalized source order."""
    source = list(records)
    counts = Counter(record.sample_id for record in source)
    duplicates = sorted(sample_id for sample_id, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate inventory sample IDs: {duplicates}")
    observed_actions = {record.action for record in source}
    if observed_actions != set(range(1, 121)):
        missing = sorted(set(range(1, 121)) - observed_actions)
        extra = sorted(observed_actions - set(range(1, 121)))
        raise ValueError(
            "source inventory must cover all 120 actions; "
            f"missing={missing}, extra={extra}"
        )

    anchor_order = tuple(protocol.dataset.official_one_shot_exemplars)
    source_by_id = {record.sample_id: record for record in source}
    missing_anchors = [
        sample_id for sample_id in anchor_order if sample_id not in source_by_id
    ]
    if missing_anchors:
        raise ValueError(
            f"official anchors are absent from inventory: {missing_anchors}"
        )
    classified = build_manifest_records(
        (record.sample_id for record in source),
        anchor_order,
        protocol,
    )
    by_split = {
        split: [record for record in classified if record.split == split]
        for split in (
            "development_train",
            "development_validation",
            "final_train",
            "novel_anchor",
            "novel_query_primary",
            "novel_query_official",
        )
    }
    source_order_novel = [
        record
        for record in classified
        if record.split in {"novel_anchor", "novel_query_official"}
    ]
    anchor_by_id = {record.sample_id: record for record in by_split["novel_anchor"]}
    anchors = [anchor_by_id[sample_id] for sample_id in anchor_order]
    return {
        "development-train.jsonl": by_split["development_train"],
        "development-validation.jsonl": by_split["development_validation"],
        "final-train.jsonl": by_split["final_train"],
        "official-novel.jsonl": source_order_novel,
        "novel-anchor.jsonl": anchors,
        "novel-query-primary.jsonl": by_split["novel_query_primary"],
        "novel-query-official.jsonl": by_split["novel_query_official"],
    }


def verify_split_manifests(
    inventory_records: Iterable[NTUInventoryRecord],
    manifests: Mapping[str, Sequence[ManifestRecord]],
    protocol: ProtocolConfig,
) -> dict[str, object]:
    """Prove exact membership, uniqueness, coverage, and ordering invariants."""
    source = list(inventory_records)
    manifest_names: set[str] = set(manifests)
    required_names: set[str] = set(SPLIT_MANIFEST_FILENAMES)
    if manifest_names != required_names:
        missing = sorted(required_names - manifest_names)
        extra = sorted(manifest_names - required_names)
        raise ValueError(
            f"manifest file set mismatch; missing={missing}, extra={extra}"
        )

    for name in SPLIT_MANIFEST_FILENAMES:
        rows = list(manifests[name])
        row_counts = Counter(row.sample_id for row in rows)
        duplicates = sorted(
            sample_id for sample_id, count in row_counts.items() if count > 1
        )
        if duplicates:
            raise ValueError(f"duplicate sample IDs in {name}: {duplicates}")

    ids = {
        name: {row.sample_id for row in manifests[name]}
        for name in SPLIT_MANIFEST_FILENAMES
    }
    source_ids = {record.sample_id for record in source}
    if len(source_ids) != len(source):
        raise ValueError("source inventory contains duplicate sample IDs")

    all_actions = set(range(1, 121))
    novel_actions = set(protocol.dataset.novel_actions)
    validation_actions = set(protocol.dataset.development_validation_actions)
    auxiliary_actions = all_actions - novel_actions
    anchors = list(manifests["novel-anchor.jsonl"])
    anchor_action_counts = Counter(row.ntu.action for row in anchors)
    if len(anchors) != len(novel_actions) or any(
        anchor_action_counts[action] != 1 for action in novel_actions
    ):
        raise ValueError("novel manifest must contain exactly one anchor per action")
    expected_actions = {
        "development-train.jsonl": auxiliary_actions - validation_actions,
        "development-validation.jsonl": validation_actions,
        "final-train.jsonl": auxiliary_actions,
        "official-novel.jsonl": novel_actions,
        "novel-anchor.jsonl": novel_actions,
        "novel-query-primary.jsonl": novel_actions,
        "novel-query-official.jsonl": novel_actions,
    }
    for name, expected_action_set in expected_actions.items():
        actual_action_set = {row.ntu.action for row in manifests[name]}
        if actual_action_set != expected_action_set:
            missing = sorted(expected_action_set - actual_action_set)
            extra = sorted(actual_action_set - expected_action_set)
            raise ValueError(
                f"{name} action set mismatch; missing={missing}, extra={extra}"
            )

    development = ids["development-train.jsonl"] | ids["development-validation.jsonl"]
    if ids["development-train.jsonl"] & ids["development-validation.jsonl"]:
        raise ValueError("development train and validation samples overlap")
    if development != ids["final-train.jsonl"]:
        raise ValueError("final train is not the exact development partition union")
    if development & ids["official-novel.jsonl"]:
        raise ValueError("auxiliary and official novel samples overlap")
    if development | ids["official-novel.jsonl"] != source_ids:
        raise ValueError("base partitions do not cover the complete source inventory")
    if (
        ids["novel-anchor.jsonl"] | ids["novel-query-official.jsonl"]
        != ids["official-novel.jsonl"]
    ):
        raise ValueError("official novel is not anchors plus exact-official queries")
    if ids["novel-anchor.jsonl"] & ids["novel-query-official.jsonl"]:
        raise ValueError("anchors and exact-official queries overlap")
    if not ids["novel-query-primary.jsonl"] <= ids["novel-query-official.jsonl"]:
        raise ValueError("primary queries are not a subset of exact-official queries")

    anchor_by_performance = {row.ntu.performance_id: row.sample_id for row in anchors}
    exclusions = []
    for row in manifests["novel-query-official.jsonl"]:
        anchor_id = anchor_by_performance.get(row.ntu.performance_id)
        is_primary = row.sample_id in ids["novel-query-primary.jsonl"]
        if anchor_id is not None:
            if is_primary:
                raise ValueError(
                    "primary query shares an official anchor performance: "
                    f"{row.sample_id}"
                )
            setup, performer, repetition, action = row.ntu.performance_id
            exclusions.append(
                {
                    "sample_id": row.sample_id,
                    "anchor_sample_id": anchor_id,
                    "setup": setup,
                    "performer": performer,
                    "repetition": repetition,
                    "action": action,
                    "reason": "synchronized camera view of the anchor performance",
                }
            )
        elif not is_primary:
            raise ValueError(
                f"primary query omits a non-anchor performance: {row.sample_id}"
            )

    expected = build_split_manifests(source, protocol)
    for name in SPLIT_MANIFEST_FILENAMES:
        rows = list(manifests[name])
        expected_rows = expected[name]
        actual_ids = [row.sample_id for row in rows]
        expected_ids = [row.sample_id for row in expected_rows]
        if set(actual_ids) != set(expected_ids):
            missing = sorted(set(expected_ids) - set(actual_ids))
            extra = sorted(set(actual_ids) - set(expected_ids))
            raise ValueError(
                f"manifest membership mismatch for {name}; "
                f"missing={missing[:10]}, extra={extra[:10]}"
            )
        if actual_ids != expected_ids:
            raise ValueError(f"{name} does not preserve stable source order")
        if [row.split for row in rows] != [row.split for row in expected_rows] or [
            row.is_anchor for row in rows
        ] != [row.is_anchor for row in expected_rows]:
            raise ValueError(f"manifest roles are inconsistent for {name}")

    return {
        "source_records": len(source),
        "splits": {
            name: {
                "records": len(manifests[name]),
                "classes": len({row.ntu.action for row in manifests[name]}),
            }
            for name in SPLIT_MANIFEST_FILENAMES
        },
        "query_exclusions": exclusions,
    }


def _canonical_json_line(model: BaseModel) -> str:
    return json.dumps(
        model.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_jsonl(path: Path, rows: Sequence[BaseModel]) -> None:
    path.write_text(
        "\n".join(_canonical_json_line(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _file_summary(path: Path, rows: Sequence[BaseModel]) -> dict[str, object]:
    actions = [parse_ntu_sample_id(row.sample_id).action for row in rows]
    counts = Counter(actions)
    return {
        "records": len(rows),
        "classes": len(counts),
        "sha256": sha256_file(path),
        "class_counts": {f"A{action:03d}": counts[action] for action in sorted(counts)},
    }


def _render_manifest_audit(summary: Mapping[str, object]) -> str:
    files = summary["files"]
    source = summary["source"]
    protocol_count = summary["protocol_count"]
    inventory_metadata = summary["inventory_metadata"]
    exclusions = summary["query_exclusions"]
    if not isinstance(files, dict):
        raise TypeError("audit files must be a mapping")
    if not isinstance(source, dict) or not isinstance(protocol_count, dict):
        raise TypeError("audit source accounting must be a mapping")
    if not isinstance(inventory_metadata, dict):
        raise TypeError("audit inventory metadata must be a mapping")
    if not isinstance(exclusions, list):
        raise TypeError("audit exclusions must be a list")

    amendment_required = protocol_count["amendment_required"]
    status = (
        "Status: manifest construction is complete for the verified usable "
        "aggregate. Final novel evaluation remains sealed until the documented "
        "result-blind protocol amendment is adopted."
        if amendment_required
        else "Status: the adopted input contract matches the verified usable "
        "aggregate. Final novel evaluation remains sealed until the separate "
        "evaluation-plan and run-set locks are complete."
    )
    lines = [
        "# NTU RGB+D 120 manifest audit v1",
        "",
        status,
        "",
        "## Source accounting",
        "",
        f"- Aggregate: `{source['aggregate_relative_path']}`",
        f"- Aggregate bytes: {source['aggregate_bytes']}",
        f"- Aggregate SHA-256: `{source['aggregate_sha256']}`",
        f"- Usable annotations: {protocol_count['usable_annotations']}",
        "- Official missing-skeleton exclusions: "
        f"{protocol_count['official_missing_skeletons']}",
        f"- Nominal captures accounted for: {protocol_count['nominal_captures']}",
        "- Locked source-inventory row expectation: "
        f"{protocol_count['locked_expected_rows']}",
        "- Protocol amendment required: "
        f"`{str(protocol_count['amendment_required']).lower()}`",
        (
            "- Required amendment scope: 113,945 usable rows plus verification "
            "of the hash-pinned aggregate and official missing-skeleton list "
            "instead of 114,480 declared per-sample files."
            if amendment_required
            else "- Adopted source contract: usable aggregate plus the hash-pinned "
            "official missing-skeleton list; two physical inputs."
        ),
        "- Pose-track counts: "
        f"`{json.dumps(inventory_metadata['pose_track_counts'], sort_keys=True)}`",
        "- Nonempty-track counts: "
        f"`{json.dumps(inventory_metadata['nonempty_track_counts'], sort_keys=True)}`",
        "- Source frame-count range: "
        f"{inventory_metadata['total_frames']['minimum']} to "
        f"{inventory_metadata['total_frames']['maximum']}",
        f"- Keypoint tail shape: `{inventory_metadata['keypoint_tail_shape']}`",
        f"- Confidence tail shape: `{inventory_metadata['keypoint_score_tail_shape']}`",
        "",
        "No placeholder rows were fabricated for officially missing skeletons.",
        "",
        "## File checksums",
        "",
        "| File | Rows | Classes | SHA-256 |",
        "| --- | ---: | ---: | --- |",
    ]
    for filename, details in files.items():
        if not isinstance(details, dict):
            raise TypeError("audit file details must be a mapping")
        lines.append(
            f"| `{filename}` | {details['records']} | {details['classes']} | "
            f"`{details['sha256']}` |"
        )

    split_names = [name for name in files if name != "source-inventory.jsonl"]
    lines.extend(
        [
            "",
            "## Counts by class and split",
            "",
            "| Action | Source inventory | "
            + " | ".join(f"`{name}`" for name in split_names)
            + " |",
            "| --- | " + " | ".join("---:" for _ in range(len(split_names) + 1)) + " |",
        ]
    )
    for action in range(1, 121):
        key = f"A{action:03d}"
        values: list[str] = []
        for name in ("source-inventory.jsonl", *split_names):
            details = files[name]
            if not isinstance(details, dict):
                raise TypeError("audit file details must be a mapping")
            class_counts = details["class_counts"]
            if not isinstance(class_counts, dict):
                raise TypeError("audit class counts must be a mapping")
            values.append(str(class_counts.get(key, 0)))
        lines.append(f"| {key} | " + " | ".join(values) + " |")

    lines.extend(
        [
            "",
            "## Primary-query exclusions",
            "",
            "The primary query differs from the exact-official query only by the "
            "following synchronized camera views of official anchor performances. "
            "Other synchronized query views are retained.",
            "",
            "| Excluded query | Anchor | Setup | Performer | Repetition | Action | "
            "Reason |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for exclusion in exclusions:
        if not isinstance(exclusion, dict):
            raise TypeError("audit exclusion must be a mapping")
        lines.append(
            f"| `{exclusion['sample_id']}` | "
            f"`{exclusion['anchor_sample_id']}` | {exclusion['setup']} | "
            f"{exclusion['performer']} | {exclusion['repetition']} | "
            f"A{exclusion['action']:03d} | {exclusion['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Verified invariants",
            "",
            "- Every source annotation has one unique canonical sample ID and "
            "normalized metadata.",
            "- Development training and validation classes are disjoint (80/20 "
            "classes).",
            "- Final training is exactly the union of both development partitions "
            "(100 classes).",
            "- Official novel samples are disjoint from auxiliary samples and "
            "complete source coverage.",
            "- There is exactly one official anchor for each of the 20 novel actions.",
            "- Exact-official queries are official novel samples minus anchors.",
            "- Primary queries are exact-official queries minus anchor-performance "
            "camera mates.",
            "- Every JSONL file preserves its declared source or published-anchor "
            "order.",
            "",
        ]
    )
    return "\n".join(lines)


def write_manifest_bundle(
    inventory: NTUAggregateInventory,
    protocol: ProtocolConfig,
    output_dir: str | Path,
) -> dict[str, object]:
    """Atomically write one immutable inventory and seven split manifests."""
    actual_source = {
        "aggregate_relative_path": inventory.aggregate_relative_path,
        "aggregate_bytes": inventory.aggregate_bytes,
        "aggregate_sha256": inventory.aggregate_sha256,
        "missing_list_relative_path": inventory.missing_list_relative_path,
        "missing_list_bytes": inventory.missing_list_bytes,
        "missing_list_sha256": inventory.missing_list_sha256,
        "missing_sample_count": len(inventory.missing_sample_ids),
        "nominal_capture_count": inventory.nominal_capture_count,
    }
    if (
        len(inventory.records) != protocol.dataset.expected_source_sample_count
        or actual_source != protocol.dataset.source_contract.model_dump()
    ):
        raise ValueError("aggregate inventory differs from the locked source contract")
    output = Path(output_dir)
    if output.exists():
        raise ValueError(f"manifest output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        manifests = build_split_manifests(inventory.records, protocol)
        verification = verify_split_manifests(inventory.records, manifests, protocol)
        inventory_path = temporary / "source-inventory.jsonl"
        _write_jsonl(inventory_path, inventory.records)
        files: dict[str, dict[str, object]] = {
            inventory_path.name: _file_summary(inventory_path, inventory.records)
        }
        for filename in SPLIT_MANIFEST_FILENAMES:
            path = temporary / filename
            rows = manifests[filename]
            _write_jsonl(path, rows)
            files[filename] = _file_summary(path, rows)

        from pose_embed.protocol import protocol_digest

        pose_track_counts = Counter(
            record.pose_track_count for record in inventory.records
        )
        nonempty_track_counts = Counter(
            record.nonempty_track_count for record in inventory.records
        )
        summary: dict[str, object] = {
            "schema_version": 1,
            "protocol_sha256": protocol_digest(protocol),
            "source": {
                "aggregate_relative_path": inventory.aggregate_relative_path,
                "aggregate_bytes": inventory.aggregate_bytes,
                "aggregate_sha256": inventory.aggregate_sha256,
                "missing_list_relative_path": inventory.missing_list_relative_path,
                "missing_list_bytes": inventory.missing_list_bytes,
                "missing_list_sha256": inventory.missing_list_sha256,
            },
            "protocol_count": {
                "usable_annotations": len(inventory.records),
                "official_missing_skeletons": len(inventory.missing_sample_ids),
                "nominal_captures": inventory.nominal_capture_count,
                "locked_expected_rows": inventory.expected_source_sample_count,
                "amendment_required": (
                    len(inventory.records) != inventory.expected_source_sample_count
                ),
            },
            "inventory_metadata": {
                "pose_track_counts": {
                    str(count): pose_track_counts[count]
                    for count in sorted(pose_track_counts)
                },
                "nonempty_track_counts": {
                    str(count): nonempty_track_counts[count]
                    for count in sorted(nonempty_track_counts)
                },
                "total_frames": {
                    "minimum": min(record.total_frames for record in inventory.records),
                    "maximum": max(record.total_frames for record in inventory.records),
                },
                "keypoint_tail_shape": list(inventory.records[0].keypoint_shape[2:]),
                "keypoint_score_tail_shape": list(
                    inventory.records[0].keypoint_score_shape[2:]
                ),
            },
            "files": files,
            "query_exclusions": verification["query_exclusions"],
        }
        audit_path = temporary / "manifest-audit.md"
        audit_path.write_text(_render_manifest_audit(summary), encoding="utf-8")
        summary["audit"] = {
            "filename": audit_path.name,
            "sha256": sha256_file(audit_path),
        }
        (temporary / "manifest-set.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return summary
