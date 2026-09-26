"""Predeclared equal-budget candidates and an append-only trial ledger."""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

from pose_embed.benchmark.config import (
    REPOSITORY_ROOT,
    BenchmarkConfig,
    benchmark_digest,
    load_benchmark,
    load_methods,
)
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


def _timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("campaign evidence timestamps require a timezone")
    return result


def _trial_evidence(directory):
    names = {"attempt.json"} | {path.name for path in directory.glob("*.json")}
    manifest_path = directory / "run-manifest.json"
    if not manifest_path.is_file():
        manifest_path = directory / "segment-manifest.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        names.add(manifest_path.name)
        for name, expected in manifest.get("outputs", {}).items():
            if Path(name).name != name:
                raise ValueError("trial manifest output must be a filename")
            # Preserve large checkpoint hashes through the immutable manifest;
            # bind every compact scientific/operational output directly as well.
            if name.endswith(".json"):
                if sha256_file(directory / name) != expected:
                    raise ValueError("prior trial result or telemetry was changed")
                names.add(name)
    return {name: _reference(directory / name) for name in sorted(names)}


def _prior_trials(roots):
    """Disclose every experiment and segment attempt under the supplied roots."""
    attempts = set()
    for value in roots:
        attempts.update(artifact_path(value).rglob("attempt.json"))
    evidence = []
    for attempt in sorted(attempts):
        outcome = attempt.with_name("outcome.json")
        if (
            not outcome.is_file()
            and not attempt.with_name("segment-manifest.json").is_file()
        ):
            raise ValueError(
                "finish prior engineering attempts before declaring campaign"
            )
        evidence.append(_trial_evidence(attempt.parent))
    return evidence


def _prior_summaries(roots):
    paths = set()
    for root in roots:
        paths.update(
            path
            for path in artifact_path(root).rglob("*.json")
            if not (path.parent / "attempt.json").exists()
        )
    return [_reference(path) for path in sorted(paths)]


def _check_prior_coverage(roots, profiles, trial_root, declared_at):
    roots = [artifact_path(value) for value in roots]
    profiles = [artifact_path(value) for value in profiles]
    for attempt in artifact_root().rglob("attempt.json"):
        if attempt.is_relative_to(trial_root) or any(
            attempt.is_relative_to(profile) for profile in profiles
        ):
            continue
        started = _timestamp(read_json(attempt)["started_at"])
        if started <= declared_at and not any(
            attempt.is_relative_to(root) for root in roots
        ):
            raise ValueError("prior trial roots omit an existing benchmark attempt")


def verify_priority_comparison(comparison, prior_trial_roots=None):
    """Verify paired pilot provenance without loading it with new source code.

    Returns hashes and identities, not retrieval scores. Large selected pilot
    checkpoints are hashed; the source release need not equal current code.
    """
    path = artifact_path(comparison)
    payload = read_json(path)
    if (
        payload.get("content_sha256")
        != digest({k: v for k, v in payload.items() if k != "content_sha256"})
        or payload.get("stage") != "development"
        or set(payload.get("methods", [])) != {"contrastive", "contextual"}
    ):
        raise ValueError(
            "priority gate requires the completed paired development comparison"
        )
    rows = payload.get("runs", [])
    roots = (
        prior_trial_roots
        if prior_trial_roots is not None
        else [row["path"] for row in rows]
    )
    seeds = payload.get("seeds", [])
    if (
        not seeds
        or {(r.get("method"), r.get("seed")) for r in rows}
        != {(m, s) for m in ("contrastive", "contextual") for s in seeds}
        or len(rows) != 2 * len(seeds)
    ):
        raise ValueError("priority comparison must contain paired method/seed results")
    references = []
    paired = {}
    source_code = None
    source_configuration = None
    source_inputs = None
    for row in rows:
        directory = artifact_path(row["path"])
        if not any(directory.is_relative_to(artifact_path(root)) for root in roots):
            raise ValueError("priority runs must be disclosed in prior trial roots")
        if sha256_file(directory / "run-manifest.json") != row["run_manifest_sha256"]:
            raise ValueError("priority comparison run manifest changed")
        evidence = _trial_evidence(directory)
        manifest = read_json(directory / "run-manifest.json")
        identity = manifest["identity"]
        code = identity.get("code_sha256")
        if (
            not isinstance(code, str)
            or len(code) != 64
            or (source_code is not None and source_code != code)
        ):
            raise ValueError("priority runs must bind one original source release")
        source_code = code
        if (
            source_configuration is not None
            and source_configuration != identity["benchmark_sha256"]
        ):
            raise ValueError("priority runs mix original configurations")
        source_configuration = identity["benchmark_sha256"]
        if source_inputs is not None and source_inputs != identity["inputs"]:
            raise ValueError("priority runs mix original input bindings")
        source_inputs = identity["inputs"]
        expected_checkpoint = manifest.get("outputs", {}).get("checkpoint.pt")
        if (
            not expected_checkpoint
            or sha256_file(directory / "checkpoint.pt") != expected_checkpoint
        ):
            raise ValueError("original priority checkpoint content changed")
        result = read_json(directory / "development-result.json")
        telemetry = read_json(directory / "telemetry.json")
        if (
            identity.get("track") != "finetune"
            or identity.get("stage") != "development"
            or identity.get("scientific_use_allowed") is not True
            or identity.get("method") != row["method"]
            or identity.get("seed") != row["seed"]
            or read_json(directory / "outcome.json").get("status") != "succeeded"
            or result.get("metrics") != row.get("metrics")
            or result.get("identity") != identity
            or telemetry.get("encoder_backward_steps", 0) < 1
        ):
            raise ValueError(
                "priority comparison requires completed actual fine-tuning"
            )
        initialization = read_json(directory / "initialization.json")
        pairing = {
            "encoder": initialization["encoder"],
            "head": initialization["head"],
            "inputs": identity["inputs"],
            "configuration": identity["benchmark_sha256"],
            "batches": manifest["outputs"]["batch-plan.json"],
            "queries": result["query_order_sha256"],
            "exclusions": result["exclusion_sha256"],
        }
        if paired.setdefault(row["seed"], pairing) != pairing:
            raise ValueError(
                "priority comparison lacks paired initializations/inputs/batches"
            )
        references.append(evidence)
    return {
        "comparison": _reference(path),
        "runs": references,
        "original_code_sha256": source_code,
        "original_benchmark_sha256": source_configuration,
        "input_bindings": source_inputs,
    }


