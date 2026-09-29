"""Deterministic lightweight-head training over cached feature fixtures."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import uuid
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch
import torch.nn.functional as functional
from torch import nn

from pose_embed.artifacts import (
    FeatureSidecar,
    load_feature_sidecar,
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

TrainingStage = Literal["engineering_pilot", "development_selection", "final_training"]
_PILOT_SNAPSHOTS = (5, 10, 15, 20)


class NormalizedLinearHead(nn.Module):
    """Trainable linear retrieval head over cached frozen representations."""

    def __init__(self, input_dimension: int, embedding_dimension: int) -> None:
        super().__init__()
        self.projection = nn.Linear(
            input_dimension, embedding_dimension, dtype=torch.float32
        )

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
    stage: TrainingStage | None = None,
    development_gallery_path: str | Path | None = None,
    development_query_path: str | Path | None = None,
    development_gallery_manifest_path: str | Path | None = None,
    development_query_manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Train a fresh head while holding the dataset's auxiliary-operation seal."""
    from pose_embed.dataset_seal import OPENING, dataset_access, registered_roots

    config = load_experiment(config_path)
    guarded = bool(os.environ.get("POSE_EMBED_ARTIFACT_ROOT"))
    if guarded and config.objective == "multi_similarity_with_miner":
        # Historical v1 permits its locked stretch study after the v1 core opening.
        # The dataset-wide event never grants this exception to another study.
        if any((root / OPENING).exists() for root in registered_roots()):
            raise ValueError("training is forbidden after the dataset test opening")
        guarded = False
    with dataset_access() if guarded else nullcontext():
        return _train_head(
            config_path,
            input_path,
            output_dir,
            protocol_path=protocol_path,
            manifest_path=manifest_path,
            device=device,
            allow_fixture=allow_fixture,
            stretch_gate_evidence_path=stretch_gate_evidence_path,
            stage=stage,
            development_paths=(
                development_gallery_path,
                development_query_path,
                development_gallery_manifest_path,
                development_query_manifest_path,
            ),
        )


