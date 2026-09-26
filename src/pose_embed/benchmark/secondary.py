"""Predeclared secondary matrices and deterministic training-only interventions."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from pose_embed.benchmark.config import (
    REPOSITORY_ROOT,
    benchmark_digest,
    load_benchmark,
    load_methods,
)
from pose_embed.benchmark.runtime import (
    artifact_root,
    code_digest,
    digest,
    now,
    read_json,
    require_unopened,
)
from pose_embed.provenance import sha256_file, write_immutable_json

PLAN_PATH = REPOSITORY_ROOT / "configs/benchmark-secondary.v2.json"
ROBUST_METHODS = (
    "context_only",
    "contrastive",
    "multi_similarity",
    "multi_similarity_miner",
)
RATES = (0.05, 0.1, 0.2)
FRACTIONS = (0.25, 0.5, 0.75)
CONDITIONS = (
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
)
_VALIDATED_PLANS = ContextVar("secondary_validated_plans", default=None)


@contextmanager
def secondary_validation_scope():
    """Reuse primary evidence only within one synchronous validation operation."""
    if _VALIDATED_PLANS.get() is not None:
        yield
        return
    token = _VALIDATED_PLANS.set({})
    try:
        yield
    finally:
        _VALIDATED_PLANS.reset(token)


def specification():
    """Finite settings explicitly implemented and bound by the scientific code hash."""
    return {
        "schema_version": 1,
        "protocol_id": "motion-retrieval-v2",
        "status": "specified",
        "classification": "secondary_descriptive",
        "seeds": [7, 17, 29, 43, 59, 71],
        "one_shot": {
            "methods": "all_main_methods",
            "query_definition": "official",
            "condition": "clean",
        },
        "query_corruption": {
            "methods": ["contrastive", "contextual"],
            "query_definitions": ["official", "primary"],
            "conditions": list(CONDITIONS),
            "implementation": "v1_query_only_stable_sample_seed",
            "gallery": {
                "official": "clean_official_20_anchors",
                "primary": "clean_full_novel_pool",
            },
            "query_policy": {
                "official": "official_one_shot_retains_synchronized_anchor_views",
                "primary": "full_novel_pool_self_and_synchronized_performance_excluded",
            },
        },
        "components": {
            "lambda": [0, "selected_contextual", 1],
            "gamma": [0, "selected_contextual"],
            "classes_per_batch": 8,
            "samples_per_class": 4,
        },
        "robustness": {
            "methods": list(ROBUST_METHODS),
            "label_noise": list(RATES),
            "pose_replacement": list(RATES),
            "retained_action_fraction": list(FRACTIONS),
            "classes_per_batch": 4,
            "samples_per_class": 8,
            "label_noise_policy": "fixed_sample_subset_uniform_other_training_action",
            "replacement_policy": (
                "fixed_sample_subset_other_training_action_and_performance"
            ),
            "action_subset_policy": "seeded_nested_training_action_prefix",
            "clean_control": True,
        },
        "training": {
            "track": "finetune",
            "embedding_dimension": 512,
            "stages": ["development", "final"],
            "recipe": "inherit_selected_main_learning_rate_scale_and_step_budget",
            "checkpoint": "fixed_last_step_no_secondary_selection",
            "reuse": "disabled_all_cells_have_independent_immutable_evidence",
            "require_development_before_final": True,
            "require_all_final_before_novel": True,
        },
        "analysis": {
            "metrics": [
                "r_at_1",
                "r_at_2",
                "r_at_4",
                "r_at_8",
                "map",
                "map_at_r",
                "mrr",
            ],
            "one_shot_metrics": ["top1", "mrr", "r_at_5", "map"],
            "aggregation": "query_weighted_mean_then_equal_seed_mean",
            "uncertainty": "sample_standard_deviation_and_all_six_seed_values",
            "comparative_claims": "descriptive_only_no_confirmatory_claims",
        },
    }


def secondary_plan_sha256():
    return sha256_file(PLAN_PATH)


def load_secondary_plan(config=None):
    plan = read_json(PLAN_PATH)
    if plan != specification():
        raise ValueError("secondary settings differ from the predeclared finite study")
    if config is not None and list(config.training.seeds) != plan["seeds"]:
        raise ValueError("secondary and primary paired seeds differ")
    return plan


def training_cells():
    """46 logical configurations; six seeds give 276 runs per stage."""
    load_secondary_plan()
    cells = {}
    for lam in ("zero", "selected", "one"):
        for gamma in ("zero", "selected"):
            key = f"components-lambda-{lam}-gamma-{gamma}"
            cells[key] = {
                "cell_id": key,
                "study": "components",
                "method": "contextual",
                "lambda": lam,
                "gamma": gamma,
                "intervention": "clean",
                "amount": 0.0,
                "classes_per_batch": 8,
                "samples_per_class": 4,
            }
    conditions = [("clean", 0.0)] + [
        (family, amount)
        for family, amounts in (
            ("label_noise", RATES),
            ("pose_replacement", RATES),
            ("retained_actions", FRACTIONS),
        )
        for amount in amounts
    ]
    for method in ROBUST_METHODS:
        for family, amount in conditions:
            key = f"robustness-{method}-{family}-{amount:g}"
            cells[key] = {
                "cell_id": key,
                "study": "robustness",
                "method": "contextual" if method == "context_only" else method,
                "pure_contextual": method == "context_only",
                "intervention": family,
                "amount": amount,
                "classes_per_batch": 4,
                "samples_per_class": 8,
            }
    return cells


def forecast():
    plan = load_secondary_plan()
    n = len(plan["seeds"])
    return {
        "classification": plan["classification"],
        "secondary_plan_sha256": secondary_plan_sha256(),
        "main_final_runs": 26 * n,
        "secondary_training_configurations": len(training_cells()),
        "secondary_training_runs_per_stage": len(training_cells()) * n,
        "secondary_development_runs": 276,
        "secondary_final_runs": 276,
        "secondary_total_training_runs": 552,
        "all_required_final_runs_before_opening": 432,
        "one_shot_evaluation_cells": 26 * n,
        "query_corruption_evaluation_cells": 2 * n * len(CONDITIONS) * 2,
        "overlapping_clean_official_evaluation_cells": 2 * n,
        "unique_main_checkpoint_secondary_evaluation_cells": 384,
        "secondary_checkpoint_novel_evaluation_cells": 276,
        "uses_measured_gpu_forecast": False,
        "notes": "Declared cells, not completed runs or measured resource forecasts.",
    }


def _rng(seed, purpose):
    return random.Random(int(digest(["secondary-v2", seed, purpose])[:16], 16))


def training_data_plan(records, *, stage, seed, cell):
    """Only verified current-stage training metadata; no pose or novel reads."""
    split = {"development": "development_train", "final": "final_train"}.get(stage)
    if not split or not records or any(row.split != split for row in records):
        raise ValueError(
            "secondary interventions require only the current training partition"
        )
    if len({row.sample_id for row in records}) != len(records):
        raise ValueError("secondary training records must be unique")
    actions = sorted({row.ntu.action for row in records})
    expected = 80 if stage == "development" else 100
    if len(actions) != expected:
        raise ValueError(
            "secondary interventions require the full declared 80/100 training actions"
        )
    ordered_actions = actions[:]
    _rng(seed, "action-subset").shuffle(ordered_actions)
    retained = set(actions)
    if cell["intervention"] == "retained_actions":
        retained = set(ordered_actions[: int(len(actions) * cell["amount"])])
    rows = [row for row in records if row.ntu.action in retained]
    observed = [row.ntu.action for row in rows]
    source_ids = [row.sample_id for row in rows]
    chosen = list(range(len(rows)))
    _rng(seed, "affected-sample-order").shuffle(chosen)
    amount = cell["amount"]
    changed = []
    by_action = defaultdict(list)
    for row in records:
        by_action[row.ntu.action].append(row)
    if cell["intervention"] in {"label_noise", "pose_replacement"}:
        changed = sorted(chosen[: math.floor(len(rows) * amount)])
        for index in changed:
            generator = _rng(seed, [cell["intervention"], rows[index].sample_id])
            action = generator.choice(
                [a for a in actions if a != rows[index].ntu.action]
            )
            if cell["intervention"] == "label_noise":
                observed[index] = action
            else:
                candidates = [
                    row
                    for row in by_action[action]
                    if row.ntu.performance_id != rows[index].ntu.performance_id
                ]
                source_ids[index] = generator.choice(candidates).sample_id
    mapping = {action: index for index, action in enumerate(sorted(retained))}
    labels = [mapping[action] for action in observed]
    if min(Counter(labels).values()) < cell["samples_per_class"] or len(
        set(labels)
    ) != len(mapping):
        raise ValueError(
            "intervention leaves insufficient items for the declared physical batch"
        )
    return {
        "schema_version": 1,
        "stage": stage,
        "seed": seed,
        "intervention": cell["intervention"],
        "amount": amount,
        "parent_order_sha256": digest([row.sample_id for row in records]),
        "sample_ids": [row.sample_id for row in rows],
        "source_sample_ids": source_ids,
        "true_actions": [row.ntu.action for row in rows],
        "observed_actions": observed,
        "label_mapping": {str(k): v for k, v in mapping.items()},
        "labels": labels,
        "retained_actions": sorted(retained),
        "changed_indices": changed,
        "changed_fraction": len(changed) / len(rows),
    }


def _path(name):
    return artifact_root() / "locks" / name


def _lock_content(config_path, selection):
    from pose_embed.benchmark.campaign import selected_config

    config = load_benchmark(config_path)
    load_secondary_plan(config)
    specs = load_methods()
    resolved = {}
    for key, cell in training_cells().items():
        method = cell["method"]
        selected = selection["methods"][method]
        effective = selected_config(config, selection, method)
        parameters = specs[method].parameters.copy()
        if method == "contextual":
            parameters["k"] = cell["samples_per_class"]
            if cell["study"] == "components":
                parameters["lam"] = {
                    "zero": 0.0,
                    "one": 1.0,
                    "selected": parameters["lam"],
                }[cell["lambda"]]
                parameters["gamma"] = (
                    0.0 if cell["gamma"] == "zero" else parameters["gamma"]
                )
            elif cell["pure_contextual"]:
                parameters.update(lam=1.0, gamma=0.0)
        training = effective.training.model_copy(
            update={
                "classes_per_batch": cell["classes_per_batch"],
                "samples_per_class": cell["samples_per_class"],
                "steps": selected["selected_steps"],
                "validation_every": min(
                    effective.training.validation_every, selected["selected_steps"]
                ),
            }
        )
        effective = effective.model_copy(update={"training": training})
        resolved[key] = cell | {
            "configuration": effective.model_dump(mode="json"),
            "method_specification": specs[method]
            .model_copy(update={"parameters": parameters})
            .model_dump(mode="json"),
            "selected_steps": selected["selected_steps"],
            "parent_candidate": selected["candidate"],
        }
    return {
        "schema_version": 1,
        "kind": "secondary_plan",
        "classification": "secondary_descriptive",
        "secondary_plan_sha256": secondary_plan_sha256(),
        "main_benchmark_sha256": benchmark_digest(config),
        "main_configuration_path": str(Path(config_path).resolve()),
        "selection_sha256": sha256_file(_path("selection.json")),
        "code_sha256": code_digest(),
        "inputs": selection["inputs"],
        "seeds": list(config.training.seeds),
        "cells": resolved,
        "forecast": forecast()
        | {
            "optimizer_updates_per_stage": sum(
                cell["selected_steps"] for cell in resolved.values()
            )
            * len(config.training.seeds),
            "physical_training_items_per_stage": 32
            * sum(cell["selected_steps"] for cell in resolved.values())
            * len(config.training.seeds),
        },
    }


def lock_secondary_plan(*, config_path):
    from pose_embed.benchmark.locks import validate_selection

    require_unopened()
    selected = validate_selection(config_path=config_path)
    payload = _lock_content(config_path, selected) | {"created_at": now()}
    require_unopened()
    write_immutable_json(_path("secondary-plan.json"), payload)
    return payload


def validate_secondary_plan(*, config_path=None):
    from pose_embed.benchmark.locks import _timestamp, validate_selection

    payload = read_json(_path("secondary-plan.json"))
    path = config_path or payload["main_configuration_path"]
    key = (str(_path("secondary-plan.json")), str(Path(path).resolve()))
    fingerprint = (
        sha256_file(_path("secondary-plan.json")),
        sha256_file(_path("selection.json")),
        sha256_file(path),
        secondary_plan_sha256(),
        code_digest(),
        digest(
            {key: spec.model_dump(mode="json") for key, spec in load_methods().items()}
        ),
    )
    cache = _VALIDATED_PLANS.get()
    if cache is not None and key in cache:
        previous_fingerprint, previous_payload = cache[key]
        if previous_fingerprint != fingerprint or previous_payload != payload:
            raise ValueError("secondary plan evidence changed during validation")
        return payload
    selected = validate_selection(config_path=path)
    expected = _lock_content(path, selected)
    if {k: v for k, v in payload.items() if k != "created_at"} != expected:
        raise ValueError("secondary plan differs from the locked selected main recipes")
    if _timestamp(payload.get("created_at")) < _timestamp(selected["created_at"]):
        raise ValueError("secondary plan predates main selection")
    if cache is not None:
        cache[key] = (fingerprint, payload)
    return payload


def resolve_training_cell(cell_id, *, config_path, stage, seed):
    from pose_embed.benchmark.config import BenchmarkConfig, MethodSpec

    plan = validate_secondary_plan(config_path=config_path)
    if (
        cell_id not in plan["cells"]
        or seed not in plan["seeds"]
        or stage not in {"development", "final"}
    ):
        raise ValueError("secondary cell, seed or stage is outside its locked matrix")
    cell = plan["cells"][cell_id]
    return (
        BenchmarkConfig.model_validate(cell["configuration"]),
        MethodSpec.model_validate(cell["method_specification"]),
        cell,
        {
            "classification": "secondary_descriptive",
            "cell_id": cell_id,
            "secondary_plan_sha256": plan["secondary_plan_sha256"],
            "secondary_lock_sha256": sha256_file(_path("secondary-plan.json")),
            "main_configuration_path": plan["main_configuration_path"],
        },
    )


def validate_run_binding(identity):
    binding = identity.get("secondary", {})
    config, spec, cell, expected = resolve_training_cell(
        binding.get("cell_id"),
        config_path=binding.get("main_configuration_path"),
        stage=identity.get("stage"),
        seed=identity.get("seed"),
    )
    if (
        {key: value for key, value in binding.items() if key != "data_plan_sha256"}
        != expected
        or not isinstance(binding.get("data_plan_sha256"), str)
        or len(binding["data_plan_sha256"]) != 64
        or identity.get("configuration") != config.model_dump(mode="json")
        or identity.get("method_specification") != spec.model_dump(mode="json")
        or identity.get("method") != spec.method_id
        or identity.get("steps") != cell["selected_steps"]
        or identity.get("track") != "finetune"
        or identity.get("scientific_use_allowed") is not True
        or any(
            key in identity
            for key in ("candidate", "campaign_sha256", "campaign_base_config_path")
        )
        or identity.get("selection_sha256") != sha256_file(_path("selection.json"))
    ):
        raise ValueError("secondary run differs from its exact locked cell")
    return config, spec, cell


def prepared_records(records, data_plan):
    lookup = {row.sample_id: row for row in records}
    return [lookup[sample_id] for sample_id in data_plan["sample_ids"]]


def bind_dataset(dataset, data_plan):
    """Redirect only this dataset's annotations and observed supervision."""
    dataset.annotations = {
        sample_id: dataset.annotations[source_id]
        for sample_id, source_id in zip(
            data_plan["sample_ids"], data_plan["source_sample_ids"], strict=True
        )
    }
    dataset.labels = data_plan["labels"][:]
    dataset.label_mapping = {
        int(key): value for key, value in data_plan["label_mapping"].items()
    }