def _priority_input_compatibility(prior, current, definition):
    declaration = None
    if prior != current:
        if {k: v for k, v in prior.items() if k != "code_sha256"} != {
            k: v for k, v in current.items() if k != "code_sha256"
        }:
            raise ValueError(
                "priority comparison inputs differ from the campaign profiles"
            )
        matches = [
            row
            for row in definition.get("archival_input_compatibility", [])
            if row["prior_motionbert_code_sha256"] == prior.get("code_sha256")
            and row["profile_motionbert_code_sha256"] == current.get("code_sha256")
        ]
        if len(matches) != 1:
            raise ValueError(
                "priority input code change lacks an exact archival declaration"
            )
        declaration = matches[0]
    return {
        "prior_input_bindings": prior,
        "profile_input_bindings": current,
        "prior_input_sha256": digest(prior),
        "profile_input_sha256": digest(current),
        "compatibility_declaration": declaration,
    }


def _profile_evidence(directories, config):
    profiles = {}
    forecast = {}
    common_inputs = None
    for value in directories:
        path = artifact_path(value)
        manifest = verify_run(path)
        identity = manifest["identity"]
        method = identity["method"]
        if not identity.get("inputs") or (
            common_inputs is not None and common_inputs != identity["inputs"]
        ):
            raise ValueError(
                "capacity profiles must bind the same verified input bundle"
            )
        common_inputs = identity["inputs"]
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
            or telemetry.get("encoder_backward_steps") != identity["steps"]
            or not history
            or any(
                not isinstance(row.get("seconds"), (int, float))
                or not math.isfinite(row["seconds"])
                or row["seconds"] <= 0
                for row in history
            )
        ):
            raise ValueError(
                "campaign feasibility requires actual allocated GPU evidence"
            )
        from pose_embed.benchmark.profiling import validate_retrieval_profile

        validate_retrieval_profile(
            telemetry.get("retrieval_profile"), identity, load_methods()[method]
        )
        mean_step_seconds = sum(row["seconds"] for row in history) / len(history)
        profiles[method] = _reference(path / "run-manifest.json")
        forecast[method] = {
            "profile_mean_update_seconds": mean_step_seconds,
            "bounded_retrieval_profile": telemetry["retrieval_profile"],
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


def declare_campaign(
    *, config_path, run_root, profiles, prior_trial_roots, priority_comparison
):
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
    if any(
        root.is_relative_to(artifact_path(prior))
        or artifact_path(prior).is_relative_to(root)
        for prior in prior_trial_roots
    ):
        raise ValueError("campaign and prior trial directories must be disjoint")
    if root.exists() and any(root.iterdir()):
        raise ValueError("campaign needs a fresh empty trial directory")
    definition = read_json(DEFINITION)
    from pose_embed.benchmark.profiling import PROFILE_RETRIEVAL

    if definition.get("profile_retrieval") != PROFILE_RETRIEVAL:
        raise ValueError(
            "campaign retrieval profile policy differs from implementation"
        )
    if definition["candidates"] != [
        {"candidate_id": key, "learning_rate_scale": value}
        for key, value in CANDIDATES.items()
    ]:
        raise ValueError(
            "candidate grid differs from the declared three-candidate design"
        )
    profile_refs, forecast = _profile_evidence(profiles, config)
    prior = _prior_trials(prior_trial_roots)
    priority = verify_priority_comparison(priority_comparison, prior_trial_roots)
    first_profile = read_json(_verify_reference(next(iter(profile_refs.values()))))
    input_compatibility = _priority_input_compatibility(
        priority["input_bindings"], first_profile["identity"]["inputs"], definition
    )
    if not prior:
        raise ValueError(
            "record the prioritized engineering pilots before the main campaign"
        )
    _check_prior_coverage(prior_trial_roots, profiles, root, _timestamp(now()))
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "kind": "development_campaign",
        "created_at": now(),
        "definition": definition,
        "definition_sha256": sha256_file(DEFINITION),
        "code_sha256": code_digest(),
        "configuration": config.model_dump(mode="json"),
        "base_configuration_path": str(Path(config_path).resolve()),
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
        "prior_summaries": _prior_summaries(prior_trial_roots),
        "priority_comparison": priority,
        "priority_input_compatibility": input_compatibility,
    }
    write_immutable_json(campaign_path(), payload)
    return payload