def _train_head(
    config_path: str | Path,
    input_path: str | Path,
    output_dir: str | Path,
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    device: str,
    allow_fixture: bool,
    stretch_gate_evidence_path: str | Path | None,
    stage: TrainingStage | None,
    development_paths: tuple[str | Path | None, ...],
) -> dict[str, Any]:
    """Preflight and preserve every attempted optimization without overwrites."""
    started_at = datetime.now(UTC)
    config = load_experiment(config_path)
    protocol = load_protocol(protocol_path)
    source = Path(input_path)
    preliminary = load_feature_sidecar(source)
    if (
        preliminary.scientific_use_allowed
        and config.objective != "multi_similarity_with_miner"
    ):
        from pose_embed.dataset_seal import require_dataset_unopened

        require_dataset_unopened(require_registry=True)
    is_v3 = protocol.protocol_id == "protocol-v3"
    if stage is not None or is_v3:
        from pose_embed.models.motionbert import configure_deterministic_inference

        # Provenance and cache validation may probe CUDA, so configure it first.
        configure_deterministic_inference()
    if is_v3:
        if stage not in {
            "engineering_pilot",
            "development_selection",
            "final_training",
        }:
            raise ValueError("v3 training requires an explicit training stage")
        if preliminary.scientific_use_allowed:
            from pose_embed.dataset_seal import require_dataset_unopened
            from pose_embed.motionbert_inputs import require_clean_repository
            from pose_embed.protocol_v3 import require_v3_design

            require_clean_repository()
            _require_v3_runtime(protocol)
            require_dataset_unopened(require_registry=True)
            require_v3_design(protocol)
            if stage != "engineering_pilot":
                from pose_embed.protocol_v3 import require_v3_selection_authorization

                require_v3_selection_authorization(protocol)
            if stage == "final_training":
                raise ValueError(
                    "v3 final training requires a selected-rate lock; "
                    "not yet authorized"
                )
    elif stage is not None and not allow_fixture:
        raise ValueError("engineering stages require protocol-v3 or explicit fixtures")
    sidecar = validate_feature_artifact(
        source,
        protocol=protocol,
        manifest_path=manifest_path,
        allow_fixture=allow_fixture,
    )
    if stage is not None and not is_v3 and sidecar.scientific_use_allowed:
        raise ValueError("scientific engineering stages require protocol-v3")
    if sidecar.scientific_use_allowed or is_v3:
        validate_experiment_against_protocol(config, protocol)
    if stage is not None and stage not in {
        "engineering_pilot",
        "development_selection",
        "final_training",
    }:
        raise ValueError("unknown training stage")
    if stage is not None:
        expected_split = (
            "final_train" if stage == "final_training" else "development_train"
        )
        if sidecar.split != expected_split:
            raise ValueError("training stage requires its complete auxiliary split")
        if sidecar.scientific_use_allowed and sidecar.shape[0] != (
            95001 if stage == "final_training" else 76013
        ):
            raise ValueError("v3 training requires the full declared auxiliary rows")
        if stage == "engineering_pilot" and (
            config.epochs,
            config.seed,
            config.learning_rate,
        ) != (20, 7, 3e-4):
            raise ValueError(
                "engineering pilot requires 20 epochs, seed 7 and learning rate 3e-4"
            )
    development = _load_development(
        development_paths,
        protocol=protocol,
        training=sidecar,
        allow_fixture=allow_fixture,
        required=stage in {"engineering_pilot", "development_selection"},
    )
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
            scientific_paths.root / "study-v3" if is_v3 else scientific_paths.root,
            label="scientific run output",
        )
    if scientific_paths is not None and (
        (scientific_paths.root / "benchmark-v2/locks/test-opening.json").exists()
        or (
            scientific_paths.test_opening_ledger.exists()
            and config.objective != "multi_similarity_with_miner"
        )
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
    if stage is not None:
        attempt_payload.update(_stage_identity(stage))
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
            stage=stage,
            development=development,
        )
    except BaseException as exc:
        known_files = {}
        for candidate in sorted(destination.rglob("*")):
            if candidate.is_file():
                known_files[str(candidate.relative_to(destination))] = sha256_file(
                    candidate
                )
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
    stage: TrainingStage | None = None,
    development: dict[str, Any] | None = None,
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
        device=runtime_device, dtype=torch.float32
    )
    initialization_sha256 = _state_dict_digest(head)
    features = features.to(runtime_device)
    labels = labels.to(runtime_device)
    criterion = build_loss(config)
    optimizer = torch.optim.AdamW(
        head.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        betas=(0.9, 0.999),
        eps=1e-8,
        amsgrad=False,
        **({"foreach": False, "fused": False} if stage is not None else {}),
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
    diagnostic_records: list[dict[str, Any]] = []
    epoch_records: dict[str, str] = {}
    updates = 0
    training_seconds = 0.0
    validation_seconds = 0.0
    checkpoint_seconds = 0.0
    if stage == "engineering_pilot":
        assert development is not None
        before = time.perf_counter()
        record = _development_record(head, development, runtime_device, epoch=0)
        record.update(_stage_identity(stage))
        write_immutable_json(destination / "epoch-000.json", record)
        epoch_records["epoch-000.json"] = sha256_file(destination / "epoch-000.json")
        validation_seconds += time.perf_counter() - before
    for epoch, batches in enumerate(epoch_batches, 1):
        batch_losses: list[float] = []
        before = time.perf_counter()
        for batch_index, indexes in enumerate(batches):
            batch = torch.as_tensor(indexes, device=runtime_device)
            raw = head.projection(features[batch])
            if stage is not None:
                _require_projection_health(raw)
            embeddings = functional.normalize(raw, dim=-1)
            loss_output = criterion(embeddings, labels[batch])
            loss = loss_output[0] if isinstance(loss_output, tuple) else loss_output
            if not torch.isfinite(loss):
                raise RuntimeError("training produced a non-finite loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if stage is not None:
                gradient_norm = _gradient_health(head)
            optimizer.step()
            if stage is not None and not all(
                torch.isfinite(parameter).all() for parameter in head.parameters()
            ):
                raise RuntimeError("training produced non-finite updated parameters")
            updates += 1
            batch_losses.append(float(loss.detach().cpu()))
            if stage is not None and (updates == 1 or batch_index == len(batches) - 1):
                diagnostics = _batch_diagnostics(
                    embeddings.detach(), labels[batch], config
                )
                diagnostics.update(
                    {
                        "epoch": epoch,
                        "update": updates,
                        "loss": batch_losses[-1],
                        "gradient_norm": gradient_norm,
                    }
                )
                diagnostic_records.append(diagnostics)
                write_immutable_json(
                    destination / "diagnostics" / f"update-{updates:07d}.json",
                    diagnostics,
                )
        if runtime_device.type == "cuda":
            torch.cuda.synchronize(runtime_device)
        training_seconds += time.perf_counter() - before
        epoch_losses.append(sum(batch_losses) / len(batch_losses))
        snapshot = stage == "engineering_pilot" and epoch in _PILOT_SNAPSHOTS
        if snapshot or epoch == config.epochs:
            checkpoint_path = destination / (
                "head.pt" if epoch == config.epochs else f"epochs/{epoch:03d}/head.pt"
            )
            before = time.perf_counter()
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint = {
                "state_dict": head.state_dict(),
                "config": config.model_dump(mode="json"),
            }
            if stage is not None:
                checkpoint.update(_stage_identity(stage))
                checkpoint["epoch"] = epoch
            with checkpoint_path.open("xb") as stream:
                torch.save(checkpoint, stream)
            checkpoint_seconds += time.perf_counter() - before
            if snapshot or stage == "development_selection":
                assert development is not None
                before = time.perf_counter()
                record = _development_record(
                    head,
                    development,
                    runtime_device,
                    epoch=epoch,
                    output=destination / f"epochs/{epoch:03d}",
                )
                record.update(_stage_identity(stage))
                record.update(
                    {
                        "checkpoint": str(checkpoint_path.relative_to(destination)),
                        "checkpoint_sha256": sha256_file(checkpoint_path),
                        "updates": updates,
                    }
                )
                record_path = destination / f"epoch-{epoch:03d}.json"
                write_immutable_json(record_path, record)
                epoch_records[record_path.name] = sha256_file(record_path)
                validation_seconds += time.perf_counter() - before
    expected_updates = config.epochs * math.ceil(
        len(labels) / (config.classes_per_batch * config.samples_per_class)
    )
    if updates != expected_updates:
        raise RuntimeError("training did not complete the prescribed update count")
    checkpoint_path = destination / "head.pt"
    if runtime_device.type == "cuda":
        torch.cuda.synchronize(runtime_device)
    scientific_design = None
    if stage is not None and sidecar.scientific_use_allowed:
        from pose_embed.motionbert_inputs import require_clean_repository
        from pose_embed.protocol_v3 import require_v3_design

        require_clean_repository()
        locked_protocol = load_protocol(protocol_path)
        scientific_design = require_v3_design(locked_protocol)
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
    if stage is not None:
        from pose_embed.models.motionbert import inference_environment

        summary.update(_stage_identity(stage))
        summary["training_environment"] = inference_environment(runtime_device)
        summary.update(
            {
                "updates": updates,
                "expected_updates": expected_updates,
                "epoch_records": epoch_records,
                "diagnostics": diagnostic_records,
                "optimizer": {
                    "name": "AdamW",
                    "betas": [0.9, 0.999],
                    "eps": 1e-8,
                    "amsgrad": False,
                    "foreach": False,
                    "fused": False,
                    "weight_decay_weight_and_bias": config.weight_decay,
                },
                "stage_seconds": {
                    "training": training_seconds,
                    "validation": validation_seconds,
                    "checkpoint": checkpoint_seconds,
                },
                "peak_host_memory_bytes": capture_runtime_telemetry(
                    started_at=started_at, ended_at=ended_at
                ).peak_memory_bytes,
                "peak_gpu_allocated_bytes": int(
                    torch.cuda.max_memory_allocated(runtime_device)
                )
                if runtime_device.type == "cuda"
                else 0,
                "peak_gpu_reserved_bytes": int(
                    torch.cuda.max_memory_reserved(runtime_device)
                )
                if runtime_device.type == "cuda"
                else 0,
                "checkpoint_bytes": sum(
                    path.stat().st_size for path in destination.rglob("*.pt")
                ),
            }
        )
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
        + ([stretch_gate_evidence_path] if stretch_gate_evidence_path else [])
        + (development["input_paths"] if development is not None else []),
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
    if stage is not None:
        provenance.update(_stage_identity(stage))
        provenance["configuration"].update(_stage_identity(stage))
        provenance["epoch_records"] = epoch_records
        provenance["training_environment"] = summary["training_environment"]
        provenance["outputs"]["pilot_artifacts"] = {
            str(path.relative_to(destination)): sha256_file(path)
            for path in sorted(destination.rglob("*"))
            if path.is_file()
            and path.name
            not in {"attempt.json", "metrics.json", "batch-plan.json", "head.pt"}
        }
        if development is not None:
            provenance["development_inputs"] = development["bindings"]
        if scientific_design is not None:
            provenance["design_code_sha256"] = scientific_design.code_sha256
            provenance["design_lock_sha256"] = sha256_file(
                resolve_scientific_paths(locked_protocol).root
                / locked_protocol.test_access.design_lock_relative_path
            )
    write_immutable_json(destination / "run-manifest.json", provenance)
    return summary


def _stage_identity(stage: TrainingStage) -> dict[str, Any]:
    return {
        "stage": stage,
        "selection_eligible": stage == "development_selection",
        "final_eligible": stage == "final_training",
    }


def _require_v3_runtime(protocol: Any) -> None:
    expected = protocol.training
    if (
        f"{sys.version_info.major}.{sys.version_info.minor}" != expected.python_version
        or str(torch.__version__).split("+", 1)[0] != expected.torch_version
        or str(np.__version__).split("+", 1)[0] != expected.numpy_version
    ):
        raise ValueError(
            "scientific v3 training requires the pinned Python/Torch/NumPy runtime"
        )


def _load_development(
    paths: tuple[str | Path | None, ...],
    *,
    protocol: Any,
    training: FeatureSidecar,
    allow_fixture: bool,
    required: bool,
) -> dict[str, Any] | None:
    if not required:
        if any(path is not None for path in paths):
            raise ValueError("development inputs require a pilot or selection stage")
        return None
    if any(path is None for path in paths):
        raise ValueError(
            "pilot/selection requires clean development gallery and query "
            "caches and manifests"
        )
    gallery_path, query_path, gallery_manifest, query_manifest = (
        Path(path).resolve() for path in paths
    )
    pairs = (
        (gallery_path, gallery_manifest, "gallery_clean"),
        (query_path, query_manifest, "query_clean"),
    )
    result: dict[str, Any] = {"input_paths": [], "bindings": {}}
    for path, manifest, role in pairs:
        sidecar = validate_feature_artifact(
            path, protocol=protocol, manifest_path=manifest, allow_fixture=allow_fixture
        )
        if (sidecar.role, sidecar.split, sidecar.condition, sidecar.array_key) != (
            role,
            "development_validation",
            "clean",
            "features",
        ):
            raise ValueError("pilot scoring requires clean pre-head development caches")
        for field in (
            "backend",
            "scientific_use_allowed",
            "protocol_sha256",
            "preprocessing_sha256",
            "encoder_checkpoint_sha256",
            "upstream_sha256",
        ):
            if getattr(sidecar, field) != getattr(training, field):
                raise ValueError(f"development cache {field} differs from training")
        if sidecar.shape[1] != training.shape[1]:
            raise ValueError("development feature dimensions differ from training")
        if sidecar.scientific_use_allowed and sidecar.shape[0] != (
            20 if role == "gallery_clean" else 18929
        ):
            raise ValueError("pilot scoring requires the complete development episode")
        with np.load(path, allow_pickle=False) as archive:
            values = torch.as_tensor(
                np.asarray(archive["features"]), dtype=torch.float32
            )
            labels = torch.as_tensor(np.asarray(archive["labels"]), dtype=torch.long)
        key = "gallery" if role == "gallery_clean" else "queries"
        result[key] = (values, labels, sidecar.sample_ids)
        for source in (path, manifest, path.with_suffix(".npz.manifest.json")):
            result["input_paths"].append(source)
            result["bindings"][str(source)] = sha256_file(source)
    gallery_ids = result["gallery"][2]
    query_ids = result["queries"][2]
    from pose_embed.data import ManifestRecord

    gallery_performances = {
        ManifestRecord(
            sample_id=value, split="development_validation"
        ).ntu.performance_id
        for value in gallery_ids
    }
    if any(
        ManifestRecord(
            sample_id=value, split="development_validation"
        ).ntu.performance_id
        in gallery_performances
        for value in query_ids
    ):
        raise ValueError("development queries include a gallery performance")
    training_labels = {int(value[-3:]) for value in training.sample_ids}
    if training_labels.intersection(
        result["gallery"][1].tolist()
    ) or training_labels.intersection(result["queries"][1].tolist()):
        raise ValueError("development scoring labels overlap training labels")
    return result


def _require_projection_health(raw: torch.Tensor) -> None:
    if not torch.isfinite(raw).all() or torch.any(
        torch.linalg.vector_norm(raw, dim=1) == 0
    ):
        raise RuntimeError("head produced a non-finite or zero projected vector")


def _gradient_health(head: nn.Module) -> float:
    gradients = [parameter.grad for parameter in head.parameters()]
    if any(
        gradient is None or not torch.isfinite(gradient).all() for gradient in gradients
    ):
        raise RuntimeError("training produced non-finite or missing gradients")
    return math.sqrt(
        sum(
            float(gradient.detach().to(torch.float64).square().sum())
            for gradient in gradients
        )
    )


def _embedding_health(embeddings: torch.Tensor) -> dict[str, float]:
    values = embeddings.to(torch.float64)
    if not torch.isfinite(values).all():
        raise RuntimeError("development embeddings are non-finite")
    norm_error = float((torch.linalg.vector_norm(values, dim=1) - 1.0).abs().max())
    variance = float((values - values.mean(dim=0)).square().sum(dim=1).mean())
    if norm_error > 1e-5 or variance <= 1e-6:
        raise RuntimeError(
            "development head health failed unit-norm or variance collapse check"
        )
    return {"max_normalization_error": norm_error, "embedding_variance": variance}


def _development_record(
    head: NormalizedLinearHead,
    development: dict[str, Any],
    device: torch.device,
    *,
    epoch: int,
    output: Path | None = None,
) -> dict[str, Any]:
    from pose_embed.evaluation.metrics import evaluate_one_shot

    projected = {}
    with torch.no_grad():
        for name in ("gallery", "queries"):
            values = development[name][0]
            chunks = []
            for start in range(0, len(values), 256):
                raw = head.projection(values[start : start + 256].to(device))
                _require_projection_health(raw)
                chunks.append(functional.normalize(raw, dim=-1).cpu())
            projected[name] = torch.cat(chunks)
    health = _embedding_health(projected["queries"])
    record: dict[str, Any] = {
        "epoch": epoch,
        "health": health,
        "development_inputs": development["bindings"],
    }
    if output is not None:
        evaluation = evaluate_one_shot(
            projected["gallery"],
            development["gallery"][1],
            projected["queries"],
            development["queries"][1],
            query_ids=development["queries"][2],
        )
        record["scores"] = evaluation.as_dict()
        output.mkdir(parents=True, exist_ok=True)
        record["projections"] = {}
        for name, embeddings in projected.items():
            path = output / f"{name}.npz"
            with path.open("xb") as stream:
                np.savez(
                    stream,
                    embeddings=embeddings.numpy(),
                    labels=development[name][1].numpy(),
                    sample_ids=np.asarray(development[name][2]),
                )
            record["projections"][str(path.resolve())] = sha256_file(path)
    return record


def _batch_diagnostics(
    embeddings: torch.Tensor, labels: torch.Tensor, config: ExperimentConfig
) -> dict[str, Any]:
    from pose_embed.losses.contextual import contextual_similarity

    with torch.no_grad():
        similarities = (
            functional.normalize(embeddings, dim=1)
            @ functional.normalize(embeddings, dim=1).T
        )
        same = labels[:, None] == labels[None, :]
        positive = same & ~torch.eye(
            len(labels), dtype=torch.bool, device=labels.device
        )
        negative = ~same
        result: dict[str, Any] = {
            "active_positive_hinge_fraction": float(
                (similarities[positive] < config.positive_margin).double().mean()
            ),
            "active_negative_hinge_fraction": float(
                (similarities[negative] > config.negative_margin).double().mean()
            ),
            "embedding_variance": float(
                (embeddings.double() - embeddings.double().mean(dim=0))
                .square()
                .sum(dim=1)
                .mean()
            ),
            "cosine_quantiles": torch.quantile(
                similarities[
                    ~torch.eye(len(labels), dtype=torch.bool, device=labels.device)
                ].double(),
                torch.tensor(
                    [0, 0.25, 0.5, 0.75, 1], dtype=torch.float64, device=labels.device
                ),
            )
            .cpu()
            .tolist(),
        }
        if config.objective == "contextual":
            assert config.contextual is not None
            _, auxiliary = contextual_similarity(
                embeddings,
                k=config.samples_per_class,
                eps=config.contextual.epsilon,
                alpha=config.contextual.straight_through_alpha,
            )
            _, components = build_loss(config)(embeddings, labels)
            result["loss_components"] = {
                key: float(value) for key, value in components.items()
            }
            neighbors = auxiliary["neighborhood"].sum(dim=1)
            result["neighborhood_counts"] = neighbors.cpu().tolist()
            result["reciprocal_counts"] = (
                auxiliary["reciprocal"].sum(dim=1).cpu().tolist()
            )
            result["empty_complement_count"] = int((neighbors == len(labels)).sum())
        else:
            result["loss_components"] = {
                config.objective: float(build_loss(config)(embeddings, labels))
            }
    return result


def validate_engineering_pilot(run_dir: str | Path) -> dict[str, Any]:
    """Rehash the complete immutable pilot, including all scores and snapshots.

    This validates engineering evidence only; a pilot is never selection or final
    evidence, even when its learning rate matches a selection candidate.
    """
    root = Path(run_dir).resolve()
    manifest = json.loads((root / "run-manifest.json").read_text())
    metrics = json.loads((root / "metrics.json").read_text())
    outcome = json.loads((root / "outcome.json").read_text())
    attempt = json.loads((root / "attempt.json").read_text())
    for value in (manifest, metrics, attempt):
        if any(
            value.get(key) != expected
            for key, expected in _stage_identity("engineering_pilot").items()
        ):
            raise ValueError("engineering pilot stage/eligibility binding is invalid")
    if (
        manifest["configuration"]["attempt_sha256"]
        != sha256_file(root / "attempt.json")
        or outcome.get("attempt_id") != attempt.get("attempt_id")
        or attempt.get("protocol_sha256") != manifest.get("protocol_sha256")
        or metrics["input_metadata"] != manifest["feature_sidecar"]
    ):
        raise ValueError("engineering pilot attempt/input provenance changed")
    if outcome.get("status") != "success" or outcome.get(
        "run_manifest_sha256"
    ) != sha256_file(root / "run-manifest.json"):
        raise ValueError("engineering pilot did not complete successfully")
    for name, key in (
        ("head.pt", "checkpoint"),
        ("metrics.json", "metrics"),
        ("batch-plan.json", "batch_plan"),
    ):
        if sha256_file(root / name) != manifest["outputs"][key]:
            raise ValueError("engineering pilot output changed")
        if outcome.get(f"{key}_sha256") != manifest["outputs"][key]:
            raise ValueError("engineering pilot outcome output binding changed")
    for path, digest in manifest["inputs"].items():
        if sha256_file(path) != digest:
            raise ValueError("engineering pilot input changed")
    for path, digest in manifest["outputs"]["pilot_artifacts"].items():
        resolved = require_path_within(root / path, root, label="pilot artifact")
        if sha256_file(resolved) != digest:
            raise ValueError("engineering pilot artifact changed")
    expected_records = {f"epoch-{epoch:03d}.json" for epoch in (0, *_PILOT_SNAPSHOTS)}
    if (
        set(manifest["epoch_records"]) != expected_records
        or manifest["epoch_records"] != metrics["epoch_records"]
    ):
        raise ValueError(
            "engineering pilot requires all epoch diagnostics and snapshots"
        )
    config = ExperimentConfig.model_validate(manifest["configuration"]["experiment"])
    config_paths = [
        Path(path)
        for path, digest in manifest["inputs"].items()
        if digest == attempt["config_sha256"]
    ]
    if len(config_paths) != 1 or load_experiment(config_paths[0]) != config:
        raise ValueError("engineering pilot configuration differs from its input file")
    _validate_pilot_scientific_provenance(manifest, metrics, attempt, config)
    rows = manifest["feature_sidecar"]["shape"][0]
    expected_updates = 20 * math.ceil(
        rows / (config.classes_per_batch * config.samples_per_class)
    )
    if (
        (config.epochs, config.seed, config.learning_rate) != (20, 7, 3e-4)
        or metrics["updates"] != expected_updates
        or metrics["expected_updates"] != expected_updates
    ):
        raise ValueError(
            "engineering pilot budget differs from its fixed specification"
        )
    for name, digest in manifest["epoch_records"].items():
        if sha256_file(root / name) != digest:
            raise ValueError("engineering pilot epoch record changed")
        record = json.loads((root / name).read_text())
        epoch = int(name.removeprefix("epoch-").removesuffix(".json"))
        if record["epoch"] != epoch or any(
            record.get(key) != value
            for key, value in _stage_identity("engineering_pilot").items()
        ):
            raise ValueError("engineering pilot epoch identity changed")
        health = record["health"]
        if not (
            0 <= health["max_normalization_error"] <= 1e-5
            and math.isfinite(health["embedding_variance"])
            and health["embedding_variance"] > 1e-6
        ):
            raise ValueError(
                "engineering pilot failed its development health criterion"
            )
        if record["epoch"]:
            checkpoint = require_path_within(
                root / record["checkpoint"], root, label="pilot checkpoint"
            )
            if sha256_file(checkpoint) != record["checkpoint_sha256"]:
                raise ValueError("engineering pilot checkpoint changed")
            if record["updates"] != epoch * (expected_updates // 20):
                raise ValueError("engineering pilot snapshot update count changed")
            scores = record["scores"]
            rows = scores["per_query"]
            if len(rows) != scores["query_count"] or not rows:
                raise ValueError("engineering pilot scores omit queries")
            ranks = [row["rank"] for row in rows]
            for key, expected in (
                ("top1", sum(rank == 1 for rank in ranks) / len(ranks)),
                ("mrr", sum(1 / rank for rank in ranks) / len(ranks)),
                ("r_at_5", sum(rank <= 5 for rank in ranks) / len(ranks)),
            ):
                if not math.isclose(scores[key], expected, rel_tol=0, abs_tol=1e-12):
                    raise ValueError(
                        "engineering pilot score does not reproduce from ranks"
                    )
            _validate_pilot_scores(root, epoch, record, manifest)
    return metrics


def _validate_pilot_scientific_provenance(manifest, metrics, attempt, config) -> None:
    scientific = manifest["feature_sidecar"]["scientific_use_allowed"]
    if (
        manifest.get("scientific_use_allowed") != scientific
        or attempt.get("scientific_use_allowed") != scientific
    ):
        raise ValueError("engineering pilot scientific eligibility changed")
    if not scientific:
        return
    from pose_embed.dataset_seal import canonical_artifact_root
    from pose_embed.protocol_v3 import require_v3_design

    root = canonical_artifact_root()
    protocol = load_protocol(root / "study-v3/locks/protocol.v3.json")
    design = require_v3_design(protocol)
    validate_experiment_against_protocol(config, protocol)
    if (
        manifest["protocol_sha256"] != protocol_digest(protocol)
        or manifest["feature_sidecar"]["shape"] != [76013, 8704]
        or manifest["design_code_sha256"] != design.code_sha256
        or manifest["design_lock_sha256"]
        != sha256_file(root / protocol.test_access.design_lock_relative_path)
        or manifest.get("git_dirty") is not False
        or attempt["provenance"].get("git_dirty") is not False
        or manifest["git_sha"] != attempt["provenance"]["git_sha"]
    ):
        raise ValueError(
            "scientific pilot differs from its frozen code/protocol/release"
        )
    for value in (manifest, attempt["provenance"]):
        runtime = value["environment"]
        if (
            not runtime["python"].startswith(protocol.training.python_version + ".")
            or runtime["torch"].split("+", 1)[0] != protocol.training.torch_version
            or runtime["dependencies"]["numpy"] != protocol.training.numpy_version
            or value["dependency_lock_sha256"] != design.code_sha256["uv.lock"]
        ):
            raise ValueError("scientific pilot runtime differs from its frozen design")
    if metrics["training_environment"] != manifest["training_environment"]:
        raise ValueError("engineering pilot runtime evidence changed")


def _validate_pilot_scores(root, epoch, record, manifest) -> None:
    """Reproduce complete ranks from the exact saved, ordered query projections."""
    from pose_embed.evaluation.metrics import evaluate_one_shot

    development = {}
    for path in manifest["development_inputs"]:
        if path.endswith(".npz.manifest.json"):
            sidecar = FeatureSidecar.model_validate_json(Path(path).read_text())
            development[sidecar.role] = sidecar
    projected = {}
    for name, role in (("gallery", "gallery_clean"), ("queries", "query_clean")):
        path = root / f"epochs/{epoch:03d}/{name}.npz"
        if record["projections"].get(str(path)) != sha256_file(path):
            raise ValueError("engineering pilot projection binding changed")
        with np.load(path, allow_pickle=False) as archive:
            ids = tuple(str(value) for value in archive["sample_ids"])
            labels = np.asarray(archive["labels"])
            if ids != development[role].sample_ids or not np.array_equal(
                labels, [int(value[-3:]) for value in ids]
            ):
                raise ValueError("engineering pilot projected identities changed")
            projected[name] = (
                torch.from_numpy(np.asarray(archive["embeddings"])),
                torch.from_numpy(labels),
                ids,
            )
    scores = evaluate_one_shot(
        projected["gallery"][0],
        projected["gallery"][1],
        projected["queries"][0],
        projected["queries"][1],
        query_ids=projected["queries"][2],
    ).as_dict()
    if record["scores"] != scores:
        raise ValueError(
            "engineering pilot complete scores differ from saved projections"
        )


def check_learnable_fixture(
    config: ExperimentConfig, *, device: str = "cpu"
) -> dict[str, Any]:
    """Exercise the same head, physical batch and optimizer for exactly 1,000 steps.

    Each of 32 rows selects a distinct coordinate. Labels form eight groups of
    four; this intentionally learnable fixture is independent of licensed poses.
    Reduced dimensions may be used in unit tests but never claim the full gate.
    """
    from pose_embed.models.motionbert import configure_deterministic_inference

    configure_deterministic_inference()
    if config.input_dimension < 32 or (
        config.classes_per_batch,
        config.samples_per_class,
    ) != (8, 4):
        raise ValueError(
            "learnable fixture requires at least 32 input values "
            "and physical 8 x 4 batches"
        )
    if (config.seed, config.learning_rate, config.weight_decay) != (7, 3e-4, 1e-4):
        raise ValueError("learnable fixture uses the fixed pilot optimizer and seed")
    torch.manual_seed(config.seed)
    head = NormalizedLinearHead(config.input_dimension, config.embedding_dimension).to(
        device=device, dtype=torch.float32
    )
    initialization_sha256 = _state_dict_digest(head)
    features = torch.zeros(
        32, config.input_dimension, dtype=torch.float32, device=device
    )
    features[:, :32] = torch.eye(32, device=device)
    labels = torch.arange(8, device=device).repeat_interleave(4)
    criterion = build_loss(config)
    optimizer = torch.optim.AdamW(
        head.parameters(),
        lr=3e-4,
        weight_decay=1e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        amsgrad=False,
        foreach=False,
        fused=False,
    )
    for _ in range(1000):
        raw = head.projection(features)
        _require_projection_health(raw)
        embeddings = functional.normalize(raw, dim=1)
        loss_output = criterion(embeddings, labels)
        loss = loss_output[0] if isinstance(loss_output, tuple) else loss_output
        if not torch.isfinite(loss):
            raise RuntimeError("learnable fixture loss is non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        _gradient_health(head)
        optimizer.step()
        if not all(torch.isfinite(parameter).all() for parameter in head.parameters()):
            raise RuntimeError("learnable fixture parameters are non-finite")
    with torch.no_grad():
        embeddings = head(features)
        similarity = embeddings @ embeddings.T
        similarity.fill_diagonal_(-torch.inf)
        accuracy = float(labels[similarity.argmax(dim=1)].eq(labels).double().mean())
    if accuracy != 1.0:
        raise RuntimeError(
            "learnable fixture did not reach 100% self-excluded retrieval"
        )
    return {
        "updates": 1000,
        "top1": accuracy,
        "initialization_sha256": initialization_sha256,
        "scientific_use_allowed": False,
        "input_dimension": config.input_dimension,
        "embedding_dimension": config.embedding_dimension,
    }