def verify_data_plan(directory, identity, records):
    _, _, cell = validate_run_binding(identity)
    expected = training_data_plan(
        records, stage=identity["stage"], seed=identity["seed"], cell=cell
    )
    if (
        digest(expected) != identity["secondary"]["data_plan_sha256"]
        or read_json(directory / "secondary-data-plan.json") != expected
    ):
        raise ValueError(
            "secondary data intervention differs from its immutable training-only plan"
        )
    return expected


@secondary_validation_scope()
def _runs_content(run_dirs, *, config_path, stage):
    from pose_embed.benchmark.locks import _timestamp
    from pose_embed.benchmark.runtime import artifact_path, verify_run

    plan = validate_secondary_plan(config_path=config_path)
    expected = {(cell, seed) for cell in plan["cells"] for seed in plan["seeds"]}
    runs, pairs = {}, {}
    completion = _timestamp(plan["created_at"])
    for value in run_dirs:
        directory = artifact_path(value)
        manifest = verify_run(directory)
        identity = manifest["identity"]
        binding = identity.get("secondary", {})
        key = (binding.get("cell_id"), identity.get("seed"))
        if key not in expected or key in runs or identity.get("stage") != stage:
            raise ValueError(
                "secondary run coverage has an absent, duplicate or wrong-stage cell"
            )
        if identity["inputs"] != plan["inputs"]:
            raise ValueError("secondary inputs differ from primary selection")
        started = _timestamp(read_json(directory / "attempt.json")["started_at"])
        finished = _timestamp(manifest["completed_at"])
        if started < _timestamp(plan["created_at"]) or finished < started:
            raise ValueError(
                "secondary training must follow its result-blind plan lock"
            )
        completion = max(completion, finished)
        cell = plan["cells"][key[0]]
        initial = read_json(directory / "initialization.json")
        batch = read_json(directory / "batch-plan.json")
        pair_key = (key[1], cell["study"], cell["intervention"], cell["amount"])
        pair = {
            "encoder": initial["encoder"],
            "head": initial["head"],
            "data_plan": binding["data_plan_sha256"],
            "sample_ids": batch["sample_ids"],
        }
        previous = pairs.setdefault(pair_key, {"identity": pair, "steps": []})
        if previous["identity"] != pair:
            raise ValueError(
                "secondary methods do not share paired initialization or intervention"
            )
        for other in previous["steps"]:
            n = min(len(other), len(batch["steps"]))
            if other[:n] != batch["steps"][:n]:
                raise ValueError(
                    "secondary physical batch prefixes differ across methods"
                )
        previous["steps"].append(batch["steps"])
        runs[key] = {
            "cell_id": key[0],
            "seed": key[1],
            "method": identity["method"],
            "relative_path": str(directory.relative_to(artifact_root())),
            "run_manifest_sha256": sha256_file(directory / "run-manifest.json"),
            "checkpoint_sha256": sha256_file(directory / "checkpoint.pt"),
        }
    if set(runs) != expected:
        raise ValueError("secondary lock requires all 46 cells and six paired seeds")
    return {
        "schema_version": 1,
        "kind": f"secondary_{stage}",
        "classification": "secondary_descriptive",
        "secondary_plan_sha256": secondary_plan_sha256(),
        "secondary_lock_sha256": sha256_file(_path("secondary-plan.json")),
        "selection_sha256": sha256_file(_path("selection.json")),
        "code_sha256": code_digest(),
        "inputs": plan["inputs"],
        "runs": [runs[key] for key in sorted(runs)],
    }, completion


