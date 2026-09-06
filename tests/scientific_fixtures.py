from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
import yaml

from pose_embed.artifacts import (
    FeatureSidecar,
    preprocessing_digest,
    sample_order_digest,
)
from pose_embed.config import ProtocolConfig, load_experiment
from pose_embed.data import ManifestRecord
from pose_embed.protocol import (
    EvaluationPlan,
    FinalRunSet,
    current_code_hashes,
    evaluation_plan_digest,
    experiment_hyperparameters_digest,
    final_run_set_digest,
    protocol_digest,
)
from pose_embed.provenance import sha256_file
from pose_embed.training.runner import (
    NormalizedLinearHead,
    _json_digest,
    _state_dict_digest,
)
from pose_embed.training.sampler import BalancedBatchSampler


def _final_training_ids() -> tuple[str, ...]:
    novel = set(range(1, 116, 6))
    return tuple(
        f"S001C{camera:03d}P{((action - 1) % 106) + 1:03d}"
        f"R{repetition:03d}A{action:03d}"
        for action in range(1, 121)
        if action not in novel
        for camera, repetition in ((1, 1), (1, 2), (2, 1), (2, 2))
    )


def locked_plan() -> EvaluationPlan:
    actions = tuple(range(1, 116, 6))
    anchors = (
        *(f"S001C003P008R001A{action:03d}" for action in actions[:10]),
        *(f"S018C003P008R001A{action:03d}" for action in actions[10:]),
    )
    official = tuple(f"S002C001P002R001A{action:03d}" for action in actions)
    source_ids = _final_training_ids() + anchors + official
    source_payload = (
        "\n".join(
            ManifestRecord(
                sample_id=sample_id,
                split=(
                    "final_train"
                    if int(sample_id[-3:]) not in actions
                    else "novel_anchor"
                    if sample_id in anchors
                    else "novel_query_official"
                ),
                is_anchor=sample_id in anchors,
            ).model_dump_json()
            for sample_id in source_ids
        )
        + "\n"
    )
    source_sha256 = hashlib.sha256(source_payload.encode("utf-8")).hexdigest()

    def binding(path: str, sample_ids: tuple[str, ...], character: str) -> dict:
        return {
            "relative_path": path,
            "sha256": source_sha256 if character == "source" else character * 64,
            "sample_count": len(sample_ids),
            "sample_ids": sample_ids,
        }

    return EvaluationPlan.model_validate(
        {
            "schema_version": 1,
            "status": "locked",
            "plan_id": "final-evaluation-v1",
            "methods": ["contrastive", "supcon", "contextual"],
            "seeds": [7, 17, 29],
            "conditions": [
                "clean",
                "coordinate_jitter:0.01",
                "coordinate_jitter:0.025",
                "coordinate_jitter:0.05",
                "joint_mask:3",
                "joint_mask:6",
                "joint_mask:8",
                "frame_mask:10",
                "frame_mask:25",
                "frame_mask:40",
            ],
            "query_definitions": ["primary", "official"],
            "metrics": ["top1", "mrr", "r_at_5"],
            "expected_rows": 180,
            "gallery_role": "gallery_clean",
            "gallery_split": "novel_anchor",
            "query_roles": ["query_clean", "query_corrupted"],
            "query_splits": ["novel_query_primary", "novel_query_official"],
            "source_inventory_manifest": binding(
                "manifests/source-inventory.jsonl", source_ids, "source"
            ),
            "anchor_manifest": binding("manifests/novel-anchor.jsonl", anchors, "b"),
            "official_query_manifest": binding(
                "manifests/novel-query-official.jsonl", official, "c"
            ),
            "primary_query_manifest": binding(
                "manifests/novel-query-primary.jsonl", official, "d"
            ),
        }
    )


