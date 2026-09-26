"""Clean, provenance-bound frozen MotionBERT caches for auxiliary classes."""

from __future__ import annotations

import os
import re
import resource
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from pose_embed.artifacts import (
    FeatureSidecar,
    _validate_archive,
    preprocessing_digest,
    sample_order_digest,
    sidecar_path_for,
)
from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.manifest import ManifestRecord, load_manifest
from pose_embed.motionbert_inputs import (
    MOTIONBERT_CODE_PATHS,
    REPOSITORY,
    VerifiedMotionBERTInputs,
    build_motionbert_bindings,
    load_motionbert_inputs,
    motionbert_code_digest,
    verify_manifest_bundle,
)
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.provenance import (
    capture_provenance,
    require_path_within,
    sha256_file,
    write_immutable_json,
)


def validate_selected_manifest(
    manifests: dict[str, list[ManifestRecord]],
    protocol: ProtocolConfig,
    manifest_path: str | Path,
    *,
    role: str,
    split: str,
    episode_path: str | Path | None = None,
    source_inventory_sha256: str | None = None,
) -> list[ManifestRecord]:
    """Only complete training sets or the fixed development episode are allowed."""
    records = load_manifest(manifest_path)
    if role == "training" and split in {"development_train", "final_train"}:
        expected = manifests[split.replace("_", "-") + ".jsonl"]
        if records != expected:
            raise ValueError("training extraction requires the complete ordered split")
    elif role in {"gallery_clean", "query_clean"} and split == (
        "development_validation"
    ):
        from pose_embed.data.development import validate_development_episode

        if episode_path is None:
            raise ValueError("development extraction requires its fixed episode report")
        episode = validate_development_episode(
            episode_path, protocol=protocol, manifest_path=manifest_path, role=role
        )
        if (
            episode["source_inventory"]["sha256"] != source_inventory_sha256
            or load_manifest(episode["source_manifest"]["path"])
            != manifests["development-validation.jsonl"]
        ):
            raise ValueError("development episode belongs to a different source bundle")
    else:
        raise ValueError(
            "Week 3 MotionBERT extraction permits only clean auxiliary data"
        )
    if any(row.split != split for row in records):
        raise ValueError("selected manifest split mismatch")
    return records


