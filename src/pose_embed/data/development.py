"""Result-blind construction and verification of the development episode."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.inventory import build_split_manifests, load_inventory
from pose_embed.data.manifest import ManifestRecord, load_manifest, verify_manifests
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.provenance import (
    require_path_within,
    sha256_file,
    write_immutable_json,
)

SELECTION_PREFIX = "protocol-v1|dev-anchor-v1|"
GALLERY_FILENAME = "development-gallery.jsonl"
QUERY_FILENAME = "development-queries.jsonl"
REPORT_FILENAME = "development-episode.json"


def build_development_episode(
    records: Sequence[ManifestRecord], protocol: ProtocolConfig
) -> tuple[list[ManifestRecord], list[ManifestRecord], list[dict[str, str]]]:
    """Select one hashed gallery sample per class and exclude its camera mates."""
    verify_manifests(records, protocol)
    if any(row.split != "development_validation" for row in records):
        raise ValueError("development episode requires development_validation records")
    actions = set(protocol.dataset.development_validation_actions)
    if {row.ntu.action for row in records} != actions:
        raise ValueError("development episode must cover all validation actions")
    chosen = {
        min(
            (row for row in records if row.ntu.action == action),
            key=lambda row: (
                hashlib.sha256(
                    (SELECTION_PREFIX + row.sample_id).encode("utf-8")
                ).hexdigest(),
                row.sample_id,
            ),
        ).sample_id
        for action in actions
    }
    gallery = [row for row in records if row.sample_id in chosen]
    anchor_by_performance = {row.ntu.performance_id: row.sample_id for row in gallery}
    queries: list[ManifestRecord] = []
    exclusions: list[dict[str, str]] = []
    for row in records:
        anchor_id = anchor_by_performance.get(row.ntu.performance_id)
        if anchor_id is None:
            queries.append(row)
        else:
            exclusions.append(
                {
                    "sample_id": row.sample_id,
                    "gallery_sample_id": anchor_id,
                    "reason": "gallery_sample"
                    if row.sample_id == anchor_id
                    else "synchronized_gallery_view",
                }
            )
    if {row.ntu.action for row in queries} != actions:
        raise ValueError("every validation action must retain independent queries")
    return gallery, queries, exclusions


def _complete_validation_records(
    manifest_path: Path, inventory_path: Path, protocol: ProtocolConfig
) -> list[ManifestRecord]:
    inventory = load_inventory(inventory_path)
    if len(inventory) != protocol.dataset.expected_source_sample_count:
        raise ValueError("development episode requires the complete source inventory")
    expected = build_split_manifests(inventory, protocol)[
        "development-validation.jsonl"
    ]
    records = load_manifest(manifest_path)
    if records != expected:
        raise ValueError(
            "development source must equal the complete ordered validation manifest"
        )
    return records


def _binding(path: Path, records: Sequence[ManifestRecord]) -> dict[str, Any]:
    sample_ids = [row.sample_id for row in records]
    return {
        "sha256": sha256_file(path),
        "sample_count": len(records),
        "sample_order_sha256": hashlib.sha256(
            json.dumps(sample_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def _report(
    output: Path,
    source: Path,
    inventory: Path,
    records: Sequence[ManifestRecord],
    protocol: ProtocolConfig,
) -> dict[str, Any]:
    gallery, queries, exclusions = build_development_episode(records, protocol)
    for filename, expected in (
        (GALLERY_FILENAME, gallery),
        (QUERY_FILENAME, queries),
    ):
        if load_manifest(output / filename) != expected:
            raise ValueError(f"development episode partition differs: {filename}")
    return {
        "schema_version": 1,
        "protocol_sha256": protocol_digest(protocol),
        "selection": "minimum_sha256_then_sample_id",
        "selection_prefix": SELECTION_PREFIX,
        "ordering": "source_manifest_order",
        "source_manifest": {"path": str(source), **_binding(source, records)},
        "source_inventory": {"path": str(inventory), "sha256": sha256_file(inventory)},
        "gallery": _binding(output / GALLERY_FILENAME, gallery),
        "query": _binding(output / QUERY_FILENAME, queries),
        "exclusions": exclusions,
    }


def generate_development_episode(
    manifest_path: str | Path,
    output_dir: str | Path,
    protocol_path: str | Path,
) -> dict[str, Any]:
    """Write a new episode from a complete Week 2 manifest bundle."""
    protocol = load_protocol(protocol_path)
    scientific_paths = resolve_scientific_paths(protocol)
    if scientific_paths.test_opening_ledger.exists():
        raise ValueError("development episode cannot be changed after test opening")
    source = Path(manifest_path).resolve()
    inventory = source.parent / "source-inventory.jsonl"
    records = _complete_validation_records(source, inventory, protocol)
    gallery, queries, _ = build_development_episode(records, protocol)
    output = require_path_within(
        output_dir, scientific_paths.root, label="development episode"
    )
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(
            f"development episode output already exists: {output}"
        ) from exc
    for filename, rows in (
        (GALLERY_FILENAME, gallery),
        (QUERY_FILENAME, queries),
    ):
        with (output / filename).open("x", encoding="utf-8") as stream:
            for row in rows:
                stream.write(row.model_dump_json() + "\n")
    report = _report(output, source, inventory, records, protocol)
    # The report is the completion marker; a partially written directory is invalid.
    write_immutable_json(output / REPORT_FILENAME, report)
    return report


def validate_development_episode(
    report_path: str | Path,
    *,
    protocol: ProtocolConfig,
    manifest_path: str | Path | None = None,
    role: Literal["gallery_clean", "query_clean"] | None = None,
) -> dict[str, Any]:
    """Rehash inputs and rederive both partitions before authorizing a cache."""
    report_file = Path(report_path).resolve()
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        source = Path(report["source_manifest"]["path"])
        inventory = Path(report["source_inventory"]["path"])
        if (
            not source.is_absolute()
            or inventory != source.parent / "source-inventory.jsonl"
        ):
            raise ValueError("development episode source paths differ from the bundle")
        records = _complete_validation_records(source, inventory, protocol)
        expected = _report(report_file.parent, source, inventory, records, protocol)
    except (KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "development episode report or its inputs are incomplete"
        ) from exc
    if report != expected:
        raise ValueError("development episode report hashes or selection differ")
    if manifest_path is not None or role is not None:
        if manifest_path is None or role not in {"gallery_clean", "query_clean"}:
            raise ValueError(
                "development episode validation requires manifest and role"
            )
        filename = GALLERY_FILENAME if role == "gallery_clean" else QUERY_FILENAME
        if sha256_file(manifest_path) != sha256_file(report_file.parent / filename):
            raise ValueError(
                "feature manifest differs from its development episode role"
            )
    return report
