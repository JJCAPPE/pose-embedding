"""Metadata-only manifests and leakage checks for the locked action splits."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pose_embed.config import ProtocolConfig
from pose_embed.data.ntu import NTUSampleId, parse_ntu_sample_id
from pose_embed.provenance import sha256_file

Split = Literal[
    "development_train",
    "development_validation",
    "final_train",
    "novel_anchor",
    "novel_query_primary",
    "novel_query_official",
]
ALLOWED_SPLITS = frozenset(Split.__args__)


class ManifestRecord(BaseModel):
    """One metadata record; pose data is intentionally not represented."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_id: str
    relative_path: str | None = None
    split: Split
    is_anchor: bool = False
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def identity_and_anchor_are_consistent(self) -> ManifestRecord:
        canonical = parse_ntu_sample_id(self.sample_id).sample_id
        if canonical != self.sample_id:
            raise ValueError(f"sample_id must be canonical uppercase ID {canonical}")
        if self.is_anchor != (self.split == "novel_anchor"):
            raise ValueError("is_anchor must be true exactly for novel_anchor records")
        if self.relative_path is not None:
            if "\\" in self.relative_path or "\x00" in self.relative_path:
                raise ValueError("relative_path must use normalized POSIX separators")
            raw_parts = self.relative_path.split("/")
            path = PurePosixPath(self.relative_path)
            if (
                path.is_absolute()
                or not self.relative_path
                or self.relative_path != path.as_posix()
                or any(part in {"", ".", ".."} for part in raw_parts)
            ):
                raise ValueError("relative_path must be normalized and stay relative")
            path_sample_id = parse_ntu_sample_id(path.name).sample_id
            filename_sample_id = path.name.split(".", maxsplit=1)[0]
            if path_sample_id != self.sample_id or filename_sample_id != self.sample_id:
                raise ValueError(
                    "relative_path filename must identify sample_id exactly"
                )
        return self

    @property
    def ntu(self) -> NTUSampleId:
        return parse_ntu_sample_id(self.sample_id)


def load_manifest(path: str | Path) -> list[ManifestRecord]:
    """Load one JSONL manifest with line-specific validation errors."""
    manifest_path = Path(path)
    records: list[ManifestRecord] = []
    try:
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ValueError(f"manifest does not exist: {manifest_path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            records.append(ManifestRecord.model_validate_json(line))
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"invalid manifest record at {manifest_path}:{line_number}: {exc}"
            ) from exc
    if not records:
        raise ValueError(f"manifest contains no records: {manifest_path}")
    return records


def _expected_actions(protocol: ProtocolConfig) -> dict[str, set[int]]:
    all_actions = set(range(1, 121))
    novel = set(protocol.dataset.novel_actions)
    validation = set(protocol.dataset.development_validation_actions)
    return {
        "development_train": all_actions - novel - validation,
        "development_validation": validation,
        "final_train": all_actions - novel,
        "novel_anchor": novel,
        "novel_query_primary": novel,
        "novel_query_official": novel,
    }


