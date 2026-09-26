"""Predeclared equal-budget candidates and an append-only trial ledger."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pose_embed.benchmark.config import (
    REPOSITORY_ROOT,
    BenchmarkConfig,
    benchmark_digest,
    load_benchmark,
)
from pose_embed.benchmark.runtime import (
    artifact_path,
    artifact_root,
    code_digest,
    now,
    read_json,
    require_unopened,
    verify_run,
)
from pose_embed.provenance import sha256_file, write_immutable_json

DEFINITION = REPOSITORY_ROOT / "configs/benchmark-campaign.v2.json"
CANDIDATES = {"baseline": 1.0, "half": 0.5, "double": 2.0}


def campaign_path():
    return artifact_root() / "locks/campaign.json"


def candidate_config(config, candidate):
    if candidate not in CANDIDATES:
        raise ValueError("candidate must be baseline, half or double")
    return config.model_copy(
        update={
            "training": config.training.model_copy(
                update={"learning_rate_scale": CANDIDATES[candidate]}
            )
        }
    )


def _reference(path):
    path = artifact_path(path)
    return {"path": str(path.relative_to(artifact_root())), "sha256": sha256_file(path)}


def _verify_reference(reference):
    relative = Path(reference["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("campaign reference must be inside the artifact root")
    path = artifact_path(artifact_root() / relative)
    if sha256_file(path) != reference["sha256"]:
        raise ValueError("campaign evidence changed")
    return path


def _prior_trials(roots):
    """Archive prior attempts and failed profiles without score selection."""
    evidence = []
    for value in sorted(set(roots)):
        root = artifact_path(value)
        for attempt in sorted(root.rglob("attempt.json")):
            outcome = attempt.with_name("outcome.json")
            if not outcome.is_file():
                raise ValueError(
                    "finish prior engineering attempts before declaring campaign"
                )
            evidence.append(
                {"attempt": _reference(attempt), "outcome": _reference(outcome)}
            )
    return evidence


def _profile_evidence(directories, config):
    profiles = {}
    forecast = {}
    for value in directories:
        path = artifact_path(value)
        manifest = verify_run(path)
        identity = manifest["identity"]
        method = identity["method"]
        recorded = BenchmarkConfig.model_validate(identity["configuration"])
        if (
            method in profiles
            or method not in config.final_methods
            or identity["stage"] != "profile"
            or identity["track"] != "finetune"
            or identity["steps"] < 3
            or recorded.training.physical_batch_size
            != config.training.physical_batch_size
            or recorded.training.classes_per_batch != config.training.classes_per_batch
            or recorded.training.learning_rate_scale != 1.0
            or recorded.methods_sha256 != config.methods_sha256
            or identity["precision"] != "float32"
        ):
            raise ValueError(
                "campaign needs one full fine-tuning capacity profile per method"
            )
        telemetry = read_json(path / "telemetry.json")
        history = read_json(path / "history.json")["steps"]
        if (
            not telemetry["environment"].get("cuda_device_name")
            or telemetry["peak_allocated_bytes"] <= 0
        ):
            raise ValueError(
                "campaign feasibility requires actual allocated GPU evidence"
            )
        mean_step_seconds = sum(row["seconds"] for row in history) / len(history)
        profiles[method] = _reference(path / "run-manifest.json")
        forecast[method] = {
            "profile_mean_update_seconds": mean_step_seconds,
            "development_update_hours_lower_bound": mean_step_seconds
            * config.training.steps
            * 18
            / 3600,
            "final_update_hours_upper_step_budget": mean_step_seconds
            * config.training.steps
            * 6
            / 3600,
            "peak_allocated_bytes": telemetry["peak_allocated_bytes"],
            "profile_checkpoint_bytes": telemetry["checkpoint_bytes"],
        }
    if set(profiles) != set(config.final_methods):
        raise ValueError("all 26 GPU profiles are required before the main campaign")
    return profiles, forecast


def declare_campaign(*, config_path, run_root, profiles, prior_trial_roots):
    """Freeze all 468 development cells before any candidate begins."""
    require_unopened()
    config = load_benchmark(config_path)
    if (
        config.training.encoder_mode != "finetune"
        or config.training.learning_rate_scale != 1.0
    ):
        raise ValueError(
            "campaign base must be fine-tuning with the unscaled source recipe"
        )
    root = artifact_path(run_root)
    if root.exists() and any(root.iterdir()):
        raise ValueError("campaign needs a fresh empty trial directory")
    definition = read_json(DEFINITION)
    if definition["candidates"] != [
        {"candidate_id": key, "learning_rate_scale": value}
        for key, value in CANDIDATES.items()
    ]:
        raise ValueError(
            "candidate grid differs from the declared three-candidate design"
        )
    profile_refs, forecast = _profile_evidence(profiles, config)
    prior = _prior_trials(prior_trial_roots)
    if not prior:
        raise ValueError(
            "record the prioritized engineering pilots before the main campaign"
        )
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "kind": "development_campaign",
        "created_at": now(),
        "definition": definition,
        "definition_sha256": sha256_file(DEFINITION),
        "code_sha256": code_digest(),
        "configuration": config.model_dump(mode="json"),
        "benchmark_sha256": benchmark_digest(config),
        "run_root": str(root.relative_to(artifact_root())),
        "candidates": {
            key: candidate_config(config, key).model_dump(mode="json")
            for key in CANDIDATES
        },
        "required_development_runs": len(config.final_methods)
        * len(config.training.seeds)
        * len(CANDIDATES),
        "profiles": profile_refs,
        "resource_forecast": forecast,
        "forecast_scope": (
            "update-only estimates exclude data loading, validation, queue bootstrap "
            "and checkpoint segmentation; profile checkpoint size is not a disk "
            "reservation"
        ),
        "prior_trial_roots": [
            str(artifact_path(p).relative_to(artifact_root()))
            for p in sorted(set(prior_trial_roots))
        ],
        "prior_trials": prior,
    }
    write_immutable_json(campaign_path(), payload)
    return payload


def validate_campaign(config):
    payload = read_json(campaign_path())
    if (
        payload.get("code_sha256") != code_digest()
        or payload.get("configuration") != config.model_dump(mode="json")
        or payload.get("benchmark_sha256") != benchmark_digest(config)
        or payload.get("definition_sha256") != sha256_file(DEFINITION)
        or payload.get("definition") != read_json(DEFINITION)
        or payload.get("candidates")
        != {
            key: candidate_config(config, key).model_dump(mode="json")
            for key in CANDIDATES
        }
        or payload.get("required_development_runs") != 468
    ):
        raise ValueError("campaign code, grid or base configuration changed")
    timestamp = datetime.fromisoformat(payload["created_at"])
    if timestamp.tzinfo is None or timestamp > datetime.fromisoformat(now()):
        raise ValueError("campaign declaration timestamp is invalid")
    refs = payload.get("profiles", {})
    profiles, forecast = _profile_evidence(
        [_verify_reference(v).parent for v in refs.values()], config
    )
    if profiles != refs or forecast != payload.get("resource_forecast"):
        raise ValueError("campaign feasibility evidence changed")
    roots = [artifact_path(artifact_root() / p) for p in payload["prior_trial_roots"]]
    if _prior_trials(roots) != payload["prior_trials"]:
        raise ValueError("prior trial inventory changed or was omitted")
    for trial in payload["prior_trials"]:
        _verify_reference(trial["attempt"])
        _verify_reference(trial["outcome"])
    return payload


def training_binding(config, candidate, output_dir):
    declaration = validate_campaign(config)
    root = artifact_path(artifact_root() / declaration["run_root"])
    if (
        not artifact_path(output_dir).is_relative_to(root)
        or artifact_path(output_dir) == root
    ):
        raise ValueError(
            "candidate attempts must be inside the declared campaign directory"
        )
    effective = candidate_config(config, candidate)
    return effective, {
        "candidate": candidate,
        "campaign_sha256": sha256_file(campaign_path()),
    }


def review_failure(directory, *, category, reason):
    """Add an operational classification without editing the original outcome."""
    require_unopened()
    directory = artifact_path(directory)
    outcome = read_json(directory / "outcome.json")
    if (
        outcome.get("status") != "failed"
        or category
        not in {"gpu_allocation", "preemption", "filesystem", "process_interruption"}
        or len(reason.strip()) < 20
    ):
        raise ValueError(
            "operational failure review needs a failed run and a concrete reason"
        )
    message = str(outcome.get("error", "")).lower()
    if any(
        word in message
        for word in (
            "non-finite",
            "nonfinite",
            "finite scalar",
            "finite gradient",
            "nan",
        )
    ):
        raise ValueError(
            "numerical instability cannot be excluded as an operational failure"
        )
    payload = {
        "created_at": now(),
        "category": category,
        "reason": reason.strip(),
        "outcome_sha256": sha256_file(directory / "outcome.json"),
    }
    write_immutable_json(directory / "failure-review.json", payload)
    return payload


def audit_trials(declaration, run_dirs):
    """Selection must account for every attempt, not a favorable subset."""
    root = artifact_path(artifact_root() / declaration["run_root"])
    successes, ledger = set(), []
    for attempt in sorted(root.rglob("attempt.json")):
        directory = attempt.parent
        payload = read_json(attempt)
        identity = payload["identity"]
        if (
            identity.get("campaign_sha256") != sha256_file(campaign_path())
            or identity.get("candidate") not in CANDIDATES
        ):
            raise ValueError("undeclared attempt in campaign trial directory")
        if datetime.fromisoformat(payload["started_at"]) < datetime.fromisoformat(
            declaration["created_at"]
        ):
            raise ValueError("candidate started before its trial grid was declared")
        outcome = read_json(directory / "outcome.json")
        entry = {
            "attempt": _reference(attempt),
            "outcome": _reference(directory / "outcome.json"),
        }
        if outcome.get("status") == "succeeded":
            successes.add(directory.resolve())
        elif outcome.get("status") == "failed":
            review = read_json(directory / "failure-review.json")
            if review.get("outcome_sha256") != sha256_file(directory / "outcome.json"):
                raise ValueError("failure review no longer binds its original outcome")
            if review.get("category") not in {
                "gpu_allocation",
                "preemption",
                "filesystem",
                "process_interruption",
            }:
                raise ValueError("failure is not a declared operational retry")
            message = str(outcome.get("error", "")).lower()
            if any(
                word in message
                for word in (
                    "non-finite",
                    "nonfinite",
                    "finite scalar",
                    "finite gradient",
                    "nan",
                )
            ):
                raise ValueError(
                    "numerically unstable trials cannot be hidden by retries"
                )
            entry["review"] = _reference(directory / "failure-review.json")
        else:
            raise ValueError("campaign has unfinished attempts")
        ledger.append(entry)
    if successes != {artifact_path(p) for p in run_dirs}:
        raise ValueError("selection must include every successful campaign attempt")
    return ledger


def selection_content(run_dirs, config, methods, select_candidate):
    declaration = validate_campaign(config)
    ledger = audit_trials(declaration, run_dirs)
    groups = {key: [] for key in CANDIDATES}
    pairing = {}
    for value in run_dirs:
        directory = artifact_path(value)
        identity = read_json(directory / "run-manifest.json")["identity"]
        candidate = identity.get("candidate")
        if candidate not in groups:
            raise ValueError("selection cannot include an engineering pilot")
        groups[candidate].append(directory)
        initialization = read_json(directory / "initialization.json")
        batches = read_json(directory / "batch-plan.json")
        pair = {
            "initialization": initialization,
            "batches": batches,
            "inputs": identity["inputs"],
        }
        key = (identity["method"], identity["seed"])
        if pairing.setdefault(key, pair) != pair:
            raise ValueError(
                "candidate initializations, physical batches or inputs differ"
            )
    contents, completed = {}, []
    for candidate in CANDIDATES:
        content, timestamp = select_candidate(
            groups[candidate], candidate_config(config, candidate), methods
        )
        contents[candidate] = content
        completed.append(timestamp)
    baseline = contents["baseline"]
    if any(
        content["development_episode"] != baseline["development_episode"]
        or content["inputs"] != baseline["inputs"]
        for content in contents.values()
    ):
        raise ValueError("candidate relevance conditions or inputs differ")
    selected = {}
    for method in config.final_methods:
        best = max(
            CANDIDATES,
            key=lambda candidate: contents[candidate]["methods"][method][
                "mean_validation_r_at_1"
            ],
        )
        selected[method] = contents[best]["methods"][method] | {
            "candidate": best,
            "learning_rate_scale": CANDIDATES[best],
            "candidates": {
                key: value["methods"][method] for key, value in contents.items()
            },
        }
    return baseline | {
        "methods": selected,
        "benchmark_sha256": benchmark_digest(config),
        "campaign_sha256": sha256_file(campaign_path()),
        "trial_ledger": ledger,
        "selection_rule": declaration["definition"]["selection_rule"],
        "runs": [
            row | {"candidate": key}
            for key, value in contents.items()
            for row in value["runs"]
        ],
    }, max(completed)
