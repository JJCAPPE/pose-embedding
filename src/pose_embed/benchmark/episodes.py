"""Metadata-only retrieval pools derived from the verified v1 input contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pose_embed.benchmark.retrieval import RETRIEVAL_POLICY, _digest
from pose_embed.config import load_protocol
from pose_embed.motionbert_inputs import verify_manifest_bundle
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file

_PROTOCOL = Path(__file__).resolve().parents[3] / "configs/protocol.v1.yaml"
_MANIFESTS = {
    "development_validation": "development-validation.jsonl",
    "novel": "official-novel.jsonl",
}


def load_episode(
    manifest_set_path: str | Path,
    split: str,
    *,
    protocol_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify the parent bundle and return one shared query/gallery pool.

    Only JSON metadata is read. The existing class partition and manifest order
    are preserved, including official anchors in the novel all-item pool. Novel
    pose extraction and evaluation authorization belong to the calling runner.
    ``records`` contains ManifestRecord objects; ``metadata`` is JSON-safe.
    """
    if split not in _MANIFESTS:
        raise ValueError("episode split must be development_validation or novel")
    protocol = load_protocol(protocol_path or _PROTOCOL)
    bundle = Path(manifest_set_path).resolve()
    parent_hash = sha256_file(bundle)
    _, manifests = verify_manifest_bundle(protocol, bundle)
    if sha256_file(bundle) != parent_hash:
        raise ValueError("manifest bundle changed during episode verification")
    filename = _MANIFESTS[split]
    records = list(manifests[filename])
    expected_actions = set(
        protocol.dataset.development_validation_actions
        if split == "development_validation"
        else protocol.dataset.novel_actions
    )
    if {row.ntu.action for row in records} != expected_actions:
        raise ValueError("retrieval episode must cover the exact declared classes")
    performances: dict[int, set[tuple[int, int, int, int]]] = {}
    for row in records:
        performances.setdefault(row.ntu.action, set()).add(row.ntu.performance_id)
    if any(len(values) < 2 for values in performances.values()):
        raise ValueError("every retrieval class requires two independent performances")
    sample_ids = [row.sample_id for row in records]
    metadata = {
        "schema_version": 1,
        "split": split,
        "policy": dict(RETRIEVAL_POLICY),
        "parent_protocol_sha256": protocol_digest(protocol),
        "manifest_set_sha256": parent_hash,
        "source_inventory_sha256": sha256_file(
            bundle.parent / "source-inventory.jsonl"
        ),
        "parent_manifest_sha256": sha256_file(bundle.parent / filename),
        "sample_count": len(records),
        "sample_order_sha256": _digest(sample_ids),
        "sample_ids": sample_ids,
        "actions": sorted(expected_actions),
    }
    return {"records": records, "metadata": metadata}