def write_feature_npz(
    destination: Path, features: np.ndarray, labels: np.ndarray, sample_ids: np.ndarray
) -> None:
    """Publish a deterministic ZIP64 archive atomically without replacement."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.savez(stream, features=features, labels=labels, sample_ids=sample_ids)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite feature cache: {destination}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _source_paths(inputs: VerifiedMotionBERTInputs) -> list[Path]:
    contract = inputs.protocol.dataset.source_contract
    return [
        inputs.data_root / contract.aggregate_relative_path,
        inputs.data_root / contract.missing_list_relative_path,
    ]


def extract_motionbert_features(
    input_path: str | Path,
    output_path: str | Path,
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    manifest_set_path: str | Path,
    parity_evidence_path: str | Path,
    role: str,
    split: str,
    device: str = "cuda",
    episode_path: str | Path | None = None,
) -> dict[str, Any]:
    from pose_embed.data.motionbert import preprocess_annotation
    from pose_embed.models.action_head import pool_action_features
    from pose_embed.models.motionbert import (
        configure_deterministic_inference,
        inference_environment,
        load_frozen_encoder,
    )
    from pose_embed.motionbert_parity import validate_parity_report

    started_at = datetime.now(UTC)
    started = time.perf_counter()
    destination = Path(output_path).resolve()
    if destination.suffix != ".npz":
        raise ValueError("feature cache output must use the .npz suffix")
    if destination.exists() or sidecar_path_for(destination).exists():
        raise ValueError(f"refusing to overwrite feature cache: {destination}")
    if split.startswith("novel") or role == "query_corrupted":
        raise ValueError(
            "Week 3 MotionBERT extraction permits only clean auxiliary data"
        )
    scientific = resolve_scientific_paths(load_protocol(protocol_path))
    if (scientific.root / "benchmark-v2/locks/test-opening.json").exists():
        raise ValueError("legacy extraction is forbidden after benchmark v2 opening")
    resolved_device = torch.device(device)
    if resolved_device.type not in {"cpu", "cuda"}:
        raise ValueError("MotionBERT supports explicit cpu or cuda devices")
    configure_deterministic_inference()
    inputs = load_motionbert_inputs(protocol_path, manifest_set_path)
    destination = require_path_within(
        destination, inputs.artifact_root, label="MotionBERT cache"
    )
    if Path(input_path).resolve() != _source_paths(inputs)[0].resolve():
        raise ValueError("--input must be the verified protocol aggregate")
    records = validate_selected_manifest(
        inputs.manifests,
        inputs.protocol,
        manifest_path,
        role=role,
        split=split,
        episode_path=episode_path,
        source_inventory_sha256=inputs.bindings["source_inventory_sha256"],
    )
    timings = {"source_verification_load": time.perf_counter() - started}
    tick = time.perf_counter()
    encoder, assets = load_frozen_encoder(inputs.data_root, device=resolved_device)
    bindings = build_motionbert_bindings(inputs, assets)
    parity_path = Path(parity_evidence_path).resolve()
    parity = validate_parity_report(parity_path, bindings)
    environment = inference_environment(resolved_device)
    if parity.get("environment") != environment:
        raise ValueError("extraction environment differs from its verified parity run")
    timings["encoder_load_and_parity_validation"] = time.perf_counter() - tick
    if resolved_device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(resolved_device)
    features = np.empty((len(records), 8704), dtype=np.float32)
    by_id = {row.sample_id: row.annotation_index for row in inputs.inventory}
    assert inputs.annotations is not None
    timings.update(preprocessing=0.0, transfer=0.0, encoder=0.0, pooling=0.0)

    def synchronize() -> None:
        if resolved_device.type == "cuda":
            torch.cuda.synchronize(resolved_device)

    with torch.inference_mode():
        for offset in range(0, len(records), 32):
            batch = records[offset : offset + 32]
            tick = time.perf_counter()
            poses = np.stack(
                [
                    preprocess_annotation(
                        inputs.annotations[by_id[row.sample_id]], inputs.protocol
                    )
                    for row in batch
                ]
            )
            timings["preprocessing"] += time.perf_counter() - tick
            tick = time.perf_counter()
            tensor = torch.from_numpy(poses).to(resolved_device)
            synchronize()
            timings["transfer"] += time.perf_counter() - tick
            tick = time.perf_counter()
            representation = encoder.get_representation(
                tensor.reshape(len(batch) * 2, 100, 17, 3)
            )
            synchronize()
            timings["encoder"] += time.perf_counter() - tick
            if tuple(representation.shape) != (len(batch) * 2, 100, 17, 512):
                raise ValueError("frozen encoder representation shape mismatch")
            tick = time.perf_counter()
            pooled = (
                pool_action_features(
                    representation.reshape(len(batch), 2, 100, 17, 512)
                )
                .cpu()
                .numpy()
            )
            if pooled.dtype != np.float32 or not np.isfinite(pooled).all():
                raise ValueError("frozen encoder produced invalid pooled features")
            features[offset : offset + len(batch)] = pooled
            timings["pooling"] += time.perf_counter() - tick
    tick = time.perf_counter()
    sample_ids = tuple(row.sample_id for row in records)
    write_feature_npz(
        destination,
        features,
        np.asarray([row.ntu.action for row in records], dtype=np.int64),
        np.asarray(sample_ids),
    )
    timings["serialization"] = time.perf_counter() - tick
    paths = {
        "manifest_set": str(inputs.manifest_set_path),
        "parity_report": str(parity_path),
        "protocol": str(Path(protocol_path).resolve()),
    }
    if episode_path is not None:
        paths["development_episode"] = str(Path(episode_path).resolve())
    provenance_inputs = [
        *_source_paths(inputs),
        inputs.manifest_set_path,
        inputs.manifest_set_path.parent / "source-inventory.jsonl",
        Path(manifest_path).resolve(),
        Path(protocol_path).resolve(),
        parity_path,
        Path(assets["checkpoint_path"]),
        Path(assets["config_path"]),
        *(REPOSITORY / path for path in MOTIONBERT_CODE_PATHS),
    ]
    if episode_path is not None:
        provenance_inputs.append(Path(episode_path).resolve())
    provenance = capture_provenance(
        command="features extract --backend motionbert",
        configuration={
            "device": str(resolved_device),
            "batch_size": 32,
            "dtype": "float32",
            "condition": "clean",
        },
        inputs=provenance_inputs,
        repository=REPOSITORY,
        started_at=started_at,
    )
    provenance["motionbert"] = {"bindings": bindings, "paths": paths}
    provenance["inference_environment"] = environment
    provenance["process"] = {"pid": os.getpid(), "job_id": os.environ.get("JOB_ID")}
    gpu_allocated = (
        int(torch.cuda.max_memory_allocated(resolved_device))
        if resolved_device.type == "cuda"
        else 0
    )
    gpu_reserved = (
        int(torch.cuda.max_memory_reserved(resolved_device))
        if resolved_device.type == "cuda"
        else 0
    )
    peak_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    provenance["extraction"] = {
        "stage_seconds": timings,
        "wall_time_seconds": time.perf_counter() - started,
        "sample_count": len(records),
        "artifact_bytes": destination.stat().st_size,
        "peak_gpu_memory_bytes": max(gpu_allocated, gpu_reserved),
        "peak_gpu_allocated_bytes": gpu_allocated,
        "peak_gpu_reserved_bytes": gpu_reserved,
        "peak_host_memory_bytes": peak_rss
        if sys.platform == "darwin"
        else peak_rss * 1024,
    }
    sidecar = FeatureSidecar(
        schema_version=3,
        artifact_type="feature_cache",
        backend="motionbert",
        method="frozen_encoder_cache",
        training_seed=None,
        role=role,
        split=split,
        condition="clean",
        scientific_use_allowed=True,
        protocol_sha256=bindings["protocol_sha256"],
        manifest_sha256=sha256_file(manifest_path),
        sample_order_sha256=sample_order_digest(sample_ids),
        preprocessing_sha256=preprocessing_digest(inputs.protocol),
        upstream_sha256=bindings["upstream_sha256"],
        encoder_checkpoint_sha256=bindings["checkpoint_sha256"],
        artifact_sha256=sha256_file(destination),
        array_key="features",
        shape=tuple(features.shape),
        dtype="float32",
        sample_ids=sample_ids,
        created_at=datetime.now(UTC),
        provenance=provenance,
    )
    # No authorization sidecar is published until the archive and its complete
    # provenance pass the same checks used by consumers. A failed run leaves
    # an unusable, immutable partial artifact for diagnosis.
    del features
    tick = time.perf_counter()
    validate_motionbert_cache(sidecar, inputs.protocol, manifest_path)
    _validate_archive(destination, sidecar)
    timings["cache_verification"] = time.perf_counter() - tick
    peak_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    provenance["extraction"].update(
        wall_time_seconds=time.perf_counter() - started,
        peak_host_memory_bytes=peak_rss
        if sys.platform == "darwin"
        else peak_rss * 1024,
    )
    provenance["ended_at"] = datetime.now(UTC).isoformat()
    sidecar = sidecar.model_copy(update={"provenance": provenance})
    write_immutable_json(sidecar_path_for(destination), sidecar.model_dump(mode="json"))
    return {
        "artifact": str(destination),
        "artifact_sha256": sidecar.artifact_sha256,
        "sidecar": str(sidecar_path_for(destination)),
        "sample_order_sha256": sidecar.sample_order_sha256,
        "extraction": provenance["extraction"],
    }


def validate_motionbert_cache(
    sidecar: FeatureSidecar, protocol: ProtocolConfig, manifest_path: str | Path
) -> None:
    """Authorize base caches by their immutable evidence, without reopening poses."""
    from pose_embed.models.motionbert import verify_motionbert_assets
    from pose_embed.motionbert_parity import validate_parity_report

    details = sidecar.provenance.get("motionbert")
    if not isinstance(details, dict) or not isinstance(details.get("paths"), dict):
        raise ValueError("MotionBERT cache lacks verified source/parity provenance")
    paths = details["paths"]
    try:
        artifact_root = resolve_scientific_paths(protocol).root
        bundle = require_path_within(
            paths["manifest_set"], artifact_root, label="MotionBERT manifest bundle"
        )
        parity = require_path_within(
            paths["parity_report"], artifact_root, label="MotionBERT parity report"
        )
        if "development_episode" in paths:
            require_path_within(
                paths["development_episode"],
                artifact_root,
                label="MotionBERT development episode",
            )
        raw_root = os.environ["POSE_EMBED_DATA_ROOT"]
        if not Path(raw_root).is_absolute():
            raise ValueError("POSE_EMBED_DATA_ROOT must be absolute")
        data_root = Path(raw_root).resolve()
        assets = verify_motionbert_assets(data_root)
        _, manifests = verify_manifest_bundle(protocol, bundle)
        contract = protocol.dataset.source_contract
        expected = {
            "protocol_sha256": protocol_digest(protocol),
            "manifest_set_sha256": sha256_file(bundle),
            "source_inventory_sha256": sha256_file(
                bundle.parent / "source-inventory.jsonl"
            ),
            "aggregate_sha256": contract.aggregate_sha256,
            "missing_list_sha256": contract.missing_list_sha256,
            "code_sha256": motionbert_code_digest(),
            "dependency_lock_sha256": sha256_file(REPOSITORY / "uv.lock"),
        } | {
            key: str(assets[key])
            for key in (
                "upstream_sha256",
                "checkpoint_sha256",
                "config_sha256",
                "license_sha256",
                "upstream_commit",
            )
        }
        if details.get("bindings") != expected:
            raise ValueError("MotionBERT cache source/code/checkpoint bindings changed")
        parity_report = validate_parity_report(parity, expected)
        if sidecar.provenance.get("inference_environment") != parity_report.get(
            "environment"
        ):
            raise ValueError("cache environment differs from its verified parity run")
        validate_selected_manifest(
            manifests,
            protocol,
            manifest_path,
            role=sidecar.role,
            split=sidecar.split,
            episode_path=paths.get("development_episode"),
            source_inventory_sha256=expected["source_inventory_sha256"],
        )
        provenance_inputs = sidecar.provenance["inputs"]
        required_paths = [
            bundle,
            bundle.parent / "source-inventory.jsonl",
            parity,
            Path(manifest_path).resolve(),
            Path(paths["protocol"]),
            Path(assets["checkpoint_path"]),
            Path(assets["config_path"]),
            *(REPOSITORY / path for path in MOTIONBERT_CODE_PATHS),
        ]
        if "development_episode" in paths:
            required_paths.append(Path(paths["development_episode"]))
        for path in required_paths:
            if provenance_inputs.get(str(path)) != sha256_file(path):
                raise ValueError(f"MotionBERT provenance input changed: {path.name}")
        for prefix in ("aggregate", "missing_list"):
            source_path = data_root / getattr(contract, f"{prefix}_relative_path")
            if provenance_inputs.get(str(source_path)) != getattr(
                contract, f"{prefix}_sha256"
            ):
                raise ValueError("MotionBERT physical source hash is missing")
    except (KeyError, TypeError, OSError) as exc:
        raise ValueError("MotionBERT provenance is incomplete or unavailable") from exc
    configuration = sidecar.provenance.get("configuration")
    if not isinstance(configuration, dict) or any(
        configuration.get(key) != value
        for key, value in {
            "batch_size": 32,
            "dtype": "float32",
            "condition": "clean",
        }.items()
    ):
        raise ValueError("MotionBERT extraction configuration mismatch")
    git_sha = sidecar.provenance.get("git_sha")
    if (
        sidecar.upstream_sha256 != expected["upstream_sha256"]
        or sidecar.encoder_checkpoint_sha256 != expected["checkpoint_sha256"]
        or sidecar.shape[1] != 8704
        or sidecar.dtype != "float32"
        or sidecar.provenance.get("git_dirty") is not False
        or not isinstance(git_sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", git_sha) is None
        or sidecar.provenance.get("dependency_lock_sha256")
        != expected["dependency_lock_sha256"]
    ):
        raise ValueError("MotionBERT cache format or clean-code provenance mismatch")