def locked_run_set(protocol_sha256: str, plan: EvaluationPlan) -> FinalRunSet:
    selected = [
        {
            "method": method,
            "config_id": f"{method}-selected",
            "hyperparameters_sha256": character * 64,
        }
        for method, character in zip(plan.methods, "ef0", strict=True)
    ]
    runs = [
        {
            "method": method,
            "seed": seed,
            "config_relative_path": f"configs/{method}-{seed}.yaml",
            "config_sha256": f"{index + 7:x}" * 64,
            "run_manifest_relative_path": f"runs/{method}-{seed}/run-manifest.json",
            "run_manifest_sha256": f"{index + 1:x}" * 64,
            "checkpoint_relative_path": f"runs/{method}-{seed}/head.pt",
            "checkpoint_sha256": f"{index + 4:x}" * 64,
            "batch_plan_relative_path": f"runs/{method}-{seed}/batch-plan.json",
            "batch_plan_sha256": f"{seed % 10:x}" * 64,
            "metrics_relative_path": f"runs/{method}-{seed}/metrics.json",
            "metrics_sha256": "a" * 64,
            "attempt_relative_path": f"runs/{method}-{seed}/attempt.json",
            "attempt_sha256": "b" * 64,
            "outcome_relative_path": f"runs/{method}-{seed}/outcome.json",
            "outcome_sha256": "c" * 64,
            "initialization_sha256": f"{(seed + 1) % 10:x}" * 64,
        }
        for index, method in enumerate(plan.methods)
        for seed in plan.seeds
    ]
    return FinalRunSet.model_validate(
        {
            "schema_version": 1,
            "run_set_id": "final-core-run-set-v1",
            "protocol_sha256": protocol_sha256,
            "evaluation_plan_sha256": evaluation_plan_digest(plan),
            "selection_locked_at": "2026-08-31T12:00:00Z",
            "locked_at": "2026-09-01T00:00:00Z",
            "selected_configs": selected,
            "runs": runs,
            "code_sha256": {
                key: character * 64
                for key, character in zip(
                    [
                        "training",
                        "evaluation",
                        "sampler",
                        "corruptions",
                        "analysis",
                    ],
                    "abcde",
                    strict=True,
                )
            },
        }
    )