def validate_campaign(config, *, verify_evidence=True):
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
    if load_benchmark(payload["base_configuration_path"]) != config:
        raise ValueError("campaign source configuration changed")
    timestamp = datetime.fromisoformat(payload["created_at"])
    if timestamp.tzinfo is None or timestamp > datetime.fromisoformat(now()):
        raise ValueError("campaign declaration timestamp is invalid")
    if not verify_evidence:
        return payload
    refs = payload.get("profiles", {})
    profiles, forecast = _profile_evidence(
        [_verify_reference(v).parent for v in refs.values()], config
    )
    if profiles != refs or forecast != payload.get("resource_forecast"):
        raise ValueError("campaign feasibility evidence changed")
    roots = [artifact_path(artifact_root() / p) for p in payload["prior_trial_roots"]]
    _check_prior_coverage(
        roots,
        [_verify_reference(ref).parent for ref in refs.values()],
        artifact_path(artifact_root() / payload["run_root"]),
        timestamp,
    )
    if (
        _prior_trials(roots) != payload["prior_trials"]
        or _prior_summaries(roots) != payload["prior_summaries"]
    ):
        raise ValueError("prior trial inventory changed or was omitted")
    for trial in payload["prior_trials"]:
        for reference in trial.values():
            _verify_reference(reference)
    priority = payload["priority_comparison"]
    if (
        verify_priority_comparison(_verify_reference(priority["comparison"]), roots)
        != priority
    ):
        raise ValueError("priority comparison evidence changed")
    first_profile = read_json(_verify_reference(next(iter(refs.values()))))
    if _priority_input_compatibility(
        priority["input_bindings"],
        first_profile["identity"]["inputs"],
        payload["definition"],
    ) != payload.get("priority_input_compatibility"):
        raise ValueError("archival input compatibility proof changed")
    for reference in refs.values():
        profile = read_json(_verify_reference(reference))
        if _timestamp(profile["completed_at"]) > timestamp:
            raise ValueError("capacity profile completed after campaign declaration")
    return payload


def training_binding(config, candidate, output_dir):
    declaration = validate_campaign(config, verify_evidence=False)
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
        "campaign_base_config_path": declaration["base_configuration_path"],
    }


def review_failure(directory, *, category, reason):
    """Add an operational classification without editing the original outcome."""
    require_unopened()
    directory = artifact_path(directory)
    outcome_path = directory / "outcome.json"
    if not outcome_path.exists():
        if (
            category != "process_interruption"
            or len(reason.strip()) < 20
            or not (directory / "attempt.json").is_file()
            or (directory / "segment-manifest.json").exists()
            or (directory / "run-manifest.json").exists()
        ):
            raise ValueError(
                "an unfinished process needs an explicit interruption attestation"
            )
        write_immutable_json(
            outcome_path,
            {
                "status": "failed",
                "completed_at": now(),
                "error_type": "ResearcherRecordedInterruption",
                "error": reason.strip(),
                "origin": "researcher_confirmed_process_termination",
            },
        )
    outcome = read_json(outcome_path)
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


