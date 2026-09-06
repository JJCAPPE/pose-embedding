"""Feature extraction interfaces with an explicitly synthetic fixture backend."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import torch
import torch.nn.functional as functional

from pose_embed.artifacts import (
    FeatureSidecar,
    preprocessing_digest,
    sample_order_digest,
    sha256_bytes,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.config import (
    ExperimentConfig,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.corruptions import apply_corruption
from pose_embed.data import load_manifest, verify_manifests
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.provenance import (
    capture_provenance,
    require_path_within,
    sha256_file,
    write_immutable_json,
)


def extract_fixture_features(
    input_path: str | Path,
    output_path: str | Path,
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    role: Literal["training", "gallery_clean", "query_clean", "query_corrupted"],
    split: Literal[
        "development_train",
        "development_validation",
        "final_train",
        "novel_anchor",
        "novel_query_primary",
        "novel_query_official",
    ],
    embedding_dimension: int = 32,
    seed: int = 0,
    corruption_family: str | None = None,
    corruption_severity: int | float = 0,
) -> dict[str, object]:
    """Extract deterministic synthetic features for plumbing tests only.

    Input is an NPZ containing `poses` `[N,M,T,17,C]`, `labels` `[N]`, and
    `sample_ids` `[N]`. This backend is not a substitute for MotionBERT and marks
    every output accordingly.
    """
    source = Path(input_path)
    destination = Path(output_path)
    if destination.suffix != ".npz":
        raise ValueError("feature cache output must use the .npz suffix")
    sidecar_path = sidecar_path_for(destination)
    if destination.exists() or sidecar_path.exists():
        raise ValueError(f"refusing to overwrite feature cache: {destination}")
    if embedding_dimension < 2:
        raise ValueError("embedding_dimension must be at least 2")
    allowed_splits_by_role = {
        "training": {"development_train", "final_train"},
        "gallery_clean": {"development_validation", "novel_anchor"},
        "query_clean": {
            "development_validation",
            "novel_query_primary",
            "novel_query_official",
        },
        "query_corrupted": {
            "development_validation",
            "novel_query_primary",
            "novel_query_official",
        },
    }
    if role not in allowed_splits_by_role or split not in allowed_splits_by_role[role]:
        raise ValueError("feature role and split are incompatible")
    with np.load(source, allow_pickle=False) as archive:
        required = {"poses", "labels", "sample_ids"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"fixture NPZ is missing keys: {sorted(missing)}")
        poses = np.asarray(archive["poses"])
        labels = np.asarray(archive["labels"])
        sample_ids = np.asarray(archive["sample_ids"]).astype(str)
    if poses.ndim != 5 or poses.shape[3:] != (17, 3):
        raise ValueError("poses must have shape [N,M,T,17,3] for x, y, confidence")
    if labels.shape != (poses.shape[0],) or sample_ids.shape != (poses.shape[0],):
        raise ValueError("labels and sample_ids must have one value per pose")

    protocol = load_protocol(protocol_path)
    if corruption_family is None and corruption_severity != 0:
        raise ValueError("nonzero corruption severity requires a corruption family")
    if corruption_family is not None:
        if role not in {"query_clean", "query_corrupted"}:
            raise ValueError("protocol v1 permits corruption only for query roles")
        allowed_severities = {
            "coordinate_jitter": protocol.corruptions.coordinate_jitter_fractions,
            "joint_mask": protocol.corruptions.joint_mask_counts,
            "frame_mask": protocol.corruptions.consecutive_frame_mask_counts,
        }
        if corruption_family not in allowed_severities:
            raise ValueError(f"unsupported corruption family: {corruption_family}")
        if (
            corruption_severity != 0
            and corruption_severity not in (allowed_severities[corruption_family])
        ):
            raise ValueError("corruption severity is absent from protocol v1")
    if role == "query_corrupted" and (
        corruption_family is None or corruption_severity == 0
    ):
        raise ValueError("query_corrupted requires a nonzero registered corruption")
    if role == "query_clean" and corruption_severity != 0:
        raise ValueError("query_clean cannot contain a nonzero corruption")
    records = load_manifest(manifest_path)
    verify_manifests(records, protocol)
    if any(record.split != split for record in records):
        raise ValueError("feature manifest must contain exactly the declared split")
    manifest_sample_ids = tuple(record.sample_id for record in records)
    if tuple(sample_ids) != manifest_sample_ids:
        raise ValueError("input sample order must exactly match the feature manifest")
    expected_labels = np.asarray(
        [record.ntu.action for record in records], dtype=labels.dtype
    )
    if not np.array_equal(labels, expected_labels):
        raise ValueError("input labels must equal NTU action IDs from the manifest")

    pose_tensor = torch.as_tensor(poses, dtype=torch.float32)
    if corruption_family is not None:
        corrupted = [
            apply_corruption(
                pose,
                family=corruption_family,  # type: ignore[arg-type]
                severity=corruption_severity,
                sample_id=sample_id,
            )
            for pose, sample_id in zip(pose_tensor, sample_ids, strict=True)
        ]
        pose_tensor = torch.stack(corrupted)
    pooled = pose_tensor.mean(dim=(1, 2)).flatten(start_dim=1)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    projection = (
        torch.randn(pooled.shape[1], embedding_dimension, generator=generator)
        / pooled.shape[1] ** 0.5
    )
    features = functional.normalize(pooled @ projection, dim=1)
    extraction_config = {
        "embedding_dimension": embedding_dimension,
        "seed": seed,
        "corruption_family": corruption_family,
        "corruption_severity": corruption_severity,
    }
    condition = (
        "clean"
        if corruption_family is None or corruption_severity == 0
        else f"{corruption_family}:{corruption_severity:g}"
    )
    metadata = {
        "backend": "fixture",
        "scientific_use_allowed": False,
        "role": role,
        "split": split,
        "condition": condition,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        destination,
        features=features.numpy(),
        labels=labels,
        sample_ids=sample_ids,
        fixture_projection=projection.numpy(),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    sidecar = FeatureSidecar(
        schema_version=3,
        artifact_type="feature_cache",
        backend="fixture",
        method="fixture_projection",
        training_seed=None,
        role=role,
        split=split,
        condition=condition,
        scientific_use_allowed=False,
        protocol_sha256=protocol_digest(protocol),
        manifest_sha256=sha256_file(manifest_path),
        sample_order_sha256=sample_order_digest(tuple(sample_ids)),
        preprocessing_sha256=preprocessing_digest(protocol),
        upstream_sha256=sha256_file(Path(__file__)),
        encoder_checkpoint_sha256=sha256_bytes(projection.numpy().tobytes(order="C")),
        artifact_sha256=sha256_file(destination),
        array_key="features",
        shape=tuple(features.shape),
        dtype=str(features.numpy().dtype),
        sample_ids=tuple(sample_ids),
        created_at=datetime.now(UTC),
        provenance=capture_provenance(
            command="features extract --backend fixture",
            configuration=extraction_config,
            inputs=[source, protocol_path, manifest_path],
        ),
    )
    write_immutable_json(sidecar_path, sidecar.model_dump(mode="json"))
    return sidecar.model_dump(mode="json")


def apply_trained_head(
    input_path: str | Path,
    output_path: str | Path,
    *,
    checkpoint_path: str | Path,
    run_manifest_path: str | Path,
    protocol_path: str | Path,
    manifest_path: str | Path,
    allow_fixture: bool = False,
) -> dict[str, object]:
    """Apply the exact trained linear head to one ordered base-feature cache."""
    source = Path(input_path)
    destination = Path(output_path)
    checkpoint_file = Path(checkpoint_path)
    run_manifest_file = Path(run_manifest_path)
    if destination.suffix != ".npz":
        raise ValueError("head output must use the .npz suffix")
    destination_sidecar = sidecar_path_for(destination)
    if destination.exists() or destination_sidecar.exists():
        raise ValueError(f"refusing to overwrite head output: {destination}")

    protocol = load_protocol(protocol_path)
    source_sidecar = validate_feature_artifact(
        source,
        protocol=protocol,
        manifest_path=manifest_path,
        allow_fixture=allow_fixture,
    )
    if source_sidecar.scientific_use_allowed:
        destination = require_path_within(
            destination,
            resolve_scientific_paths(protocol).root,
            label="scientific feature output",
        )
        destination_sidecar = sidecar_path_for(destination)
    expected_base_method = (
        "fixture_projection"
        if source_sidecar.backend == "fixture"
        else "frozen_encoder_cache"
    )
    if source_sidecar.method != expected_base_method:
        raise ValueError("head application requires an unprojected base-feature cache")
    if source_sidecar.role == "training":
        raise ValueError("head application requires a gallery or query feature role")

    try:
        checkpoint = torch.load(
            checkpoint_file,
            map_location="cpu",
            weights_only=True,
        )
    except Exception as exc:
        raise ValueError("head checkpoint is not a readable safe checkpoint") from exc
    if not isinstance(checkpoint, dict):
        raise ValueError("head checkpoint must contain a state and configuration")
    try:
        config = ExperimentConfig.model_validate(checkpoint.get("config"))
    except ValueError as exc:
        raise ValueError("head checkpoint configuration is invalid") from exc
    if source_sidecar.scientific_use_allowed:
        validate_experiment_against_protocol(config, protocol)
    state_dict = checkpoint.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError("head checkpoint is missing its state dictionary")
    weight = state_dict.get("projection.weight")
    bias = state_dict.get("projection.bias")
    if (
        not isinstance(weight, torch.Tensor)
        or tuple(weight.shape) != (config.embedding_dimension, config.input_dimension)
        or not torch.isfinite(weight).all()
        or not isinstance(bias, torch.Tensor)
        or tuple(bias.shape) != (config.embedding_dimension,)
        or not torch.isfinite(bias).all()
    ):
        raise ValueError("head checkpoint state is invalid")

    try:
        run_manifest = json.loads(run_manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("training run manifest is invalid JSON") from exc
    checkpoint_sha256 = sha256_file(checkpoint_file)
    if (
        run_manifest.get("configuration", {}).get("experiment")
        != config.model_dump(mode="json")
        or run_manifest.get("outputs", {}).get("checkpoint") != checkpoint_sha256
        or run_manifest.get("protocol_sha256") != protocol_digest(protocol)
        or run_manifest.get("scientific_use_allowed")
        is not source_sidecar.scientific_use_allowed
    ):
        raise ValueError(
            "training run manifest differs from the checkpoint or protocol"
        )

    with np.load(source, allow_pickle=False) as archive:
        required = {source_sidecar.array_key, "labels", "sample_ids"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"base-feature cache is missing keys: {sorted(missing)}")
        features = torch.as_tensor(
            np.asarray(archive[source_sidecar.array_key]),
            dtype=torch.float32,
        )
        labels = np.asarray(archive["labels"])
        sample_ids = np.asarray(archive["sample_ids"]).astype(str)
    if tuple(features.shape) != source_sidecar.shape:
        raise ValueError("base-feature array shape differs from its sidecar")
    if features.shape[1] != config.input_dimension:
        raise ValueError("base-feature dimension differs from the trained head")
    with torch.no_grad():
        embeddings = functional.normalize(
            functional.linear(features, weight, bias),
            dim=-1,
        ).numpy()
    if not np.isfinite(embeddings).all():
        raise ValueError("trained head produced non-finite embeddings")

    metadata = {
        "backend": source_sidecar.backend,
        "scientific_use_allowed": source_sidecar.scientific_use_allowed,
        "role": source_sidecar.role,
        "split": source_sidecar.split,
        "condition": source_sidecar.condition,
        "method": config.objective,
        "training_seed": config.seed,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        destination,
        embeddings=embeddings,
        labels=labels,
        sample_ids=sample_ids,
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    sidecar = FeatureSidecar(
        schema_version=3,
        artifact_type="feature_cache",
        backend=source_sidecar.backend,
        method=config.objective,
        training_seed=config.seed,
        role=source_sidecar.role,
        split=source_sidecar.split,
        condition=source_sidecar.condition,
        scientific_use_allowed=source_sidecar.scientific_use_allowed,
        protocol_sha256=source_sidecar.protocol_sha256,
        manifest_sha256=source_sidecar.manifest_sha256,
        sample_order_sha256=source_sidecar.sample_order_sha256,
        preprocessing_sha256=source_sidecar.preprocessing_sha256,
        upstream_sha256=source_sidecar.upstream_sha256,
        encoder_checkpoint_sha256=source_sidecar.encoder_checkpoint_sha256,
        head_checkpoint_sha256=checkpoint_sha256,
        base_artifact_sha256=source_sidecar.artifact_sha256,
        base_sidecar_sha256=sha256_file(sidecar_path_for(source)),
        artifact_sha256=sha256_file(destination),
        array_key="embeddings",
        shape=tuple(embeddings.shape),
        dtype=str(embeddings.dtype),
        sample_ids=tuple(sample_ids),
        created_at=datetime.now(UTC),
        provenance=capture_provenance(
            command="features apply-head",
            configuration={
                "method": config.objective,
                "seed": config.seed,
                "input_dimension": config.input_dimension,
                "embedding_dimension": config.embedding_dimension,
            },
            inputs=[
                source.resolve(),
                sidecar_path_for(source).resolve(),
                checkpoint_file.resolve(),
                run_manifest_file.resolve(),
                Path(protocol_path).resolve(),
                Path(manifest_path).resolve(),
            ],
        ),
    )
    write_immutable_json(
        destination_sidecar,
        sidecar.model_dump(mode="json"),
    )
    return sidecar.model_dump(mode="json")
