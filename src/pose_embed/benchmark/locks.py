"""Complete, immutable selection and final-test authorization for benchmark v2."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch

from pose_embed.benchmark.analysis import analysis_plan_sha256, load_analysis_plan
from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.episodes import load_episode
from pose_embed.benchmark.losses import supports
from pose_embed.benchmark.runtime import (
    artifact_path,
    artifact_root,
    code_digest,
    digest,
    now,
    read_json,
    require_unopened,
    verify_run,
)
from pose_embed.provenance import sha256_file, write_immutable_json


def _path(name: str) -> Path:
    return artifact_path(artifact_root() / "locks" / name)


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("lock evidence requires a timestamp")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid lock evidence timestamp") from exc
    if (
        timestamp.tzinfo is None
        or timestamp.utcoffset() is None
        or timestamp > datetime.now(UTC)
    ):
        raise ValueError(
            "lock evidence timestamps require a timezone and cannot be future"
        )
    return timestamp


def _context(config_path):
    config = load_benchmark(config_path)
    load_analysis_plan(config)
    methods = load_methods()
    if config.training.encoder_mode != "finetune":
        raise ValueError("final selection requires the declared fine-tuning benchmark")
    unavailable = [
        method
        for method in config.final_methods
        if methods[method].status != "implemented" or not supports(method)
    ]
    if unavailable:
        raise ValueError(
            "complete final roster is not implemented: " + ", ".join(unavailable)
        )
    return config, methods


def _references(runs: dict) -> list[dict[str, Any]]:
    root = artifact_root()
    return [
        {
            "method": method,
            "seed": seed,
            "relative_path": str(directory.relative_to(root)),
            "run_manifest_sha256": sha256_file(directory / "run-manifest.json"),
            "checkpoint_sha256": manifest["outputs"]["checkpoint.pt"],
        }
        for (method, seed), (directory, manifest) in sorted(runs.items())
    ]


def _referenced_directories(references: Any) -> list[Path]:
    if not isinstance(references, list) or not references:
        raise ValueError("lock requires complete run references")
    directories = []
    for reference in references:
        relative = reference.get("relative_path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise ValueError("lock run path must stay relative to the canonical root")
        directory = artifact_path(artifact_root() / relative)
        if sha256_file(directory / "run-manifest.json") != reference.get(
            "run_manifest_sha256"
        ):
            raise ValueError("locked run manifest changed")
        directories.append(directory)
    return directories


def _collect_runs(
    run_dirs: Sequence[str | Path], config, methods, stage: str, selection=None
) -> dict:
    runs = {}
    config_hash = benchmark_digest(config)
    selection_hash = (
        sha256_file(_path("selection.json")) if selection is not None else None
    )
    selected_at = _timestamp(selection["created_at"]) if selection is not None else None
    pairs = {}
    common_inputs = None
    for value in run_dirs:
        directory = artifact_path(value)
        manifest = verify_run(directory)
        identity = manifest["identity"]
        key = (identity.get("method"), identity.get("seed"))
        if key in runs:
            raise ValueError("duplicate locked method/seed run")
        if key[0] not in config.final_methods or key[1] not in config.training.seeds:
            raise ValueError("run method/seed is outside the complete benchmark")
        if (
            identity.get("stage") != stage
            or identity.get("track") != "finetune"
            or identity.get("scientific_use_allowed") is not True
            or identity.get("benchmark_sha256") != config_hash
            or identity.get("configuration") != config.model_dump(mode="json")
            or identity.get("method_specification")
            != methods[key[0]].model_dump(mode="json")
        ):
            raise ValueError(
                "lock requires scientific fine-tuning runs of the exact "
                "declared stage/configuration"
            )
        started_at = _timestamp(read_json(directory / "attempt.json").get("started_at"))
        completed_at = _timestamp(manifest.get("completed_at"))
        if started_at > completed_at or (
            selected_at is not None and started_at < selected_at
        ):
            raise ValueError(
                "final training must start after selection "
                "and finish in timestamp order"
            )
        expected_steps = (
            config.training.steps
            if selection is None
            else selection["methods"][key[0]]["selected_steps"]
        )
        if (
            identity.get("steps") != expected_steps
            or identity.get("selection_sha256") != selection_hash
        ):
            raise ValueError(
                "run steps or selection binding differs "
                "from the locked development choice"
            )
        checkpoint = torch.load(
            directory / "checkpoint.pt", map_location="cpu", weights_only=True
        )
        if stage == "final" and checkpoint.get("selected_step") != expected_steps:
            raise ValueError("final checkpoint must be the selected training step")
        if "initialization.json" not in manifest["outputs"]:
            raise ValueError("paired initialization evidence is missing")
        initialization = read_json(directory / "initialization.json")
        batch = read_json(directory / "batch-plan.json")
        if len(batch.get("steps", [])) != expected_steps:
            raise ValueError("batch plan does not cover the declared training steps")
        pair = {
            "encoder": initialization.get("encoder"),
            "inputs": identity.get("inputs"),
            "sample_ids": batch.get("sample_ids"),
        }
        if not pair["encoder"] or not pair["inputs"] or not pair["sample_ids"]:
            raise ValueError("paired encoder/input/batch evidence is missing")
        if common_inputs is not None and common_inputs != pair["inputs"]:
            raise ValueError("all benchmark runs must bind the same input provenance")
        common_inputs = pair["inputs"]
        seed_pair = pairs.setdefault(
            key[1], {"common": pair, "heads": {}, "batches": []}
        )
        if seed_pair["common"] != pair:
            raise ValueError(
                "paired encoder, input provenance or sample identities differ"
            )
        from pose_embed.benchmark.model import head_recipe

        head_group = (methods[key[0]].embedding_dimension, head_recipe(key[0]))
        head = initialization.get("head")
        if not head or seed_pair["heads"].setdefault(head_group, head) != head:
            raise ValueError(
                "paired head initialization differs within a head recipe/dimension"
            )
        for other in seed_pair["batches"]:
            shared = min(len(other), len(batch["steps"]))
            if other[:shared] != batch["steps"][:shared]:
                raise ValueError("paired physical batch sequences differ")
        seed_pair["batches"].append(batch["steps"])
        runs[key] = (directory, manifest)
    expected = {
        (method, seed)
        for method in config.final_methods
        for seed in config.training.seeds
    }
    if set(runs) != expected:
        raise ValueError("complete 26-method by six-seed run matrix is required")
    return runs


def _selection_content(run_dirs, config, methods) -> tuple[dict, datetime]:
    runs = _collect_runs(run_dirs, config, methods, "development")
    selected = {}
    episode = None
    completed_at = max(
        _timestamp(manifest["completed_at"]) for _, manifest in runs.values()
    )
    for method in config.final_methods:
        histories = []
        minimum_selected_step = 1
        for seed in config.training.seeds:
            directory, manifest = runs[(method, seed)]
            if "development-result.json" not in manifest["outputs"]:
                raise ValueError(
                    "development selection requires bound retrieval evidence"
                )
            result = read_json(directory / "development-result.json")
            if result.get("identity") != manifest["identity"]:
                raise ValueError("development result identity differs from its run")
            condition = {
                key: result.get(key)
                for key in (
                    "query_order_sha256",
                    "gallery_order_sha256",
                    "exclusion_sha256",
                    "policy",
                )
            }
            if not all(condition.values()):
                raise ValueError(
                    "development retrieval identity and exclusions are missing"
                )
            if episode is not None and episode != condition:
                raise ValueError(
                    "development runs used different query/gallery "
                    "or exclusion policies"
                )
            episode = condition
            rows = read_json(directory / "history.json").get("steps", [])
            minimum_selected_step = max(
                minimum_selected_step,
                manifest["identity"]
                .get("training_recipe", {})
                .get("minimum_selected_step", 1),
            )
            scores = {}
            for row in rows:
                if "validation" not in row:
                    continue
                step = row.get("step")
                score = row["validation"].get(config.selection_metric)
                if (
                    isinstance(step, bool)
                    or not isinstance(step, int)
                    or step in scores
                    or not 1 <= step <= config.training.steps
                    or isinstance(score, bool)
                    or not isinstance(score, (int, float))
                    or not math.isfinite(score)
                    or not 0 <= score <= 1
                ):
                    raise ValueError(
                        "development history has invalid validation steps/scores"
                    )
                scores[step] = float(score)
            expected_steps = set(
                range(
                    config.training.validation_every,
                    config.training.steps + 1,
                    config.training.validation_every,
                )
            ) | {config.training.steps}
            if set(scores) != expected_steps:
                raise ValueError(
                    "development history must contain every scheduled validation"
                )
            histories.append(scores)
        means = {
            step: sum(history[step] for history in histories) / len(histories)
            for step in histories[0]
        }
        eligible = [step for step in means if step >= minimum_selected_step]
        if not eligible:
            raise ValueError(
                "selection requires a checkpoint after the full final warmup"
            )
        selected_step = max(eligible, key=lambda step: (means[step], -step))
        selected[method] = {
            "selected_steps": selected_step,
            "configuration_sha256": digest(config.model_dump(mode="json")),
            "method_specification_sha256": digest(
                methods[method].model_dump(mode="json")
            ),
            "embedding_dimension": methods[method].embedding_dimension,
            "mean_validation_r_at_1": means[selected_step],
            "validation_means": [
                {"step": step, "r_at_1": means[step]} for step in sorted(means)
            ],
        }
    return {
        "schema_version": 2,
        "kind": "final_selection",
        "analysis_plan_sha256": analysis_plan_sha256(),
        "benchmark_sha256": benchmark_digest(config),
        "code_sha256": code_digest(),
        "methods": selected,
        "seeds": list(config.training.seeds),
        "selection_rule": "maximum_mean_r_at_1_across_six_seeds_then_earliest_step",
        "development_episode": episode,
        "inputs": next(iter(runs.values()))[1]["identity"]["inputs"],
        "runs": _references(runs),
    }, completed_at


def create_selection(
    run_dirs: Sequence[str | Path], *, config_path: str | Path | None = None
) -> dict:
    """Lock all method choices from complete paired development evidence."""
    require_unopened()
    config, methods = _context(config_path)
    content, _ = _selection_content(run_dirs, config, methods)
    payload = {**content, "created_at": now()}
    require_unopened()
    write_immutable_json(_path("selection.json"), payload)
    return payload


def validate_selection(*, config_path: str | Path | None = None) -> dict:
    """Rehash and rederive every selected method/step from original runs."""
    config, methods = _context(config_path)
    payload = read_json(_path("selection.json"))
    expected, completed_at = _selection_content(
        _referenced_directories(payload.get("runs")), config, methods
    )
    if {
        key: value for key, value in payload.items() if key != "created_at"
    } != expected:
        raise ValueError("selection lock differs from revalidated development evidence")
    if _timestamp(payload.get("created_at")) < completed_at:
        raise ValueError("selection cannot predate development completion")
    return payload


def _final_content(run_dirs, config, methods, selection) -> tuple[dict, datetime]:
    runs = _collect_runs(run_dirs, config, methods, "final", selection)
    inputs = [manifest["identity"]["inputs"] for _, manifest in runs.values()]
    if any(value != selection["inputs"] for value in inputs):
        raise ValueError("final input bundle differs from development selection")
    return {
        "schema_version": 2,
        "kind": "final_run_set",
        "analysis_plan_sha256": analysis_plan_sha256(),
        "benchmark_sha256": benchmark_digest(config),
        "code_sha256": code_digest(),
        "selection_sha256": sha256_file(_path("selection.json")),
        "methods": list(config.final_methods),
        "seeds": list(config.training.seeds),
        "inputs": inputs[0],
        "runs": _references(runs),
    }, max(_timestamp(manifest["completed_at"]) for _, manifest in runs.values())


def lock_final_runs(
    run_dirs: Sequence[str | Path], *, config_path: str | Path | None = None
) -> dict:
    """Finalize all selected scientific runs before any novel opening."""
    require_unopened()
    selection = validate_selection(config_path=config_path)
    config, methods = _context(config_path)
    content, _ = _final_content(run_dirs, config, methods, selection)
    payload = {**content, "created_at": now()}
    require_unopened()
    write_immutable_json(_path("final-runs.json"), payload)
    return payload


def validate_final_runs(*, config_path: str | Path | None = None) -> dict:
    """Validate complete selected training without opening novel data."""
    selection = validate_selection(config_path=config_path)
    config, methods = _context(config_path)
    payload = read_json(_path("final-runs.json"))
    expected, completed_at = _final_content(
        _referenced_directories(payload.get("runs")), config, methods, selection
    )
    if {
        key: value for key, value in payload.items() if key != "created_at"
    } != expected:
        raise ValueError("final run lock differs from revalidated training evidence")
    if _timestamp(payload.get("created_at")) < completed_at:
        raise ValueError("final run lock cannot predate training completion")
    return payload


def _opening_content(manifest_set_path, config_path) -> tuple[dict, datetime]:
    final_runs = validate_final_runs(config_path=config_path)
    config = load_benchmark(config_path)
    episode = load_episode(manifest_set_path, "novel")
    metadata = episode["metadata"]
    inputs = final_runs["inputs"]
    if (
        metadata["manifest_set_sha256"] != inputs.get("manifest_set_sha256")
        or metadata["source_inventory_sha256"] != inputs.get("source_inventory_sha256")
        or metadata["parent_protocol_sha256"] != config.input_protocol_sha256
    ):
        raise ValueError("novel episode differs from the locked training input bundle")
    if (artifact_root().parent / "locks/test-opening.v1.json").exists():
        raise ValueError(
            "legacy novel-test opening prevents a new confirmatory opening"
        )
    return {
        "schema_version": 2,
        "kind": "test_opening",
        "analysis_plan_sha256": analysis_plan_sha256(),
        "benchmark_sha256": benchmark_digest(config),
        "code_sha256": code_digest(),
        "selection_sha256": sha256_file(_path("selection.json")),
        "final_run_set_sha256": sha256_file(_path("final-runs.json")),
        "manifest_set_path": str(Path(manifest_set_path).resolve()),
        "novel_episode": metadata,
    }, _timestamp(final_runs["created_at"])


def open_test(
    *, manifest_set_path: str | Path, config_path: str | Path | None = None
) -> dict:
    """Atomically open only the complete locked suite; repeat calls must match.

    This function verifies metadata and run evidence. The final evaluator must
    verify its physical pose/model inputs before invoking this opening event.
    """
    expected, _ = _opening_content(manifest_set_path, config_path)
    path = _path("test-opening.json")
    if path.exists():
        return validate_opening(
            manifest_set_path=manifest_set_path, config_path=config_path
        )
    payload = {**expected, "created_at": now()}
    try:
        write_immutable_json(path, payload)
    except ValueError:
        if not path.exists():
            raise
        return validate_opening(
            manifest_set_path=manifest_set_path, config_path=config_path
        )
    return payload


def validate_opening(
    *, manifest_set_path: str | Path, config_path: str | Path | None = None
) -> dict:
    """Require the existing ledger to bind both still-valid locks and the pool."""
    payload = read_json(_path("test-opening.json"))
    expected, finalized_at = _opening_content(manifest_set_path, config_path)
    if {
        key: value for key, value in payload.items() if key != "created_at"
    } != expected:
        raise ValueError("test opening differs from the locked study")
    if _timestamp(payload.get("created_at")) < finalized_at:
        raise ValueError("test opening cannot predate final run locking")
    return payload
