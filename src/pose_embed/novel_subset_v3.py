"""Retain the locked primary rows without a second encoder pass."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from pose_embed.artifacts import (
    load_feature_sidecar,
    sample_order_digest,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.config import load_protocol
from pose_embed.data import load_manifest
from pose_embed.motionbert_features import write_feature_npz
from pose_embed.protocol import resolve_scientific_paths
from pose_embed.protocol_v3 import require_v3_design, require_v3_final_authorization
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json
from pose_embed.validation_proofs import validation_command, verify_validation_proofs


@validation_command()
def export_primary_queries(source_path, output_path, *, protocol_path):
    protocol = load_protocol(protocol_path)
    require_v3_final_authorization(protocol)
    root = resolve_scientific_paths(protocol).root
    design = require_v3_design(protocol)
    official_manifest = root / design.manifests["novel_query_official"].relative_path
    primary_manifest = root / design.manifests["novel_query_primary"].relative_path
    source = require_path_within(source_path, root, label="official cache")
    revision_root = (
        root / protocol.test_access.resolved_protocol_relative_path
    ).parent.parent
    destination = require_path_within(output_path, revision_root, label="primary cache")
    if destination.exists() or sidecar_path_for(destination).exists():
        raise ValueError("refusing to overwrite primary cache")
    original = validate_feature_artifact(
        source, protocol=protocol, manifest_path=official_manifest
    )
    if (
        original.split != "novel_query_official"
        or original.method != "frozen_encoder_cache"
    ):
        raise ValueError("primary export requires the exact-official pre-head cache")
    sample_ids = tuple(row.sample_id for row in load_manifest(primary_manifest))
    index = {sample_id: n for n, sample_id in enumerate(original.sample_ids)}
    if any(sample_id not in index for sample_id in sample_ids):
        raise ValueError("primary queries are not a subset of the official queries")
    indices = [index[sample_id] for sample_id in sample_ids]
    with np.load(source, allow_pickle=False) as archive:
        features = np.asarray(archive["features"])[indices]
        labels = np.asarray(archive["labels"])[indices]
    verify_validation_proofs()
    write_feature_npz(destination, features, labels, np.asarray(sample_ids))
    provenance = deepcopy(original.provenance)
    provenance["inputs"][str(primary_manifest)] = sha256_file(primary_manifest)
    provenance["inputs"][str(source)] = sha256_file(source)
    provenance["inputs"][str(sidecar_path_for(source))] = sha256_file(
        sidecar_path_for(source)
    )
    provenance["primary_subset"] = {
        "source": str(source),
        "source_manifest": str(official_manifest),
        "artifact_sha256": sha256_file(source),
        "sidecar_sha256": sha256_file(sidecar_path_for(source)),
    }
    if "jitter_fallback" in provenance:
        fallback = provenance["jitter_fallback"]
        selected = set(sample_ids)
        used = [value for value in fallback["fallback_sample_ids"] if value in selected]
        fallback.update(
            sample_count=len(sample_ids),
            fallback_sample_ids=used,
            fallback_count=len(used),
            fallback_fraction=len(used) / len(sample_ids),
            fallback_sample_order_sha256=sample_order_digest(used),
        )
    if "geometry" in provenance:
        from pose_embed.geometry_v3 import summarize_geometry

        rows = [provenance["geometry"]["rows"][index] for index in indices]
        provenance["geometry"] = {"rows": rows, "summary": summarize_geometry(rows)}
    sidecar = original.model_copy(
        update={
            "split": "novel_query_primary",
            "sample_ids": sample_ids,
            "manifest_sha256": sha256_file(primary_manifest),
            "sample_order_sha256": sample_order_digest(sample_ids),
            "artifact_sha256": sha256_file(destination),
            "shape": tuple(features.shape),
            "created_at": datetime.now(UTC),
            "provenance": provenance,
        }
    )
    verify_validation_proofs()
    write_immutable_json(sidecar_path_for(destination), sidecar.model_dump(mode="json"))
    validate_feature_artifact(
        destination, protocol=protocol, manifest_path=primary_manifest
    )
    return {"artifact": str(destination), "artifact_sha256": sidecar.artifact_sha256}


def validate_primary_subset(artifact, sidecar, protocol):
    """Recompute exact ordered row equality, not just subset metadata."""
    if (
        sidecar.split != "novel_query_primary"
        or sidecar.method != "frozen_encoder_cache"
    ):
        return
    record = sidecar.provenance.get("primary_subset")
    if (
        not isinstance(record, dict)
        or set(record)
        != {"source", "source_manifest", "artifact_sha256", "sidecar_sha256"}
        or not all(isinstance(value, str) and value for value in record.values())
    ):
        raise ValueError("primary cache lacks its official encoding binding")
    source = Path(record["source"])
    if source.resolve() == Path(artifact).resolve():
        raise ValueError("primary cache cannot refer to itself")
    source_sidecar = load_feature_sidecar(source)
    if (
        source_sidecar.split != "novel_query_official"
        or source_sidecar.method != "frozen_encoder_cache"
        or source_sidecar.condition != sidecar.condition
        or source_sidecar.artifact_sha256 != record["artifact_sha256"]
        or sha256_file(sidecar_path_for(source)) != record["sidecar_sha256"]
    ):
        raise ValueError("primary cache official source binding differs")
    source_sidecar = validate_feature_artifact(
        source, protocol=protocol, manifest_path=record["source_manifest"]
    )
    index = {value: n for n, value in enumerate(source_sidecar.sample_ids)}
    if not set(sidecar.sample_ids) <= set(index):
        raise ValueError("primary cache contains a non-official identity")
    indices = [index[value] for value in sidecar.sample_ids]
    with (
        np.load(source, allow_pickle=False) as original,
        np.load(artifact, allow_pickle=False) as subset,
    ):
        if not all(
            np.array_equal(subset[key], original[key][indices])
            for key in ("features", "labels", "sample_ids")
        ):
            raise ValueError(
                "primary cache differs from its exact ordered official rows"
            )