def materialize_final_run_set(
    root: Path,
    repository_root: Path,
    protocol: ProtocolConfig,
    plan: EvaluationPlan | None = None,
) -> FinalRunSet:
    """Create small but structurally real artifacts for all nine locked core runs."""
    active_plan = plan or locked_plan()
    payload = locked_run_set(protocol_digest(protocol), active_plan).model_dump(
        mode="json"
    )
    payload["code_sha256"] = current_code_hashes(repository_root).model_dump()
    assert active_plan.source_inventory_manifest is not None
    assert active_plan.anchor_manifest is not None
    training_ids = set(_final_training_ids())
    anchor_ids = set(active_plan.anchor_manifest.sample_ids)
    source_manifest_path = root / active_plan.source_inventory_manifest.relative_path
    source_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    source_records = [
        ManifestRecord(
            sample_id=sample_id,
            split=(
                "final_train"
                if sample_id in training_ids
                else "novel_anchor"
                if sample_id in anchor_ids
                else "novel_query_official"
            ),
            is_anchor=sample_id in anchor_ids,
        )
        for sample_id in active_plan.source_inventory_manifest.sample_ids
    ]
    source_manifest_path.write_text(
        "\n".join(record.model_dump_json() for record in source_records) + "\n",
        encoding="utf-8",
    )
    plan_path = root / protocol.test_access.evaluation_plan_relative_path
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    if not plan_path.exists():
        plan_path.write_text(active_plan.model_dump_json(), encoding="utf-8")
    selected_by_method = {item["method"]: item for item in payload["selected_configs"]}
    base_configs = {
        method: load_experiment(repository_root / f"configs/experiments/{method}.yaml")
        for method in active_plan.methods
    }
    for method, config in base_configs.items():
        selected_by_method[method]["hyperparameters_sha256"] = (
            experiment_hyperparameters_digest(config)
        )

    training_dir = root / "training-input"
    training_dir.mkdir(parents=True, exist_ok=True)
    source_path = training_dir / "features.npz"
    source_sidecar_path = source_path.with_suffix(".npz.manifest.json")
    training_manifest_path = training_dir / "final-train.jsonl"
    protocol_path = repository_root / "configs/protocol.v1.yaml"
    sample_ids = _final_training_ids()
    labels = np.asarray([int(sample_id[-3:]) for sample_id in sample_ids])
    features = np.zeros((len(sample_ids), 8704), dtype=np.float32)
    np.savez(source_path, features=features, labels=labels, sample_ids=sample_ids)
    training_manifest_path.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id,
                split="final_train",
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )
    created_at = datetime(2026, 8, 30, 12, tzinfo=UTC)
    source_sidecar = FeatureSidecar(
        schema_version=3,
        artifact_type="feature_cache",
        backend="motionbert",
        method="frozen_encoder_cache",
        training_seed=None,
        role="training",
        split="final_train",
        condition="clean",
        scientific_use_allowed=True,
        protocol_sha256=protocol_digest(protocol),
        manifest_sha256=sha256_file(training_manifest_path),
        sample_order_sha256=sample_order_digest(sample_ids),
        preprocessing_sha256=preprocessing_digest(protocol),
        upstream_sha256="d" * 64,
        encoder_checkpoint_sha256="e" * 64,
        artifact_sha256=sha256_file(source_path),
        array_key="features",
        shape=features.shape,
        dtype=str(features.dtype),
        sample_ids=sample_ids,
        created_at=created_at,
        provenance={"fixture": "scientific-contract-only"},
    )
    source_sidecar_path.write_text(source_sidecar.model_dump_json(), encoding="utf-8")
    dependency_lock_sha256 = sha256_file(repository_root / "uv.lock")
    environment = {
        "python": "3.11",
        "platform": "test",
        "torch": torch.__version__,
        "cuda_available": False,
        "cuda_version": None,
        "device_count": 0,
        "devices": [],
        "dependencies": {},
    }

    def provenance(
        command: str,
        configuration: dict[str, object],
        inputs: list[Path],
        *,
        ended_at: str,
    ) -> dict[str, object]:
        return {
            "schema_version": 1,
            "started_at": "2026-08-31T12:00:00+00:00",
            "ended_at": ended_at,
            "command": command,
            "git_sha": "0" * 40,
            "git_dirty": False,
            "dependency_lock_sha256": dependency_lock_sha256,
            "configuration": configuration,
            "inputs": {str(path): sha256_file(path) for path in inputs},
            "environment": environment,
        }

    for run in payload["runs"]:
        method = run["method"]
        seed = run["seed"]
        config = base_configs[method].model_copy(
            update={"name": f"{method}-final-{seed}", "seed": seed}
        )
        config_payload = config.model_dump(mode="json")
        config_path = root / run["config_relative_path"]
        checkpoint_path = root / run["checkpoint_relative_path"]
        batch_plan_path = root / run["batch_plan_relative_path"]
        run_manifest_path = root / run["run_manifest_relative_path"]
        metrics_path = root / run["metrics_relative_path"]
        attempt_path = root / run["attempt_relative_path"]
        outcome_path = root / run["outcome_relative_path"]
        for path in (
            config_path,
            checkpoint_path,
            batch_plan_path,
            run_manifest_path,
            metrics_path,
            attempt_path,
            outcome_path,
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8"
        )
        run["config_sha256"] = sha256_file(config_path)

        torch.manual_seed(seed)
        head = NormalizedLinearHead(config.input_dimension, config.embedding_dimension)
        run["initialization_sha256"] = _state_dict_digest(head)
        with torch.no_grad():
            head.projection.weight[0, 0] += 0.01
        torch.save(
            {"state_dict": head.state_dict(), "config": config_payload},
            checkpoint_path,
        )
        run["checkpoint_sha256"] = sha256_file(checkpoint_path)

        epochs = [
            [
                list(batch)
                for batch in BalancedBatchSampler(
                    labels.tolist(),
                    classes_per_batch=config.classes_per_batch,
                    samples_per_class=config.samples_per_class,
                    seed=seed + epoch,
                )
            ]
            for epoch in range(config.epochs)
        ]
        epoch_hashes = [_json_digest(epoch) for epoch in epochs]
        batch_payload = {
            "schema_version": 1,
            "seed": seed,
            "classes_per_batch": config.classes_per_batch,
            "samples_per_class": config.samples_per_class,
            "sample_order_sha256": source_sidecar.sample_order_sha256,
            "epoch_sha256": epoch_hashes,
            "epochs": epochs,
        }
        batch_plan_path.write_text(
            json.dumps(batch_payload, sort_keys=True), encoding="utf-8"
        )
        run["batch_plan_sha256"] = sha256_file(batch_plan_path)
        attempt_id = f"attempt-{method}-{seed}"
        training_inputs = [
            config_path,
            protocol_path,
            training_manifest_path,
            source_path,
            source_sidecar_path,
        ]
        attempt_payload = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "status": "started",
            "started_at": "2026-08-31T12:00:00+00:00",
            "objective": method,
            "seed": seed,
            "device": "cpu",
            "scientific_use_allowed": True,
            "protocol_sha256": protocol_digest(protocol),
            "config_sha256": run["config_sha256"],
            "input_artifact_sha256": source_sidecar.artifact_sha256,
            "feature_sidecar_sha256": sha256_file(source_sidecar_path),
            "manifest_sha256": source_sidecar.manifest_sha256,
            "canonical_test_opening_ledger": str(root / "locks/test-opening.v1.json"),
            "provenance": provenance(
                "train-attempt",
                {"experiment": config_payload, "device": "cpu"},
                training_inputs,
                ended_at="2026-08-31T12:00:01+00:00",
            ),
        }
        attempt_path.write_text(json.dumps(attempt_payload), encoding="utf-8")
        run["attempt_sha256"] = sha256_file(attempt_path)
        losses = [1.0 - (epoch / (2 * config.epochs)) for epoch in range(config.epochs)]
        telemetry = {
            "wall_time_seconds": 60.0,
            "peak_memory_bytes": 1_024,
            "peak_memory_source": "process_max_rss",
        }
        metrics_payload = {
            "objective": method,
            "seed": seed,
            "epochs": config.epochs,
            "epoch_losses": losses,
            "initial_loss": losses[0],
            "final_loss": losses[-1],
            "input_metadata": source_sidecar.model_dump(mode="json"),
            "initialization_sha256": run["initialization_sha256"],
            "batch_plan_sha256": run["batch_plan_sha256"],
            "epoch_batch_plan_sha256": epoch_hashes,
            "checkpoint_sha256": run["checkpoint_sha256"],
            "telemetry": telemetry,
        }
        metrics_path.write_text(json.dumps(metrics_payload), encoding="utf-8")
        run["metrics_sha256"] = sha256_file(metrics_path)
        manifest_payload = provenance(
            "train",
            {
                "experiment": config_payload,
                "device": "cpu",
                "attempt_sha256": run["attempt_sha256"],
            },
            training_inputs,
            ended_at="2026-08-31T12:01:00+00:00",
        )
        manifest_payload.update(
            {
                "scientific_use_allowed": True,
                "protocol_sha256": protocol_digest(protocol),
                "feature_sidecar": source_sidecar.model_dump(mode="json"),
                "initialization_sha256": run["initialization_sha256"],
                "batch_plan_sha256": run["batch_plan_sha256"],
                "epoch_batch_plan_sha256": epoch_hashes,
                "telemetry": telemetry,
                "outputs": {
                    "checkpoint": run["checkpoint_sha256"],
                    "metrics": run["metrics_sha256"],
                    "batch_plan": run["batch_plan_sha256"],
                },
            }
        )
        run_manifest_path.write_text(
            json.dumps(manifest_payload, sort_keys=True), encoding="utf-8"
        )
        run["run_manifest_sha256"] = sha256_file(run_manifest_path)
        outcome_payload = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "status": "success",
            "ended_at": "2026-08-31T12:02:00+00:00",
            "checkpoint_sha256": run["checkpoint_sha256"],
            "batch_plan_sha256": run["batch_plan_sha256"],
            "metrics_sha256": run["metrics_sha256"],
            "run_manifest_sha256": run["run_manifest_sha256"],
        }
        outcome_path.write_text(json.dumps(outcome_payload), encoding="utf-8")
        run["outcome_sha256"] = sha256_file(outcome_path)
    return FinalRunSet.model_validate(payload)