def _audited_failure(directory):
    outcome = read_json(directory / "outcome.json")
    review = read_json(directory / "failure-review.json")
    if (
        outcome.get("status") != "failed"
        or review.get("outcome_sha256") != sha256_file(directory / "outcome.json")
        or review.get("category")
        not in {"gpu_allocation", "preemption", "filesystem", "process_interruption"}
        or len(review.get("reason", "").strip()) < 20
        or _timestamp(review["created_at"]) < _timestamp(outcome["completed_at"])
    ):
        raise ValueError("failure requires a valid immutable operational review")
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
        raise ValueError("numerical instability cannot be hidden by retries")
    return {
        "attempt": _reference(directory / "attempt.json"),
        "outcome": _reference(directory / "outcome.json"),
        "review": _reference(directory / "failure-review.json"),
    }


def audit_trials(declaration, run_dirs):
    """Selection must account for every attempt, not a favorable subset."""
    root = artifact_path(artifact_root() / declaration["run_root"])
    successes, ledger = set(), []
    for attempt in sorted(root.rglob("attempt.json")):
        if (
            attempt.parent.parent.name == "segments"
            and (attempt.parents[2] / "attempt.json").is_file()
        ):
            continue
        directory = attempt.parent
        payload = read_json(attempt)
        identity = payload["identity"]
        if (
            identity.get("method") not in declaration["configuration"]["final_methods"]
            or identity.get("seed")
            not in declaration["configuration"]["training"]["seeds"]
            or identity.get("stage") != "development"
            or identity.get("campaign_sha256") != sha256_file(campaign_path())
            or identity.get("candidate") not in CANDIDATES
        ):
            raise ValueError("undeclared attempt in campaign trial directory")
        if datetime.fromisoformat(payload["started_at"]) < datetime.fromisoformat(
            declaration["created_at"]
        ):
            raise ValueError("candidate started before its trial grid was declared")
        validate_run_binding(
            identity,
            BenchmarkConfig.model_validate(identity["configuration"]),
            directory,
        )
        outcome = read_json(directory / "outcome.json")
        entry = {
            "attempt": _reference(attempt),
            "outcome": _reference(directory / "outcome.json"),
        }
        if outcome.get("status") == "succeeded":
            successes.add(directory.resolve())
        elif outcome.get("status") == "failed":
            entry.update(_audited_failure(directory))
        else:
            raise ValueError("campaign has unfinished attempts")
        entry["evidence"] = _trial_evidence(directory)
        entry["segments"] = []
        for segment_attempt in sorted((directory / "segments").glob("*/attempt.json")):
            segment = segment_attempt.parent
            sealed = segment / "segment-manifest.json"
            failed = segment / "outcome.json"
            if sealed.is_file() and not failed.exists():
                if read_json(sealed).get("status") not in {"resumable", "complete"}:
                    raise ValueError("sealed segment has an invalid operational status")
                entry["segments"].append(_trial_evidence(segment))
            elif failed.is_file() and not sealed.exists():
                entry["segments"].append(_audited_failure(segment))
            else:
                raise ValueError(
                    "campaign has unfinished or contradictory segment attempts"
                )

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
        "campaign_base_config_path": declaration["base_configuration_path"],
        "selection_rule": declaration["definition"]["selection_rule"],
        "runs": [
            row | {"candidate": key}
            for key, value in contents.items()
            for row in value["runs"]
        ],
    }, max(completed)


def selected_config(config, selection, method):
    chosen = selection["methods"][method]
    candidate = chosen.get("candidate")
    effective = candidate_config(config, candidate)
    if chosen.get("configuration_sha256") != digest(effective.model_dump(mode="json")):
        raise ValueError("selected candidate configuration hash differs")
    return effective


def validate_run_binding(identity, config, directory):
    if "candidate" not in identity and "campaign_sha256" not in identity:
        return
    payload = read_json(campaign_path())
    base = BenchmarkConfig.model_validate(payload["configuration"])
    validate_campaign(base, verify_evidence=False)
    if (
        identity.get("campaign_base_config_path")
        != payload.get("base_configuration_path")
        or load_benchmark(identity["campaign_base_config_path"]) != base
        or identity.get("campaign_sha256") != sha256_file(campaign_path())
        or identity.get("stage") not in {"development", "final"}
        or config != candidate_config(base, identity.get("candidate"))
    ):
        raise ValueError("run candidate differs from its declared campaign")
    root = artifact_path(artifact_root() / payload["run_root"])
    directory = artifact_path(directory)
    if identity["stage"] == "development" and (
        directory == root or not directory.is_relative_to(root)
    ):
        raise ValueError("development candidate is outside campaign directory")
    attempt = read_json(directory / "attempt.json")
    if _timestamp(attempt["started_at"]) < _timestamp(payload["created_at"]):
        raise ValueError("candidate attempt predates campaign declaration")
    if (
        Path(identity["input_paths"]["configuration"]).resolve()
        != directory / "effective-configuration.json"
    ):
        raise ValueError("candidate must preserve its effective configuration")
