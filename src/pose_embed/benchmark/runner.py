"""Development-first, paired MotionBERT experiments with immutable evidence."""

from __future__ import annotations

import copy
import json
import math
import random
import shlex
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.descriptors import (
    descriptor_summary,
    encode_retrieval,
    make_score_rows,
)
from pose_embed.benchmark.losses import build_loss, supports
from pose_embed.benchmark.model import MotionRetrievalModel, head_recipe
from pose_embed.benchmark.retrieval import evaluate_retrieval, method_retrieval_policy
from pose_embed.benchmark.runtime import (
    REPOSITORY,
    artifact_path,
    artifact_root,
    code_digest,
    digest,
    now,
    publish_manifest,
    read_json,
    require_unopened,
    save_checkpoint,
    state_digest,
    verify_run,
)
from pose_embed.benchmark.segments import (
    StopAtBoundary,
    begin_segment,
    capture_rng,
    load_continuation,
    optimizer_layout,
    restore_module,
    restore_optimizer,
    restore_rng,
    seal_segment,
    verify_chain,
    verify_environment,
)
from pose_embed.benchmark.training import (
    advance_optimizer,
    build_optimizer,
    phase_for_step,
    resolve_recipe,
    set_step_learning_rates,
)
from pose_embed.data.motionbert import preprocess_annotation
from pose_embed.models.motionbert import (
    configure_deterministic_inference,
    inference_environment,
    load_frozen_encoder,
    verify_motionbert_assets,
)
from pose_embed.motionbert_inputs import (
    build_motionbert_bindings,
    load_motionbert_inputs,
)
from pose_embed.motionbert_parity import validate_parity_report
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file, write_immutable_json
from pose_embed.training.sampler import BalancedBatchSampler


class PoseDataset(Dataset):
    """Stream verified annotations through the shared deterministic preprocessing."""

    def __init__(self, records, annotations, protocol) -> None:
        self.records = list(records)
        self.annotations = annotations
        self.protocol = protocol
        mapping = {
            label: index
            for index, label in enumerate(sorted({r.ntu.action for r in records}))
        }
        self.label_mapping = mapping
        self.labels = [mapping[r.ntu.action] for r in records]

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        annotation = self.annotations[self.records[index].sample_id]
        return torch.from_numpy(
            preprocess_annotation(annotation, self.protocol)
        ), self.labels[index]


def encode(model, dataset, device, batch_size: int) -> np.ndarray:
    return encode_retrieval(model, dataset, device, batch_size)["embeddings"]


def optimizer_step(
    model, criterion, optimizer, poses, labels, gradient_clip_value=None
) -> float:
    optimizer.zero_grad(set_to_none=True)
    if getattr(criterion, "requires_feature_training", False):
        value = criterion.training_loss(model, poses, labels)
    else:
        embedded = (
            model.forward_raw(poses)
            if getattr(criterion, "requires_raw_embeddings", False)
            else model(poses)
        )
        value = criterion(embedded, labels)
    if value.ndim != 0 or not torch.isfinite(value):
        raise ValueError("objective must produce a finite scalar")
    value.backward()
    if hasattr(criterion, "after_backward"):
        criterion.after_backward(model)
    parameters = [*model.parameters(), *criterion.parameters()]
    if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in parameters):
        raise ValueError("training produced non-finite gradients")
    if hasattr(criterion, "clip_gradients"):
        criterion.clip_gradients(model)
    if gradient_clip_value is not None:
        torch.nn.utils.clip_grad_value_(model.parameters(), gradient_clip_value)
    optimizer.step()
    if any(not torch.isfinite(p).all() for p in parameters):
        raise ValueError("training produced non-finite parameters")
    if hasattr(criterion, "after_optimizer_step"):
        criterion.after_optimizer_step(model)
    return float(value.detach().cpu())