def write_lock_bundle(root: Path, protocol_sha256: str) -> tuple[Path, Path, Path]:
    locks = root / "locks"
    locks.mkdir(parents=True, exist_ok=True)
    plan = locked_plan()
    run_set = locked_run_set(protocol_sha256, plan)
    plan_path = locks / "evaluation-plan.v1.yaml"
    run_set_path = locks / "final-run-set.v1.json"
    lock_path = locks / "protocol-lock.v1.json"
    plan_path.write_text(json.dumps(plan.model_dump(mode="json")), encoding="utf-8")
    run_set_path.write_text(
        json.dumps(run_set.model_dump(mode="json")), encoding="utf-8"
    )
    assert plan.source_inventory_manifest is not None
    assert plan.anchor_manifest is not None
    assert plan.official_query_manifest is not None
    assert plan.primary_query_manifest is not None
    approved = datetime(2026, 9, 1, tzinfo=UTC)
    lock_path.write_text(
        json.dumps(
            {
                "protocol_id": "protocol-v1",
                "protocol_sha256": protocol_sha256,
                "evaluation_plan_sha256": evaluation_plan_digest(plan),
                "source_inventory_manifest_sha256": (
                    plan.source_inventory_manifest.sha256
                ),
                "anchor_manifest_sha256": plan.anchor_manifest.sha256,
                "official_query_manifest_sha256": (plan.official_query_manifest.sha256),
                "primary_query_manifest_sha256": (plan.primary_query_manifest.sha256),
                "final_run_set_sha256": final_run_set_digest(run_set),
                "advisor_approved_by": "Advisor",
                "advisor_approved_at": approved.isoformat(),
                "locked_at": approved.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return lock_path, plan_path, run_set_path
