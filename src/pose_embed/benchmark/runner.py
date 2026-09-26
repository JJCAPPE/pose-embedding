"""Development-first, paired MotionBERT experiments with immutable evidence."""

from __future__ import annotations

import copy
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.losses import build_loss, supports
from pose_embed.benchmark.model import MotionRetrievalModel, head_recipe
from pose_embed.benchmark.retrieval import evaluate_retrieval
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
    was_training = model.training
    model.eval()
    chunks = []
    try:
        with torch.inference_mode():
            for poses, _ in DataLoader(dataset, batch_size=batch_size, shuffle=False):
                embedded = model(poses.to(device))
                if not torch.isfinite(embedded).all():
                    raise ValueError("model produced non-finite retrieval embeddings")
                chunks.append(embedded.cpu().numpy())
    finally:
        model.train(was_training)
    return np.concatenate(chunks)


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
    parameters = [*model.parameters(), *criterion.parameters()]
    if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in parameters):
        raise ValueError("training produced non-finite gradients")
    if gradient_clip_value is not None:
        torch.nn.utils.clip_grad_value_(model.parameters(), gradient_clip_value)
    optimizer.step()
    if any(not torch.isfinite(p).all() for p in parameters):
        raise ValueError("training produced non-finite parameters")
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
    if recipe["optimizer"] == "Adam":
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
) -> dict[str, Any]:
    """Run one declared method/seed. Profiling can never certify a final run."""
    require_unopened()
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
        if method in {"proxy_nca_pp", "proxy_nca_metrix", "hist"}
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
    destination.mkdir(parents=True, exist_ok=False)
    write_immutable_json(
        destination / "attempt.json", {"identity": identity, "started_at": now()}
    )
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
        ).to(device)
        annotations = {a["frame_dir"]: a for a in inputs.annotations}
        dataset = PoseDataset(train_rows, annotations, inputs.protocol)
        criterion = build_loss(
            method,
            spec.parameters | {"embedding_dimension": spec.embedding_dimension},
            len(set(dataset.labels)),
        ).to(device)
        phase = phase_for_step(recipe, 1)
        optimizer = build_optimizer(model, criterion, recipe, phase)
        initial = {
            "model": state_digest(model),
            "encoder": state_digest(model.encoder),
            "head": state_digest(model.head),
            "criterion": state_digest(criterion),
        }
        write_immutable_json(destination / "initialization.json", initial)
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
        write_immutable_json(
            destination / "batch-plan.json",
            {
                "sample_ids": [r.sample_id for r in train_rows],
                "label_mapping": dataset.label_mapping,
                "steps": batches,
            },
        )
        validation_rows = inputs.manifests["development-validation.jsonl"]
        validation = PoseDataset(validation_rows, annotations, inputs.protocol)
        batch_size = (
            config.training.classes_per_batch * config.training.samples_per_class
        )
        loader = DataLoader(dataset, batch_sampler=batches)
        best_score = -1.0
        best_state = None
        best_result = None
        selected_step = steps
        history = []
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        started = time.perf_counter()
        model.train()
        criterion.train()
        for step, (poses, labels) in enumerate(loader, start=1):
            requested_phase = phase_for_step(recipe, step)
            if requested_phase != phase:
                phase = requested_phase
                optimizer = advance_optimizer(
                    model, criterion, optimizer, recipe, phase
                )
            set_step_learning_rates(optimizer, recipe, step)
            step_started = time.perf_counter()
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
            if (
                stage == "development"
                and profile_steps is None
                and (step % config.training.validation_every == 0 or step == steps)
            ):
                embedded = encode(model, validation, device, batch_size)
                result = evaluate_retrieval(
                    embedded,
                    embedded,
                    validation_rows,
                    validation_rows,
                    recall_k=config.metrics.recall_k,
                )
                row["validation"] = result["metrics"]
                score = result["metrics"][config.selection_metric]
                if step >= recipe["minimum_selected_step"] and score > best_score:
                    best_score = score
                    selected_step = step
                    best_result = result
                    best_state = _checkpoint_state(
                        model, criterion, optimizer, recipe, step, phase
                    )
            history.append(row)
        elapsed = time.perf_counter() - started
        if best_state is None:
            best_state = _checkpoint_state(
                model, criterion, optimizer, recipe, steps, phase
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
        if best_result is not None:
            write_immutable_json(
                destination / "development-result.json",
                {"identity": identity, "selected_step": selected_step, **best_result},
            )
            output_names.append("development-result.json")
        telemetry = {
            "elapsed_seconds": elapsed,
            "environment": inference_environment(device) | {"batch_size": batch_size},
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device)
            if torch.device(device).type == "cuda"
            else 0,
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device)
            if torch.device(device).type == "cuda"
            else 0,
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
        }
        write_immutable_json(destination / "telemetry.json", telemetry)
        write_immutable_json(
            destination / "outcome.json", {"status": "succeeded", "completed_at": now()}
        )
        return publish_manifest(destination, identity, output_names)
    except BaseException as exc:
        if not (destination / "outcome.json").exists():
            write_immutable_json(
                destination / "outcome.json",
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "completed_at": now(),
                },
            )
        raise


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
