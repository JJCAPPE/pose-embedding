"""Measure final-size residency with 80-action updates and no retained head."""

from __future__ import annotations

import argparse
import math
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as functional

from pose_embed.artifacts import validate_feature_artifact
from pose_embed.config import (
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.data.manifest import load_manifest
from pose_embed.dataset_seal import (
    canonical_artifact_root,
    dataset_access,
    require_dataset_unopened,
)
from pose_embed.models.motionbert import configure_deterministic_inference
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.protocol import protocol_digest
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import (
    capture_runtime_telemetry,
    require_path_within,
    reset_peak_memory,
    sha256_file,
    write_immutable_json,
)
from pose_embed.training.runner import (
    NormalizedLinearHead,
    _gradient_health,
    _json_digest,
    _require_projection_health,
    _require_v3_runtime,
    _state_dict_digest,
    build_loss,
)
from pose_embed.training.sampler import BalancedBatchSampler


def eligible_indices(sample_ids, development_ids, excluded_actions):
    """Map the locked development order into the resident full auxiliary matrix."""
    if len(set(sample_ids)) != len(sample_ids) or len(set(development_ids)) != len(
        development_ids
    ):
        raise ValueError("timing identities contain duplicates")
    lookup = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    if not set(development_ids) <= set(lookup):
        raise ValueError("development rows must be a subset of the final cache")
    if any(int(sample_id[-3:]) in excluded_actions for sample_id in development_ids):
        raise ValueError("timing updates cannot use validation or novel actions")
    return [lookup[sample_id] for sample_id in development_ids]


def measure_method(config, features, labels, eligible, output):
    torch.manual_seed(config.seed)
    reset_peak_memory("cuda")
    head = NormalizedLinearHead(
        config.input_dimension, config.embedding_dimension
    ).cuda()
    initialized = _state_dict_digest(head)
    criterion = build_loss(config)
    optimizer = torch.optim.AdamW(
        head.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        betas=(0.9, 0.999),
        eps=1e-8,
        amsgrad=False,
        foreach=False,
        fused=False,
    )
    eligible_labels = labels[eligible].cpu().tolist()
    batches_per_epoch = math.ceil(
        len(features) / (config.classes_per_batch * config.samples_per_class)
    )
    updates = 0
    seconds = 0.0
    epoch_hashes = []
    for epoch in range(config.epochs):
        sampler = BalancedBatchSampler(
            eligible_labels,
            classes_per_batch=config.classes_per_batch,
            samples_per_class=config.samples_per_class,
            seed=config.seed + epoch,
            batches_per_epoch=batches_per_epoch,
        )
        batches = [[eligible[index] for index in batch] for batch in sampler]
        epoch_hashes.append(_json_digest(batches))
        write_immutable_json(
            output / f"batch-plan-{epoch + 1:03d}.json",
            {"epoch": epoch + 1, "batches": batches},
        )
        torch.cuda.synchronize()
        started = time.perf_counter()
        for indexes in batches:
            batch = torch.as_tensor(indexes, device="cuda")
            raw = head.projection(features[batch])
            _require_projection_health(raw)
            embeddings = functional.normalize(raw, dim=-1)
            value = criterion(embeddings, labels[batch])
            loss = value[0] if isinstance(value, tuple) else value
            if not torch.isfinite(loss):
                raise ValueError("timing loss is non-finite")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            _gradient_health(head)
            optimizer.step()
            if not all(
                torch.isfinite(parameter).all() for parameter in head.parameters()
            ):
                raise ValueError("timing parameters are non-finite")
            updates += 1
        torch.cuda.synchronize()
        seconds += time.perf_counter() - started
    return {
        "objective": config.objective,
        "seed": config.seed,
        "epochs": config.epochs,
        "updates": updates,
        "expected_updates": config.epochs * batches_per_epoch,
        "initialization_sha256": initialized,
        "epoch_batch_plan_sha256": epoch_hashes,
        "training_seconds": seconds,
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "checkpoint_retained": False,
        "selection_eligible": False,
        "final_training_eligible": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-config", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--manifest-set", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("JOB_ID", "").isdecimal():
        parser.error("scheduler allocation required")
    configure_deterministic_inference()
    started = datetime.now(UTC)
    with dataset_access():
        require_dataset_unopened(require_registry=True)
        require_clean_repository()
        protocol = load_protocol(args.protocol_config)
        if protocol.test_access.resolved_protocol_relative_path != (
            "study-v3/revisions/execution-r1/locks/protocol.v3.json"
        ):
            raise ValueError("timing requires the admitted execution-r1 successor")
        design = require_v3_design(protocol)
        _require_v3_runtime(protocol)
        root = canonical_artifact_root()
        revision = (
            root
            / Path(protocol.test_access.resolved_protocol_relative_path).parent.parent
        )
        output = require_path_within(args.output_dir, revision, label="resident timing")
        output.mkdir(parents=True, exist_ok=False)
        source = args.cache_dir / "final-train-first.npz"
        bundle = args.manifest_set.parent
        attempt = {
            "status": "started",
            "started_at": started.isoformat(),
            "protocol_sha256": protocol_digest(protocol),
            "script_sha256": sha256_file(__file__),
            "purpose": "resource_timing_only",
            "selection_eligible": False,
            "final_training_eligible": False,
            "inputs": {
                str(path): sha256_file(path)
                for path in (
                    args.protocol_config,
                    args.manifest_set,
                    source,
                    bundle / "final-train.jsonl",
                    bundle / "development-train.jsonl",
                )
            },
        }
        write_immutable_json(output / "attempt.json", attempt)
        try:
            tick = time.perf_counter()
            sidecar = validate_feature_artifact(
                source, protocol=protocol, manifest_path=bundle / "final-train.jsonl"
            )
            if (sidecar.shape, sidecar.role, sidecar.split) != (
                (95001, 8704),
                "training",
                "final_train",
            ):
                raise ValueError(
                    "resident timing requires the complete scientific final cache"
                )
            for name in ("final_train", "development_train"):
                if (
                    sha256_file(bundle / (name.replace("_", "-") + ".jsonl"))
                    != design.manifests[name].sha256
                ):
                    raise ValueError("timing manifest differs from design")
            validation_seconds = time.perf_counter() - tick
            tick = time.perf_counter()
            with np.load(source, allow_pickle=False) as archive:
                features = torch.from_numpy(archive["features"]).cuda()
                labels = torch.from_numpy(archive["labels"]).long().cuda()
                ids = archive["sample_ids"].tolist()
            torch.cuda.synchronize()
            if features.dtype != torch.float32:
                raise ValueError("resident timing requires the fixed float32 cache")
            loading_seconds = time.perf_counter() - tick
            development = load_manifest(bundle / "development-train.jsonl")
            eligible = eligible_indices(
                ids,
                [row.sample_id for row in development],
                set(protocol.dataset.novel_actions)
                | set(protocol.dataset.development_validation_actions),
            )
            if (
                len(eligible) != 76013
                or len({row.ntu.action for row in development}) != 80
            ):
                raise ValueError(
                    "timing update identity must be the complete 80-action training set"
                )
            records = []
            for method in ("contrastive", "contextual", "supcon"):
                config_path = Path(f"configs/experiments/v3/{method}-lr3e-4-seed7.yaml")
                config = load_experiment(config_path)
                validate_experiment_against_protocol(config, protocol)
                record = measure_method(
                    config, features, labels, eligible, output / method
                )
                record["config_sha256"] = sha256_file(config_path)
                write_immutable_json(output / method / "timing.json", record)
                records.append(record)
            if any(
                (r["initialization_sha256"], r["epoch_batch_plan_sha256"])
                != (
                    records[0]["initialization_sha256"],
                    records[0]["epoch_batch_plan_sha256"],
                )
                for r in records
            ):
                raise ValueError("timing arms are not paired")
            ended = datetime.now(UTC)
            write_immutable_json(
                output / "timing.json",
                {
                    "status": "passed",
                    "protocol_sha256": protocol_digest(protocol),
                    "attempt_sha256": sha256_file(output / "attempt.json"),
                    "full_size_resident_rows": len(features),
                    "timing_optimization_actions": 80,
                    "optimization_rows": len(eligible),
                    "methods": records,
                    "artifact_validation_seconds": validation_seconds,
                    "loading_seconds": loading_seconds,
                    "peak_host_bytes": capture_runtime_telemetry(
                        started_at=started, ended_at=ended
                    ).peak_memory_bytes,
                    "wall_time_seconds": (ended - started).total_seconds(),
                    "checkpoint_retained": False,
                },
            )
            write_immutable_json(
                output / "outcome.json",
                {
                    "status": "success",
                    "timing_sha256": sha256_file(output / "timing.json"),
                },
            )
        except BaseException as error:
            write_immutable_json(
                output / "outcome.json",
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                },
            )
            raise


if __name__ == "__main__":
    main()