def _cpu_snapshot(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: _cpu_snapshot(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_cpu_snapshot(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_cpu_snapshot(item) for item in value)
    return copy.deepcopy(value)


def _checkpoint_state(model, criterion, optimizer, recipe, step, phase):
    state = {
        "model": _cpu_snapshot(model.state_dict()),
        "criterion": _cpu_snapshot(criterion.state_dict()),
    }
    if optimizer is not None:
        profiling = recipe["profile_phase"] is not None
        state["optimizer"] = _cpu_snapshot(optimizer.state_dict())
        state["training_state"] = {
            "phase": phase,
            "step": step,
            "warmup_updates": 0 if profiling else min(step, recipe["warmup_steps"]),
            "main_updates": step
            if profiling
            else max(0, step - recipe["warmup_steps"]),
            "encoder_trainable": model.train_encoder,
        }
    return state


def run_experiment(
    *,
    config_path: str | Path,
    manifest_set_path: str | Path,
    parity_evidence_path: str | Path,
    output_dir: str | Path,
    method: str,
    seed: int,
    track: str | None = None,
    device: str = "cuda",
    stage: str = "development",
    profile_steps: int | None = None,
    resume_from: str | Path | None = None,
    segment_steps: int | None = None,
    max_segment_seconds: float | None = None,
) -> dict[str, Any]:
    """Run one declared method/seed. Profiling can never certify a final run."""
    attempt_started = time.perf_counter()
    require_unopened()
    segmented = any(
        value is not None for value in (resume_from, segment_steps, max_segment_seconds)
    )
    if segmented and profile_steps is not None:
        raise ValueError("capacity profiles cannot be segmented or resumed")
    if segment_steps is not None and (
        type(segment_steps) is not int or segment_steps < 1
    ):
        raise ValueError("segment_steps must be a positive integer")
    if max_segment_seconds is not None and (
        not math.isfinite(max_segment_seconds) or max_segment_seconds <= 0
    ):
        raise ValueError("max_segment_seconds must be positive and finite")
    config = load_benchmark(config_path)
    track = track or config.training.encoder_mode
    if track != config.training.encoder_mode:
        raise ValueError(
            "track must match the hash-bound encoder_mode in the configuration"
        )
    methods = load_methods()
    if (
        method not in config.final_methods
        or method not in methods
        or not supports(method)
    ):
        raise ValueError(f"method is not implemented and authorized: {method}")
    if seed not in config.training.seeds or track not in {"frozen", "finetune"}:
        raise ValueError("seed/track is outside the declared benchmark")
    if stage not in {"development", "final"}:
        raise ValueError("stage must be development or final")
    if profile_steps is not None and (
        not 1 <= profile_steps <= 100 or stage != "development"
    ):
        raise ValueError("profiling requires 1–100 development steps")
    if stage == "final":
        from pose_embed.benchmark.locks import validate_selection

        selection = validate_selection(config_path=config_path)
        if method not in selection.get("methods", {}) or track != "finetune":
            raise ValueError("final method/track was not selected")
    configure_deterministic_inference()
    protocol_path = REPOSITORY / config.input_protocol
    inputs = load_motionbert_inputs(protocol_path, manifest_set_path)
    if protocol_digest(inputs.protocol) != config.input_protocol_sha256:
        raise ValueError(
            "v2 input contract differs from the adopted v1 source contract"
        )
    assets = verify_motionbert_assets(inputs.data_root)
    bindings = build_motionbert_bindings(inputs, assets)
    validate_parity_report(parity_evidence_path, bindings)
    spec = methods[method]
    steps = profile_steps or (
        selection["methods"][method]["selected_steps"]
        if stage == "final"
        else config.training.steps
    )
    train_rows = inputs.manifests[
        "final-train.jsonl" if stage == "final" else "development-train.jsonl"
    ]
    selection_num_records = (
        len(inputs.manifests["final-train.jsonl"])
        if method in {"proxy_nca_pp", "proxy_nca_metrix", "hist", "proxy_anchor_avsl"}
        and stage == "development"
        else len(train_rows)
    )
    recipe = resolve_recipe(
        method,
        spec.parameters,
        config.training,
        len(train_rows),
        selection_num_records=selection_num_records,
        profile=profile_steps is not None,
    )
    if profile_steps is None and steps < recipe["minimum_selected_step"]:
        raise ValueError(
            "scientific step budget must exceed the complete declared warmup "
            "for both development and final training; use a declared longer budget"
        )
    identity = {
        "benchmark_sha256": benchmark_digest(config),
        "configuration": config.model_dump(mode="json"),
        "method": method,
        "method_specification": spec.model_dump(mode="json"),
        "seed": seed,
        "track": track,
        "stage": "profile" if profile_steps is not None else stage,
        "steps": steps,
        "code_sha256": code_digest(),
        "inputs": bindings,
        "input_paths": {
            "manifest_set": str(Path(manifest_set_path).resolve()),
            "parity_evidence": str(Path(parity_evidence_path).resolve()),
            "protocol": str(protocol_path.resolve()),
            "configuration": str(Path(config_path).resolve()),
        },
        "parity_sha256": sha256_file(parity_evidence_path),
        "selection_sha256": sha256_file(artifact_root() / "locks/selection.json")
        if stage == "final"
        else None,
        "optimizer": recipe["optimizer"],
        "training_recipe": recipe,
        "head_recipe": head_recipe(method),
        "precision": "float32",
        "scientific_use_allowed": profile_steps is None,
    }
    destination = artifact_path(output_dir)
    parent = None
    continuation = None
    prior_best = None
    segment = None
    stop = StopAtBoundary()
    if resume_from is None:
        destination.mkdir(parents=True, exist_ok=False)
        write_immutable_json(
            destination / "attempt.json", {"identity": identity, "started_at": now()}
        )
    else:
        if read_json(destination / "attempt.json").get("identity") != identity:
            raise ValueError(
                "resume requires the identical code, inputs and experiment identity"
            )
        parent = verify_chain(destination, resume_from, identity)
        verify_environment(
            parent["manifest"]["telemetry"]["environment"],
            inference_environment(device)
            | {"batch_size": config.training.physical_batch_size},
        )
        continuation, prior_best = load_continuation(destination, parent, identity)
    if segmented:
        segment = begin_segment(destination, identity, parent)
        stop.__enter__()
    try:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        encoder, _ = load_frozen_encoder(inputs.data_root, device)
        model = MotionRetrievalModel(
            encoder,
            embedding_dimension=spec.embedding_dimension,
            train_encoder=track == "finetune",
            method_id=method,
            method_parameters=spec.parameters,
        ).to(device)
        annotations = {a["frame_dir"]: a for a in inputs.annotations}
        dataset = PoseDataset(train_rows, annotations, inputs.protocol)
        criterion = build_loss(
            method,
            spec.parameters | {"embedding_dimension": spec.embedding_dimension},
            len(set(dataset.labels)),
        ).to(device)
        if method == "s2sd":
            criterion.completed_steps.fill_(recipe["profile_counter_offset"])
        phase = phase_for_step(recipe, 1)
        optimizer = build_optimizer(model, criterion, recipe, phase)
        initial = {
            "model": state_digest(model),
            "encoder": state_digest(model.encoder),
            "head": state_digest(model.head),
            "criterion": state_digest(criterion),
        }
        if continuation is None:
            write_immutable_json(destination / "initialization.json", initial)
        elif read_json(destination / "initialization.json") != initial:
            raise ValueError(
                "continuation fresh initialization differs from the original"
            )
        # A proxy's random initialization must not shift the shared model RNG stream.
        torch.manual_seed(seed)
        batches = list(
            BalancedBatchSampler(
                dataset.labels,
                classes_per_batch=config.training.classes_per_batch,
                samples_per_class=config.training.samples_per_class,
                seed=seed,
                batches_per_epoch=steps,
            )
        )
        batch_plan = {
            "sample_ids": [r.sample_id for r in train_rows],
            "label_mapping": {
                str(key): value for key, value in dataset.label_mapping.items()
            },
            "steps": batches,
        }
        if continuation is None:
            write_immutable_json(destination / "batch-plan.json", batch_plan)
        elif digest(read_json(destination / "batch-plan.json")) != digest(batch_plan):
            raise ValueError(
                "continuation batch plan differs from the original experiment"
            )
        memory_bootstrap_seconds = 0.0
        memory_bootstrap_peak_allocated_bytes = 0
        if method == "diva" and continuation is None:
            criterion.configure_training(train_rows, dataset.labels, stage)
            memory_batches = list(
                BalancedBatchSampler(
                    dataset.labels,
                    classes_per_batch=config.training.classes_per_batch,
                    samples_per_class=config.training.samples_per_class,
                    seed=seed,
                    batches_per_epoch=recipe["queue_batches"],
                )
            )
            write_immutable_json(
                destination / "memory-plan.json",
                {
                    "schema_version": 1,
                    "policy": recipe["memory_bootstrap"],
                    "partition": "final_train"
                    if stage == "final"
                    else "development_train",
                    "batch_plan_sha256": sha256_file(destination / "batch-plan.json"),
                    "steps": memory_batches,
                },
            )
            memory_started = time.perf_counter()
            for indices, (poses, _) in zip(
                memory_batches,
                DataLoader(
                    dataset,
                    batch_sampler=memory_batches,
                    generator=torch.Generator().manual_seed(seed),
                ),
                strict=True,
            ):
                criterion.bootstrap(model, poses.to(device), indices)
            if torch.device(device).type == "cuda":
                torch.cuda.synchronize(device)
            memory_bootstrap_seconds = time.perf_counter() - memory_started
            memory_bootstrap_peak_allocated_bytes = (
                torch.cuda.max_memory_allocated(device)
                if torch.device(device).type == "cuda"
                else 0
            )
            write_immutable_json(
                destination / "memory-initialization.json",
                {
                    "criterion_sha256": state_digest(criterion),
                    "memory_plan_sha256": sha256_file(destination / "memory-plan.json"),
                    "completed_steps": 0,
                    "queue_count": criterion.config.queue_size,
                    "momentum_updates": 0,
                },
            )
        validation_rows = inputs.manifests["development-validation.jsonl"]
        validation = PoseDataset(validation_rows, annotations, inputs.protocol)
        batch_size = (
            config.training.classes_per_batch * config.training.samples_per_class
        )
        completed_steps = continuation["step"] if continuation else 0
        loader = iter(DataLoader(dataset, batch_sampler=batches[completed_steps:]))
        best_score = -1.0
        best_state = None
        best_result = None
        selected_step = steps
        history = list(parent["rows"]) if parent else []
        if continuation:
            restore_module(model, continuation["model"])
            restore_module(criterion, continuation["criterion"])
            if hasattr(criterion, "configure_training"):
                criterion.configure_training(train_rows, dataset.labels, stage)
            if method == "diva":
                memory_bootstrap_seconds = continuation["bootstrap_telemetry"][
                    "seconds"
                ]
                memory_bootstrap_peak_allocated_bytes = continuation[
                    "bootstrap_telemetry"
                ]["peak_allocated_bytes"]
            phase = phase_for_step(recipe, completed_steps)
            optimizer = build_optimizer(model, criterion, recipe, phase)
            set_step_learning_rates(optimizer, recipe, completed_steps)
            restore_optimizer(
                model,
                criterion,
                optimizer,
                continuation["optimizer"],
                continuation["optimizer_layout"],
            )
            if hasattr(criterion, "validate_checkpoint_state"):
                criterion.validate_checkpoint_state(
                    continuation["criterion"], completed_steps
                )
            if prior_best:
                best_state = {
                    key: value
                    for key, value in prior_best.items()
                    if key not in {"identity", "selected_step", "result"}
                }
                selected_step = prior_best["selected_step"]
                best_result = prior_best["result"]
                best_score = parent["manifest"]["best"]["score"]
            # DataLoader iterator creation consumes a Torch base seed. Restore after it.
            restore_rng(continuation["rng"])
            del continuation, prior_best
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        started = time.perf_counter()
        model.train()
        criterion.train()
        for step, (poses, labels) in enumerate(loader, start=completed_steps + 1):
            requested_phase = phase_for_step(recipe, step)
            if requested_phase != phase:
                phase = requested_phase
                optimizer = advance_optimizer(
                    model, criterion, optimizer, recipe, phase
                )
            set_step_learning_rates(optimizer, recipe, step)
            step_started = time.perf_counter()
            if hasattr(criterion, "set_training_batch"):
                criterion.set_training_batch(batches[step - 1])
            value = optimizer_step(
                model,
                criterion,
                optimizer,
                poses.to(device),
                labels.to(device),
                recipe.get("model_gradient_clip_value"),
            )
            if torch.device(device).type == "cuda":
                torch.cuda.synchronize(device)
            row = {
                "step": step,
                "loss": value,
                "seconds": time.perf_counter() - step_started,
                "phase": phase,
                "encoder_gradient_parameters": sum(
                    p.grad is not None for p in model.encoder.parameters()
                ),
            }
            if method == "drml":
                row["drml_assignment_counts"] = list(criterion.assignment_counts)
            if (
                stage == "development"
                and profile_steps is None
                and (step % config.training.validation_every == 0 or step == steps)
            ):
                encoding_started = time.perf_counter()
                descriptors = encode_retrieval(model, validation, device, batch_size)
                encoding_seconds = time.perf_counter() - encoding_started
                scoring_started = time.perf_counter()
                embedded = descriptors["embeddings"]
                result = evaluate_retrieval(
                    embedded,
                    embedded,
                    validation_rows,
                    validation_rows,
                    recall_k=config.metrics.recall_k,
                    score_rows=make_score_rows(model, descriptors, descriptors),
                    scoring_policy=method_retrieval_policy(method, spec.parameters),
                )
                row["validation"] = result["metrics"]
                row["descriptor_storage"] = descriptor_summary(descriptors)
                row["retrieval_timing"] = {
                    "encoding_seconds": encoding_seconds,
                    "scoring_seconds": time.perf_counter() - scoring_started,
                }
                score = result["metrics"][config.selection_metric]
                if step >= recipe["minimum_selected_step"] and score > best_score:
                    best_score = score
                    selected_step = step
                    best_result = result
                    best_state = _checkpoint_state(
                        model, criterion, optimizer, recipe, step, phase
                    )
                print(
                    json.dumps(
                        {
                            "event": "development_validation",
                            "method": method,
                            "seed": seed,
                            "step": step,
                            "planned_steps": steps,
                            "r_at_1": score,
                            "selected_step": selected_step
                            if best_state is not None
                            else None,
                            "attempt_elapsed_seconds": time.perf_counter()
                            - attempt_started,
                        }
                    ),
                    file=sys.stderr,
                    flush=True,
                )
            history.append(row)
            if segmented and step < steps:
                elapsed_now = time.perf_counter() - attempt_started
                if (
                    stop.reason
                    or (
                        segment_steps is not None
                        and step - completed_steps >= segment_steps
                    )
                    or (
                        max_segment_seconds is not None
                        and elapsed_now >= max_segment_seconds
                    )
                ):
                    break
        elapsed = time.perf_counter() - started
        if best_state is None and step == steps:
            best_state = _checkpoint_state(
                model, criterion, optimizer, recipe, steps, phase
            )
        environment = inference_environment(device) | {"batch_size": batch_size}
        peak_allocated = (
            torch.cuda.max_memory_allocated(device)
            if torch.device(device).type == "cuda"
            else 0
        )
        peak_reserved = (
            torch.cuda.max_memory_reserved(device)
            if torch.device(device).type == "cuda"
            else 0
        )
        if segmented:
            if any(
                getattr(criterion, name, None) is not None
                for name in ("_pending", "_batch_indices")
            ):
                raise ValueError(
                    "criterion has an unfinished update at the continuation boundary"
                )
            latest = _checkpoint_state(model, criterion, optimizer, recipe, step, phase)
            latest.update(
                {
                    "step": step,
                    "rng": capture_rng(),
                    "optimizer_layout": optimizer_layout(model, criterion, optimizer),
                }
            )
            if method == "diva":
                latest["bootstrap_telemetry"] = {
                    "seconds": memory_bootstrap_seconds,
                    "peak_allocated_bytes": memory_bootstrap_peak_allocated_bytes,
                }
            seal_segment(
                destination,
                segment,
                identity,
                parent,
                latest,
                best_state,
                best_result,
                selected_step,
                best_score,
                history,
                batches,
                time.perf_counter() - attempt_started,
                environment,
                peak_allocated,
                peak_reserved,
                stop.reason or ("completed" if step == steps else "segment_limit"),
            )
            chain = verify_chain(destination, segment, identity)
            elapsed = chain["elapsed_seconds"]
            peak_allocated = chain["peak_allocated_bytes"]
            peak_reserved = chain["peak_reserved_bytes"]
            if step < steps:
                arguments = [
                    "uv",
                    "run",
                    "pose-embed",
                    "benchmark",
                    "train",
                    "--config",
                    str(
                        Path(
                            identity.get("campaign_base_config_path", config_path)
                        ).resolve()
                    ),
                    "--manifest-set",
                    str(Path(manifest_set_path).resolve()),
                    "--parity-evidence",
                    str(Path(parity_evidence_path).resolve()),
                    "--method",
                    method,
                    "--seed",
                    str(seed),
                    "--output-dir",
                    str(destination),
                    "--device",
                    device,
                    "--phase",
                    stage,
                    "--resume-from",
                    str(segment / "segment-manifest.json"),
                ]
                if segment_steps is not None:
                    arguments.extend(["--segment-steps", str(segment_steps)])
                if max_segment_seconds is not None:
                    arguments.extend(
                        ["--max-segment-seconds", str(max_segment_seconds)]
                    )
                if "secondary" in identity:
                    arguments.extend(
                        ["--secondary-cell", identity["secondary"]["cell_id"]]
                    )
                if stage == "development" and identity.get("candidate") is not None:
                    arguments.extend(["--candidate", identity["candidate"]])
                return {
                    "status": "resumable",
                    "scientific_use_allowed": False,
                    "completed_steps": step,
                    "planned_steps": steps,
                    "segment_manifest": str(segment / "segment-manifest.json"),
                    "segment_manifest_sha256": sha256_file(
                        segment / "segment-manifest.json"
                    ),
                    "next_resume_command": shlex.join(arguments),
                    "retained_artifact_bytes": sum(
                        path.stat().st_size
                        for path in destination.rglob("*")
                        if path.is_file()
                    ),
                    "checkpoint_bytes": (segment / "checkpoint.pt").stat().st_size,
                    "storage_scenario": {
                        "planned_segments": math.ceil(steps / segment_steps),
                        "checkpoint_archive_bytes": (
                            2 * math.ceil(steps / segment_steps) + 1
                        )
                        * (segment / "checkpoint.pt").stat().st_size,
                        "assumption": (
                            "unchanged segment step limit and checkpoint size; "
                            "excludes history/descriptor overhead"
                        ),
                    }
                    if segment_steps
                    else None,
                }
            write_immutable_json(
                destination / "segments.json",
                {
                    "schema_version": 1,
                    "leaf": str(
                        (segment / "segment-manifest.json").relative_to(destination)
                    ),
                    "leaf_sha256": sha256_file(segment / "segment-manifest.json"),
                    "chain": chain["chain"],
                },
            )
        save_checkpoint(
            destination / "checkpoint.pt",
            {"identity": identity, "selected_step": selected_step, **best_state},
        )
        write_immutable_json(
            destination / "history.json",
            {
                "steps": history,
                "selected_step": selected_step,
                "elapsed_seconds": elapsed,
            },
        )
        output_names = [
            "attempt.json",
            "outcome.json",
            "checkpoint.pt",
            "history.json",
            "batch-plan.json",
            "initialization.json",
            "telemetry.json",
        ]
        if segmented:
            output_names.append("segments.json")
        if method == "diva":
            output_names.extend(["memory-plan.json", "memory-initialization.json"])
        if best_result is not None:
            write_immutable_json(
                destination / "development-result.json",
                {"identity": identity, "selected_step": selected_step, **best_result},
            )
            output_names.append("development-result.json")
        if method == "diva":
            output_names.extend(["memory-plan.json", "memory-initialization.json"])
        telemetry = {
            "elapsed_seconds": elapsed,
            "environment": environment,
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "checkpoint_bytes": (destination / "checkpoint.pt").stat().st_size,
            "training_steps": steps,
            "trainable_parameters": sum(
                p.numel()
                for p in [*model.parameters(), *criterion.parameters()]
                if p.requires_grad
            ),
            "profile_phase": recipe["profile_phase"],
            "encoder_backward_steps": sum(
                row["encoder_gradient_parameters"] > 0 for row in history
            ),
            "segment_artifact_bytes": sum(
                path.stat().st_size
                for path in (destination / "segments").rglob("*")
                if path.is_file()
            )
            if segmented
            else 0,
        }
        if method == "diva":
            telemetry.update(
                memory_bootstrap_seconds=memory_bootstrap_seconds,
                memory_bootstrap_peak_allocated_bytes=memory_bootstrap_peak_allocated_bytes,
                memory_items=criterion.config.queue_size,
                momentum_parameters=sum(
                    p.numel() for p in model.momentum_encoder.parameters()
                )
                + sum(p.numel() for p in model.momentum_projection.parameters()),
            )
        write_immutable_json(destination / "telemetry.json", telemetry)
        write_immutable_json(
            destination / "outcome.json", {"status": "succeeded", "completed_at": now()}
        )
        return publish_manifest(destination, identity, output_names)
    except BaseException as exc:
        failure_dir = segment if segmented and segment is not None else destination
        if not (failure_dir / "outcome.json").exists():
            write_immutable_json(
                failure_dir / "outcome.json",
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "elapsed_seconds": time.perf_counter() - attempt_started,
                    "completed_at": now(),
                },
            )
        raise
    finally:
        if segmented:
            stop.__exit__()


def compare_development(run_dirs: list[str | Path], output: str | Path) -> dict:
    """Summarize complete paired development results without opening the novel set."""
    runs = {}
    config_hash = None
    pairing = {}
    heads = {}
    for directory in run_dirs:
        directory = artifact_path(directory)
        manifest = verify_run(directory)
        identity = manifest["identity"]
        if identity["stage"] != "development" or not identity["scientific_use_allowed"]:
            raise ValueError("comparison accepts completed development runs only")
        if config_hash is not None and identity["benchmark_sha256"] != config_hash:
            raise ValueError("comparison mixes benchmark configurations")
        config_hash = identity["benchmark_sha256"]
        key = (identity["method"], identity["seed"])
        if key in runs:
            raise ValueError("duplicate method/seed")
        result = read_json(directory / "development-result.json")
        initialization = read_json(directory / "initialization.json")
        pair = {
            "encoder": initialization["encoder"],
            "batch_plan": manifest["outputs"]["batch-plan.json"],
            "query_order": result["query_order_sha256"],
            "exclusions": result["exclusion_sha256"],
            "track": identity["track"],
            "inputs": identity["inputs"],
        }
        seed = identity["seed"]
        if seed in pairing and pairing[seed] != pair:
            raise ValueError(
                "paired initialization, batches or query conditions differ"
            )
        pairing[seed] = pair
        head_key = (
            seed,
            identity["method_specification"]["embedding_dimension"],
            head_recipe(identity["method"]),
        )
        if heads.setdefault(head_key, initialization["head"]) != initialization["head"]:
            raise ValueError("paired initialization differs within a head recipe")
        runs[key] = {
            "method": key[0],
            "seed": key[1],
            "metrics": result["metrics"],
            "run_manifest_sha256": sha256_file(directory / "run-manifest.json"),
            "path": str(directory),
        }
    if not runs:
        raise ValueError("no runs supplied")
    methods = sorted({key[0] for key in runs})
    seeds = sorted({key[1] for key in runs})
    if set(runs) != {(m, s) for m in methods for s in seeds}:
        raise ValueError("development matrix is incomplete")
    pairs = []
    if {"contextual", "contrastive"}.issubset(methods):
        pairs = [
            {
                "seed": s,
                "contextual_minus_contrastive_r_at_1": runs[("contextual", s)][
                    "metrics"
                ]["r_at_1"]
                - runs[("contrastive", s)]["metrics"]["r_at_1"],
            }
            for s in seeds
        ]
    payload = {
        "schema_version": 2,
        "stage": "development",
        "benchmark_sha256": config_hash,
        "methods": methods,
        "seeds": seeds,
        "runs": list(runs.values()),
        "paired_effects": pairs,
        "interpretation": (
            "Development comparison; no novel-test result or superiority claim."
        ),
    }
    payload["content_sha256"] = digest(payload)
    write_immutable_json(artifact_path(output), payload)
    return payload