def verify_manifests(
    records: Iterable[ManifestRecord],
    protocol: ProtocolConfig,
    *,
    data_root: str | Path | None = None,
    check_files: bool = False,
    require_complete: bool = False,
) -> dict[str, object]:
    """Fail on malformed partitions, duplicate IDs, or query/gallery leakage."""
    rows = list(records)
    if not rows:
        raise ValueError("at least one manifest record is required")
    expected = _expected_actions(protocol)
    by_split: dict[str, list[ManifestRecord]] = defaultdict(list)
    for row in rows:
        by_split[row.split].append(row)
        if row.ntu.action not in expected[row.split]:
            raise ValueError(
                f"action A{row.ntu.action:03d} is forbidden in split {row.split}"
            )

    for split, split_rows in by_split.items():
        counts = Counter(row.sample_id for row in split_rows)
        duplicates = sorted(sample for sample, count in counts.items() if count > 1)
        if duplicates:
            raise ValueError(f"duplicate sample IDs in {split}: {duplicates}")

    paths_by_sample: dict[str, set[str]] = defaultdict(set)
    samples_by_path: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.relative_path is not None:
            paths_by_sample[row.sample_id].add(row.relative_path)
            samples_by_path[row.relative_path].add(row.sample_id)
    aliased_samples = {
        sample_id: sorted(paths)
        for sample_id, paths in paths_by_sample.items()
        if len(paths) > 1
    }
    if aliased_samples:
        raise ValueError(
            f"sample IDs resolve to multiple path aliases: {aliased_samples}"
        )
    collided_paths = {
        path: sorted(sample_ids)
        for path, sample_ids in samples_by_path.items()
        if len(sample_ids) > 1
    }
    if collided_paths:
        raise ValueError(
            f"manifest paths resolve to multiple sample IDs: {collided_paths}"
        )

    train_classes = {
        row.ntu.action
        for row in rows
        if row.split in {"development_train", "final_train"}
    }
    novel_classes = {row.ntu.action for row in rows if row.split.startswith("novel_")}
    overlap = train_classes & novel_classes
    if overlap:
        raise ValueError(f"auxiliary/novel class leakage: {sorted(overlap)}")

    development_train_classes = {
        row.ntu.action for row in by_split["development_train"]
    }
    validation_classes = {row.ntu.action for row in by_split["development_validation"]}
    if development_train_classes & validation_classes:
        raise ValueError("development train and validation classes overlap")

    anchor_ids = {row.sample_id for row in by_split["novel_anchor"]}
    anchor_performances = {row.ntu.performance_id for row in by_split["novel_anchor"]}
    for row in by_split["novel_query_official"]:
        if row.sample_id in anchor_ids:
            raise ValueError(f"anchor is also an official query: {row.sample_id}")
    for row in by_split["novel_query_primary"]:
        if row.ntu.performance_id in anchor_performances:
            raise ValueError(
                "primary query shares the anchor performance across cameras: "
                f"{row.sample_id}"
            )

    if require_complete:
        missing_splits = ALLOWED_SPLITS - set(by_split)
        if missing_splits:
            raise ValueError(
                f"complete manifest is missing splits: {sorted(missing_splits)}"
            )
        for split, required_actions in expected.items():
            observed_actions = {row.ntu.action for row in by_split[split]}
            if observed_actions != required_actions:
                missing_actions = sorted(required_actions - observed_actions)
                extra_actions = sorted(observed_actions - required_actions)
                raise ValueError(
                    f"incomplete action coverage for {split}; "
                    f"missing={missing_actions}, extra={extra_actions}"
                )
        anchor_counts = Counter(row.ntu.action for row in by_split["novel_anchor"])
        if set(anchor_counts.values()) != {1}:
            raise ValueError("complete manifest requires one anchor per novel action")
        official_ids = {row.sample_id for row in by_split["novel_query_official"]}
        primary_ids = {row.sample_id for row in by_split["novel_query_primary"]}
        expected_primary_ids = {
            row.sample_id
            for row in by_split["novel_query_official"]
            if row.ntu.performance_id not in anchor_performances
        }
        if primary_ids != expected_primary_ids:
            raise ValueError(
                "primary queries must equal official queries minus anchor performances"
            )
        development_ids = {
            row.sample_id
            for split in ("development_train", "development_validation")
            for row in by_split[split]
        }
        final_train_ids = {row.sample_id for row in by_split["final_train"]}
        if final_train_ids != development_ids:
            raise ValueError(
                "final_train must equal development_train plus development_validation"
            )
        if primary_ids - official_ids:
            raise ValueError("primary queries must be a subset of official queries")

    if check_files:
        if data_root is None:
            raise ValueError("data_root is required when check_files is true")
        root = Path(data_root)
        for row in rows:
            if row.relative_path is None:
                raise ValueError(f"missing relative_path for {row.sample_id}")
            if row.sha256 is None:
                raise ValueError(f"missing sha256 for {row.sample_id}")
            candidate = (root / row.relative_path).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError(
                    f"relative_path escapes data root for {row.sample_id}"
                ) from exc
            if not candidate.is_file():
                raise ValueError(f"data file does not exist for {row.sample_id}")
            digest = sha256_file(candidate)
            if digest != row.sha256:
                raise ValueError(f"checksum mismatch for {row.sample_id}")

    return {
        "records": len(rows),
        "splits": {
            split: len(split_rows) for split, split_rows in sorted(by_split.items())
        },
        "classes": {
            split: len({row.ntu.action for row in split_rows})
            for split, split_rows in sorted(by_split.items())
        },
    }


def build_manifest_records(
    sample_ids: Iterable[str],
    anchor_ids: Iterable[str],
    protocol: ProtocolConfig,
) -> list[ManifestRecord]:
    """Build deterministic split records from authorized IDs and official anchors."""
    samples = sorted({parse_ntu_sample_id(value) for value in sample_ids})
    anchors = {parse_ntu_sample_id(value).sample_id for value in anchor_ids}
    official_anchors = set(protocol.dataset.official_one_shot_exemplars)
    if anchors != official_anchors:
        missing = sorted(official_anchors - anchors)
        extra = sorted(anchors - official_anchors)
        raise ValueError(
            "anchor IDs must equal the pinned official one-shot exemplars; "
            f"missing={missing}, extra={extra}"
        )
    available_ids = {sample.sample_id for sample in samples}
    missing_anchors = sorted(anchors - available_ids)
    if missing_anchors:
        raise ValueError(f"anchor IDs are absent from samples: {missing_anchors}")

    novel = set(protocol.dataset.novel_actions)
    validation = set(protocol.dataset.development_validation_actions)
    anchor_performances = {
        sample.performance_id for sample in samples if sample.sample_id in anchors
    }
    records: list[ManifestRecord] = []
    for sample in samples:
        common = {"sample_id": sample.sample_id, "relative_path": None}
        if sample.action not in novel:
            records.append(
                ManifestRecord(
                    **common,
                    split=(
                        "development_validation"
                        if sample.action in validation
                        else "development_train"
                    ),
                )
            )
            records.append(ManifestRecord(**common, split="final_train"))
            continue
        if sample.sample_id in anchors:
            records.append(
                ManifestRecord(**common, split="novel_anchor", is_anchor=True)
            )
            continue
        records.append(ManifestRecord(**common, split="novel_query_official"))
        if sample.performance_id not in anchor_performances:
            records.append(ManifestRecord(**common, split="novel_query_primary"))
    return records
