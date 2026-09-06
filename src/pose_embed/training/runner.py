"""Deterministic lightweight-head training over cached feature fixtures."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.artifacts import (
    FeatureSidecar,
    validate_feature_artifact,
    validate_stretch_gate_evidence,
)
from pose_embed.config import (
    ExperimentConfig,
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.losses import (
    ContextualLossConfig,
    ContextualMetricLoss,
    MultiSimilarityWithMinerLoss,
    PairwiseContrastiveLoss,
    SupervisedContrastiveLoss,
)
from pose_embed.protocol import (
    protocol_digest,
    resolve_scientific_paths,
    validate_post_core_stretch_authorization,
)
from pose_embed.provenance import (
    capture_provenance,
    capture_runtime_telemetry,
    require_path_within,
    reset_peak_memory,
    sha256_file,
    write_immutable_json,
)
from pose_embed.training.sampler import BalancedBatchSampler


class NormalizedLinearHead(nn.Module):
    """Trainable linear retrieval head over cached frozen representations."""

    def __init__(self, input_dimension: int, embedding_dimension: int) -> None:
        super().__init__()
        self.projection = nn.Linear(input_dimension, embedding_dimension)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return functional.normalize(self.projection(features), dim=-1)


def _state_dict_digest(module: nn.Module) -> str:
    """Hash an initialized module without relying on pickle serialization."""
    digest = hashlib.sha256()
    for name, tensor in sorted(module.state_dict().items()):
        contiguous = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(json.dumps(list(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _json_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_loss(config: ExperimentConfig) -> nn.Module:
    """Build the exact declared core or gated-stretch objective."""
    if config.objective == "contrastive":
        return PairwiseContrastiveLoss(
            positive_margin=config.positive_margin,
            negative_margin=config.negative_margin,
        )
    if config.objective == "supcon":
        return SupervisedContrastiveLoss(temperature=config.temperature)
    if config.objective == "multi_similarity_with_miner":
        multi_similarity = config.multi_similarity
        if multi_similarity is None:  # protected by typed configuration
            raise ValueError("multi-similarity settings are required")
        return MultiSimilarityWithMinerLoss(
            library_version=multi_similarity.library_version,
            loss_alpha=multi_similarity.loss_alpha,
            loss_beta=multi_similarity.loss_beta,
            loss_base=multi_similarity.loss_base,
            miner_epsilon=multi_similarity.miner_epsilon,
            distance_p=multi_similarity.distance_p,
            distance_power=multi_similarity.distance_power,
        )
    contextual = config.contextual
    if contextual is None:  # protected by typed configuration; keeps mypy narrow
        raise ValueError("contextual settings are required")
    return ContextualMetricLoss(
        ContextualLossConfig(
            k=config.samples_per_class,
            eps=contextual.epsilon,
            alpha=contextual.straight_through_alpha,
            lam=contextual.contextual_weight,
            gamma=contextual.regularizer_weight,
            target_mean_similarity=contextual.target_mean_similarity,
            positive_margin=config.positive_margin,
            negative_margin=config.negative_margin,
        )
    )


def train_head(
    config_path: str | Path,
    input_path: str | Path,
    output_dir: str | Path,
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    device: str = "cpu",
    allow_fixture: bool = False,
    stretch_gate_evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    """Train one declared head and create an immutable run directory."""
    started_at = datetime.now(UTC)
    config = load_experiment(config_path)
    protocol = load_protocol(protocol_path)
    source = Path(input_path)
    sidecar = validate_feature_artifact(
        source,
        protocol=protocol,
        manifest_path=manifest_path,
        allow_fixture=allow_fixture,
    )
    if sidecar.scientific_use_allowed:
        validate_experiment_against_protocol(config, protocol)
    try:
        scientific_paths = resolve_scientific_paths(protocol)
    except ValueError:
        if sidecar.scientific_use_allowed:
            raise
        scientific_paths = None
    destination = Path(output_dir)
    if sidecar.scientific_use_allowed:
        assert scientific_paths is not None
        destination = require_path_within(
            destination,
            scientific_paths.root,
            label="scientific run output",
        )
    if (
        scientific_paths is not None
        and scientific_paths.test_opening_ledger.exists()
        and config.objective != "multi_similarity_with_miner"
    ):
        raise ValueError("training is forbidden after the final-test opening")
    if config.objective == "multi_similarity_with_miner":
        if stretch_gate_evidence_path is None:
            raise ValueError(
                "Multi-Similarity training requires all four stretch-gate "
                "evidence files"
            )
        validate_stretch_gate_evidence(
            stretch_gate_evidence_path,
            protocol=protocol,
        )
        if sidecar.scientific_use_allowed:
            if (
                scientific_paths is None
                or not scientific_paths.test_opening_ledger.is_file()
            ):
                raise ValueError(
                    "scientific stretch training requires the completed core opening"
                )
            validate_post_core_stretch_authorization(
                protocol,
                stretch_gate_evidence_path,
            )
    elif stretch_gate_evidence_path is not None:
        raise ValueError("stretch gate evidence is only valid for Multi-Similarity")
    if sidecar.role != "training":
        raise ValueError("training requires a feature sidecar with the training role")
    if sidecar.split not in {"development_train", "final_train"}:
        raise ValueError("training cannot consume novel or query feature splits")

    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"refusing to reuse non-empty run directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    attempt_id = str(uuid.uuid4())
    attempt_path = destination / "attempt.json"
    attempt_payload = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "status": "started",
        "started_at": started_at.isoformat(),
        "objective": config.objective,
        "seed": config.seed,
        "device": device,
        "scientific_use_allowed": sidecar.scientific_use_allowed,
        "protocol_sha256": protocol_digest(protocol),
        "config_sha256": sha256_file(config_path),
        "input_artifact_sha256": sha256_file(source),
        "feature_sidecar_sha256": sha256_file(
            source.with_suffix(f"{source.suffix}.manifest.json")
        ),
        "manifest_sha256": sha256_file(manifest_path),
        "canonical_test_opening_ledger": (
            str(scientific_paths.test_opening_ledger)
            if scientific_paths is not None
            else None
        ),
        "provenance": capture_provenance(
            command="train-attempt",
            configuration={
                "experiment": config.model_dump(mode="json"),
                "device": device,
            },
            inputs=[
                config_path,
                protocol_path,
                manifest_path,
                source,
                source.with_suffix(f"{source.suffix}.manifest.json"),
            ],
            started_at=started_at,
        ),
    }
    write_immutable_json(attempt_path, attempt_payload)
    try:
        summary = _execute_training(
            config,
            source,
            destination,
            sidecar=sidecar,
            config_path=config_path,
            protocol_path=protocol_path,
            manifest_path=manifest_path,
            device=device,
            stretch_gate_evidence_path=stretch_gate_evidence_path,
            started_at=started_at,
            attempt_sha256=sha256_file(attempt_path),
        )
    except BaseException as exc:
        known_files = {}
        for name in ("batch-plan.json", "head.pt", "metrics.json", "run-manifest.json"):
            candidate = destination / name
            if candidate.is_file():
                known_files[name] = sha256_file(candidate)
        write_immutable_json(
            destination / "outcome.json",
            {
                "schema_version": 1,
                "attempt_id": attempt_id,
                "status": "failed",
                "ended_at": datetime.now(UTC).isoformat(),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "artifacts_written": known_files,
            },
        )
        raise
    write_immutable_json(
        destination / "outcome.json",
        {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "status": "success",
            "ended_at": datetime.now(UTC).isoformat(),
            "checkpoint_sha256": summary["checkpoint_sha256"],
            "batch_plan_sha256": summary["batch_plan_sha256"],
            "metrics_sha256": sha256_file(destination / "metrics.json"),
            "run_manifest_sha256": sha256_file(destination / "run-manifest.json"),
        },
    )
    return summary


def _execute_training(
    config: ExperimentConfig,
    source: Path,
    destination: Path,
    *,
    sidecar: FeatureSidecar,
    config_path: str | Path,
    protocol_path: str | Path,
    manifest_path: str | Path,
    device: str,
    stretch_gate_evidence_path: str | Path | None,
    started_at: datetime,
    attempt_sha256: str,
) -> dict[str, Any]:
    """Execute one preflighted attempt inside its immutable run directory."""
    with np.load(source, allow_pickle=False) as archive:
        key = "features" if "features" in archive.files else "embeddings"
        if key not in archive.files or "labels" not in archive.files:
            raise ValueError(
                "training NPZ requires features (or embeddings) and labels"
            )
        features = torch.as_tensor(np.asarray(archive[key]), dtype=torch.float32)
        labels = torch.as_tensor(np.asarray(archive["labels"]), dtype=torch.long)
    if features.ndim != 2 or labels.shape != (features.shape[0],):
        raise ValueError("features must be [N,D] and labels must be [N]")
    if features.shape[1] != config.input_dimension:
        raise ValueError(
            f"config input_dimension={config.input_dimension}, "
            f"data has {features.shape[1]}"
        )

    torch.manual_seed(config.seed)
    runtime_device = torch.device(device)
    reset_peak_memory(runtime_device)
    head = NormalizedLinearHead(config.input_dimension, config.embedding_dimension).to(
        runtime_device
    )
    initialization_sha256 = _state_dict_digest(head)
    features = features.to(runtime_device)
    labels = labels.to(runtime_device)
    criterion = build_loss(config)
    optimizer = torch.optim.AdamW(
        head.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    label_values = labels.detach().cpu().tolist()
    epoch_batches: list[list[list[int]]] = []
    for epoch in range(config.epochs):
        sampler = BalancedBatchSampler(
            label_values,
            classes_per_batch=config.classes_per_batch,
            samples_per_class=config.samples_per_class,
            seed=config.seed + epoch,
        )
        epoch_batches.append([list(indexes) for indexes in sampler])
    if any(not batches for batches in epoch_batches):
        raise ValueError("balanced batch plan contains an empty epoch")
    epoch_batch_plan_sha256 = [_json_digest(batches) for batches in epoch_batches]
    batch_plan_path = destination / "batch-plan.json"
    write_immutable_json(
        batch_plan_path,
        {
            "schema_version": 1,
            "seed": config.seed,
            "classes_per_batch": config.classes_per_batch,
            "samples_per_class": config.samples_per_class,
            "sample_order_sha256": sidecar.sample_order_sha256,
            "epoch_sha256": epoch_batch_plan_sha256,
            "epochs": epoch_batches,
        },
    )
    batch_plan_sha256 = sha256_file(batch_plan_path)

    epoch_losses: list[float] = []
    for batches in epoch_batches:
        batch_losses: list[float] = []
        for indexes in batches:
            batch = torch.as_tensor(indexes, device=runtime_device)
            embeddings = head(features[batch])
            loss_output = criterion(embeddings, labels[batch])
            loss = loss_output[0] if isinstance(loss_output, tuple) else loss_output
            if not torch.isfinite(loss):
                raise RuntimeError("training produced a non-finite loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            batch_losses.append(float(loss.detach().cpu()))
        epoch_losses.append(sum(batch_losses) / len(batch_losses))

    checkpoint_path = destination / "head.pt"
    torch.save(
        {
            "state_dict": head.state_dict(),
            "config": config.model_dump(mode="json"),
        },
        checkpoint_path,
    )
    if runtime_device.type == "cuda":
        torch.cuda.synchronize(runtime_device)
    ended_at = datetime.now(UTC)
    telemetry = capture_runtime_telemetry(
        started_at=started_at,
        ended_at=ended_at,
        device=runtime_device,
    )
    summary: dict[str, Any] = {
        "objective": config.objective,
        "seed": config.seed,
        "epochs": config.epochs,
        "epoch_losses": epoch_losses,
        "initial_loss": epoch_losses[0],
        "final_loss": epoch_losses[-1],
        "input_metadata": sidecar.model_dump(mode="json"),
        "initialization_sha256": initialization_sha256,
        "batch_plan_sha256": batch_plan_sha256,
        "epoch_batch_plan_sha256": epoch_batch_plan_sha256,
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "telemetry": telemetry.model_dump(mode="json"),
    }
    write_immutable_json(destination / "metrics.json", summary)
    provenance = capture_provenance(
        command="train",
        configuration={
            "experiment": config.model_dump(mode="json"),
            "device": str(runtime_device),
            "attempt_sha256": attempt_sha256,
        },
        inputs=[
            config_path,
            protocol_path,
            manifest_path,
            source,
            source.with_suffix(f"{source.suffix}.manifest.json"),
        ]
        + ([stretch_gate_evidence_path] if stretch_gate_evidence_path else []),
        started_at=started_at,
        ended_at=ended_at,
    )
    provenance["scientific_use_allowed"] = sidecar.scientific_use_allowed
    provenance["protocol_sha256"] = sidecar.protocol_sha256
    provenance["feature_sidecar"] = sidecar.model_dump(mode="json")
    provenance["initialization_sha256"] = initialization_sha256
    provenance["batch_plan_sha256"] = batch_plan_sha256
    provenance["epoch_batch_plan_sha256"] = epoch_batch_plan_sha256
    provenance["telemetry"] = telemetry.model_dump(mode="json")
    provenance["outputs"] = {
        "checkpoint": summary["checkpoint_sha256"],
        "metrics": sha256_file(destination / "metrics.json"),
        "batch_plan": batch_plan_sha256,
    }
    write_immutable_json(destination / "run-manifest.json", provenance)
    return summary