@secondary_validation_scope()
def lock_secondary_runs(run_dirs, *, config_path, stage):
    require_unopened()
    if stage not in {"development", "final"}:
        raise ValueError("secondary training lock requires development or final")
    if stage == "final":
        validate_secondary_runs(config_path=config_path, stage="development")
    content, _ = _runs_content(run_dirs, config_path=config_path, stage=stage)
    payload = content | {"created_at": now()}
    require_unopened()
    write_immutable_json(_path(f"secondary-{stage}.json"), payload)
    return payload


@secondary_validation_scope()
def validate_secondary_runs(*, config_path, stage="final"):
    from pose_embed.benchmark.locks import _referenced_directories, _timestamp

    if stage not in {"development", "final"}:
        raise ValueError("secondary training lock requires development or final")
    payload = read_json(_path(f"secondary-{stage}.json"))
    content, completion = _runs_content(
        _referenced_directories(payload.get("runs")),
        config_path=config_path,
        stage=stage,
    )
    if {
        key: value for key, value in payload.items() if key != "created_at"
    } != content or _timestamp(payload.get("created_at")) < completion:
        raise ValueError("secondary training lock differs from verified run evidence")
    if stage == "final":
        development = validate_secondary_runs(
            config_path=config_path, stage="development"
        )
        for reference in payload["runs"]:
            attempt = read_json(
                artifact_root() / reference["relative_path"] / "attempt.json"
            )
            if _timestamp(attempt["started_at"]) < _timestamp(
                development["created_at"]
            ):
                raise ValueError(
                    "secondary final training must follow complete development locking"
                )
    return payload
