"""Verified source and code bindings shared by MotionBERT parity and extraction."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.inventory import (
    SPLIT_MANIFEST_FILENAMES,
    NTUInventoryRecord,
    inspect_ntu_aggregate_sources,
    load_inventory,
    verify_split_manifests,
)
from pose_embed.data.manifest import ManifestRecord, load_manifest
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.provenance import sha256_file

REPOSITORY = Path(__file__).resolve().parents[2]
MOTIONBERT_CODE_PATHS = (
    "src/pose_embed/artifacts.py",
    "src/pose_embed/config.py",
    "src/pose_embed/data/inventory.py",
    "src/pose_embed/data/manifest.py",
    "src/pose_embed/data/ntu.py",
    "src/pose_embed/data/development.py",
    "src/pose_embed/data/motionbert.py",
    "src/pose_embed/models/action_head.py",
    "src/pose_embed/models/motionbert.py",
    "src/pose_embed/motionbert_inputs.py",
    "src/pose_embed/motionbert_parity.py",
    "src/pose_embed/motionbert_features.py",
    "src/pose_embed/provenance.py",
)


@dataclass(frozen=True)
class VerifiedMotionBERTInputs:
    protocol: ProtocolConfig
    data_root: Path
    artifact_root: Path
    manifest_set_path: Path
    inventory: tuple[NTUInventoryRecord, ...]
    manifests: dict[str, list[ManifestRecord]]
    annotations: list[dict[str, Any]] | None
    bindings: dict[str, str]


def motionbert_code_digest() -> str:
    digest = hashlib.sha256()
    for relative in MOTIONBERT_CODE_PATHS:
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update((REPOSITORY / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def require_clean_repository() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=True,
    )
    if status.stdout.strip():
        raise ValueError(
            "scientific MotionBERT runs require a clean committed checkout"
        )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def verify_manifest_bundle(
    protocol: ProtocolConfig,
    manifest_set_path: str | Path,
) -> tuple[tuple[NTUInventoryRecord, ...], dict[str, list[ManifestRecord]]]:
    """Recompute the complete metadata contract without opening pose data."""
    bundle_path = Path(manifest_set_path).resolve()
    document = json.loads(bundle_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or document.get("protocol_sha256") != (
        protocol_digest(protocol)
    ):
        raise ValueError("manifest bundle must bind the current adopted protocol")
    contract = protocol.dataset.source_contract
    expected_source = {
        key: value
        for key, value in contract.model_dump().items()
        if key not in {"missing_sample_count", "nominal_capture_count"}
    }
    if document.get("source") != expected_source:
        raise ValueError("manifest bundle physical source contract mismatch")
    count = document.get("protocol_count", {})
    if count != {
        "usable_annotations": protocol.dataset.expected_source_sample_count,
        "official_missing_skeletons": contract.missing_sample_count,
        "nominal_captures": contract.nominal_capture_count,
        "locked_expected_rows": protocol.dataset.expected_source_sample_count,
        "amendment_required": False,
    }:
        raise ValueError(
            "manifest bundle does not account for the complete usable source"
        )
    names = ("source-inventory.jsonl", *SPLIT_MANIFEST_FILENAMES)
    files = document.get("files", {})
    if set(files) != set(names):
        raise ValueError("manifest bundle file set mismatch")
    for name in names:
        path = bundle_path.parent / name
        if not path.resolve().is_relative_to(bundle_path.parent):
            raise ValueError("manifest file escapes its bundle")
        if sha256_file(path) != files[name].get("sha256"):
            raise ValueError(f"manifest bundle checksum mismatch: {name}")
    inventory = tuple(load_inventory(bundle_path.parent / names[0]))
    if len(inventory) != protocol.dataset.expected_source_sample_count:
        raise ValueError("source inventory is incomplete")
    manifests = {
        name: load_manifest(bundle_path.parent / name)
        for name in SPLIT_MANIFEST_FILENAMES
    }
    verify_split_manifests(inventory, manifests, protocol)
    for name, rows in ((names[0], inventory), *manifests.items()):
        if files[name].get("records") != len(rows):
            raise ValueError(f"manifest bundle count mismatch: {name}")
    return inventory, manifests


def load_motionbert_inputs(
    protocol_path: str | Path,
    manifest_set_path: str | Path,
    *,
    load_annotations: bool = True,
    require_clean: bool = True,
) -> VerifiedMotionBERTInputs:
    """Verify the adopted complete bundle and hash before any deserialization."""
    protocol = load_protocol(protocol_path)
    scientific = resolve_scientific_paths(protocol)
    if scientific.test_opening_ledger.exists():
        raise ValueError("Week 3 extraction is forbidden after novel-test opening")
    raw_root = os.environ.get("POSE_EMBED_DATA_ROOT")
    if not raw_root or not Path(raw_root).is_absolute():
        raise ValueError("POSE_EMBED_DATA_ROOT must be an absolute path")
    data_root = Path(raw_root).resolve()
    if require_clean:
        require_clean_repository()
    bundle_path = Path(manifest_set_path).resolve()
    if not bundle_path.is_relative_to(scientific.root):
        raise ValueError("manifest bundle must be inside POSE_EMBED_ARTIFACT_ROOT")
    inventory, manifests = verify_manifest_bundle(protocol, bundle_path)
    contract = protocol.dataset.source_contract
    for prefix in ("aggregate", "missing_list"):
        relative = getattr(contract, f"{prefix}_relative_path")
        path = (data_root / relative).resolve()
        if not path.is_relative_to(data_root):
            raise ValueError("physical source escapes POSE_EMBED_DATA_ROOT")
        if path.stat().st_size != getattr(contract, f"{prefix}_bytes") or (
            sha256_file(path) != getattr(contract, f"{prefix}_sha256")
        ):
            raise ValueError(f"verified {prefix} source differs from the protocol")
    annotations = None
    if load_annotations:
        inspected = inspect_ntu_aggregate_sources(
            data_root,
            protocol,
            **contract.model_dump(),
            usable_annotation_count=protocol.dataset.expected_source_sample_count,
            retain_annotations=True,
        )
        if inspected.records != inventory:
            raise ValueError("aggregate annotations differ from the bound inventory")
        annotations = inspected.annotations
    bindings = {
        "protocol_sha256": protocol_digest(protocol),
        "manifest_set_sha256": sha256_file(bundle_path),
        "source_inventory_sha256": sha256_file(
            bundle_path.parent / "source-inventory.jsonl"
        ),
        "aggregate_sha256": contract.aggregate_sha256,
        "missing_list_sha256": contract.missing_list_sha256,
        "code_sha256": motionbert_code_digest(),
        "dependency_lock_sha256": sha256_file(REPOSITORY / "uv.lock"),
    }
    return VerifiedMotionBERTInputs(
        protocol,
        data_root,
        scientific.root,
        bundle_path,
        inventory,
        manifests,
        annotations,
        bindings,
    )


def build_motionbert_bindings(
    inputs: VerifiedMotionBERTInputs, assets: dict[str, Any]
) -> dict[str, str]:
    return inputs.bindings | {
        key: str(assets[key])
        for key in (
            "upstream_sha256",
            "checkpoint_sha256",
            "config_sha256",
            "license_sha256",
            "upstream_commit",
        )
    }
