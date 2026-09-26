"""Full 468-cell campaign gates using explicitly synthetic, hashed evidence.

GPU execution and numerical run validation have separate tests. This fixture
mocks that boundary; no fixture GPU name is presented as measured evidence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import test_benchmark_locks as lock_helpers

from pose_embed.benchmark import campaign, locks
from pose_embed.benchmark.config import benchmark_digest
from pose_embed.benchmark.profiling import PROFILE_RETRIEVAL
from pose_embed.benchmark.retrieval import method_retrieval_policy
from pose_embed.benchmark.runtime import artifact_root, digest, read_json
from pose_embed.provenance import sha256_file

lock_context = lock_helpers.lock_context
REAL_SELECTION = campaign.selection_content


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _manifest(directory, identity, timestamp):
    names = [p.name for p in directory.glob("*.json") if p.name != "run-manifest.json"]
    value = {
        "schema_version": 2,
        "identity": identity,
        "outputs": {name: sha256_file(directory / name) for name in names},
        "completed_at": timestamp,
    }
    _json(directory / "run-manifest.json", value)
    return value


def _rehash(directory):
    value = read_json(directory / "run-manifest.json")
    value["outputs"] = {
        name: sha256_file(directory / name) for name in value["outputs"]
    }
    _json(directory / "run-manifest.json", value)


@pytest.fixture
def declared(lock_context, tmp_path, monkeypatch):
    config, methods = lock_context
    monkeypatch.setattr(campaign, "selection_content", REAL_SELECTION)
    root = artifact_root()
    clock = datetime.now(UTC)
    completed = (clock - timedelta(hours=3)).isoformat()
    declaration_time = (clock - timedelta(hours=2)).isoformat()
    config_path = tmp_path / "base.json"
    _json(config_path, config.model_dump(mode="json"))
    monkeypatch.setattr(campaign, "load_benchmark", lambda _: config)
    monkeypatch.setattr(campaign, "now", lambda: declaration_time)

    def verified(directory):
        value = read_json(Path(directory) / "run-manifest.json")
        for name, hashed in value["outputs"].items():
            if sha256_file(Path(directory) / name) != hashed:
                raise ValueError("fixture evidence changed")
        return value

    monkeypatch.setattr(campaign, "verify_run", verified)
    profiles = []
    for method in config.final_methods:
        directory = root / "profiles" / method
        identity = {
            "method": method,
            "configuration": config.model_dump(mode="json"),
            "stage": "profile",
            "track": "finetune",
            "steps": 3,
            "precision": "float32",
            "profile_retrieval": PROFILE_RETRIEVAL,
            "inputs": {"source": "paired"},
        }
        _json(
            directory / "telemetry.json",
            {
                "environment": {"cuda_device_name": "synthetic-fixture"},
                "peak_allocated_bytes": 1,
                "checkpoint_bytes": 1,
                "encoder_backward_steps": 3,
            },
        )
        _json(directory / "history.json", {"steps": [{"seconds": 0.1}] * 3})
        ids = ["S001C001P001R001A001", "S001C001P002R001A001"]
        fields = {
            "embeddings": {
                "shape": [2, methods[method].embedding_dimension],
                "dtype": "float32",
                "bytes": 2 * methods[method].embedding_dimension * 4,
            }
        }
        if method == "diml":
            fields.update(
                local={
                    "shape": [2, 16, 512],
                    "dtype": "float32",
                    "bytes": 2 * 16 * 512 * 4,
                },
                local_mask={"shape": [2, 16], "dtype": "bool", "bytes": 32},
            )
        if method == "proxy_anchor_avsl":
            fields["cam_std"] = {
                "shape": [2, 3, 512],
                "dtype": "float32",
                "bytes": 2 * 3 * 512 * 4,
            }
        total = sum(value["bytes"] for value in fields.values())
        telemetry = read_json(directory / "telemetry.json")
        telemetry["retrieval_profile"] = {
            "contract": PROFILE_RETRIEVAL,
            "sample_count": 2,
            "sample_ids": ids,
            "query_order_sha256": digest(ids),
            "gallery_order_sha256": digest(ids),
            "exclusion_sha256": digest(
                [{"sample_id": value, "excluded": [value]} for value in ids]
            ),
            "policy": method_retrieval_policy(method, methods[method].parameters),
            "encoding_seconds": 0.1,
            "scoring_seconds": 0.1,
            "descriptor_storage": {
                "count": 2,
                "fields": fields,
                "total_bytes": total,
                "bytes_per_sample": total // 2,
            },
        }
        _json(directory / "telemetry.json", telemetry)
        _manifest(directory, identity, completed)
        profiles.append(directory)
    prior = root / "prior"
    rows = []
    for method in ("contrastive", "contextual"):
        directory = prior / method
        identity = {
            "method": method,
            "seed": 7,
            "stage": "development",
            "track": "finetune",
            "scientific_use_allowed": True,
            "benchmark_sha256": "old-config",
            "code_sha256": "a" * 64,
            "inputs": {"source": "paired"},
            "steps": 2,
        }
        _json(
            directory / "attempt.json", {"identity": identity, "started_at": completed}
        )
        _json(
            directory / "outcome.json",
            {"status": "succeeded", "completed_at": completed},
        )
        _json(directory / "telemetry.json", {"encoder_backward_steps": 2})
        _json(
            directory / "initialization.json",
            {"encoder": "paired-encoder", "head": "paired-head"},
        )
        _json(directory / "batch-plan.json", {"steps": [[1], [2]]})
        _json(
            directory / "development-result.json",
            {
                "identity": identity,
                "metrics": {"r_at_1": 0.5},
                "query_order_sha256": "q",
                "exclusion_sha256": "x",
            },
        )
        (directory / "checkpoint.pt").write_bytes(b"synthetic archival checkpoint")
        old_manifest = _manifest(directory, identity, completed)
        old_manifest["outputs"]["checkpoint.pt"] = sha256_file(
            directory / "checkpoint.pt"
        )
        _json(directory / "run-manifest.json", old_manifest)
        rows.append(
            {
                "method": method,
                "seed": 7,
                "metrics": {"r_at_1": 0.5},
                "path": str(directory),
                "run_manifest_sha256": sha256_file(directory / "run-manifest.json"),
            }
        )
    comparison = prior / "priority-comparison.json"
    value = {
        "stage": "development",
        "methods": ["contrastive", "contextual"],
        "seeds": [7],
        "runs": rows,
    }
    _json(comparison, value | {"content_sha256": digest(value)})
    args = dict(
        config_path=config_path,
        run_root=root / "campaign",
        profiles=profiles,
        prior_trial_roots=[prior],
        priority_comparison=comparison,
    )
    declaration = campaign.declare_campaign(**args)
    return config, methods, declaration, args


def _matrix(declared, monkeypatch):
    config, methods, declaration, _ = declared
    root = artifact_root()
    directories = []
    for candidate in campaign.CANDIDATES:
        effective = campaign.candidate_config(config, candidate)
        with monkeypatch.context() as context:
            context.setattr(
                lock_helpers,
                "artifact_root",
                lambda candidate=candidate: root / "campaign" / candidate,
            )
            current = lock_helpers._runs((effective, methods), "development")
        for directory in current:
            value = read_json(directory / "run-manifest.json")
            identity = value["identity"]
            identity.update(
                candidate=candidate,
                campaign_sha256=sha256_file(campaign.campaign_path()),
                campaign_base_config_path=str(declared[3]["config_path"]),
                input_paths={
                    "configuration": str(directory / "effective-configuration.json")
                },
            )
            _json(
                directory / "effective-configuration.json",
                effective.model_dump(mode="json"),
            )
            for filename in ("attempt.json", "development-result.json"):
                body = read_json(directory / filename)
                body["identity"] = identity
                _json(directory / filename, body)
            value["identity"] = identity
            value["outputs"]["effective-configuration.json"] = sha256_file(
                directory / "effective-configuration.json"
            )
            _json(directory / "run-manifest.json", value)
            _rehash(directory)
        directories.extend(current)
    return directories


def test_declaration_requires_all_profiles_and_completed_finetuned_pair(declared):
    config, _, payload, args = declared
    assert payload["required_development_runs"] == 468
    assert set(payload["profiles"]) == set(config.final_methods)
    assert campaign.validate_campaign(config) == payload
    with pytest.raises(ValueError, match="all 26"):
        campaign._profile_evidence(args["profiles"][:-1], config)
    directory = args["profiles"][0]
    telemetry = read_json(directory / "telemetry.json")
    telemetry["environment"] = {}
    _json(directory / "telemetry.json", telemetry)
    _rehash(directory)
    with pytest.raises(ValueError, match="actual allocated GPU"):
        campaign._profile_evidence(args["profiles"], config)


def test_prior_metrics_and_comparison_are_bound(declared):
    config, _, _, args = declared
    directory = args["prior_trial_roots"][0] / "contextual"
    _json(directory / "development-result.json", {"metrics": {"r_at_1": 1}})
    with pytest.raises(ValueError, match="prior trial result"):
        campaign.validate_campaign(config)


def test_runtime_binding_is_cheap_but_rejects_changed_candidate(declared, monkeypatch):
    config, _, _, _ = declared
    directory = artifact_root() / "campaign" / "half" / "contrastive"
    effective, binding = campaign.training_binding(config, "half", directory)
    assert effective.training.learning_rate_scale == 0.5
    monkeypatch.setattr(
        campaign,
        "_profile_evidence",
        lambda *_: pytest.fail("recursive profile validation"),
    )
    again, _ = campaign.training_binding(config, "half", directory)
    assert again == effective
    identity = binding | {
        "stage": "development",
        "input_paths": {
            "configuration": str(directory / "effective-configuration.json")
        },
    }
    _json(
        directory / "attempt.json",
        {"identity": identity, "started_at": datetime.now(UTC).isoformat()},
    )
    campaign.validate_run_binding(identity, effective, directory)
    with pytest.raises(ValueError, match="declared campaign"):
        campaign.validate_run_binding(identity, config, directory)
    with pytest.raises(ValueError, match="inside"):
        campaign.training_binding(config, "half", artifact_root() / "outside")


def test_complete_campaign_selects_all_candidates_and_locks_winner_configs(
    declared, monkeypatch
):
    config, methods, _, _ = declared
    directories = _matrix(declared, monkeypatch)
    # Only half/contrastive improves; other methods tie and retain baseline.
    for directory in directories:
        identity = read_json(directory / "run-manifest.json")["identity"]
        if identity["candidate"] == "half" and identity["method"] == "contrastive":
            history = read_json(directory / "history.json")
            history["steps"][0]["validation"]["r_at_1"] = 0.9
            _json(directory / "history.json", history)
            _rehash(directory)
    selected = locks.create_selection(directories)
    assert len(selected["runs"]) == 468 and len(selected["trial_ledger"]) == 468
    assert selected["methods"]["contrastive"]["candidate"] == "half"
    assert selected["methods"]["contrastive"]["selected_steps"] == 1
    assert selected["methods"]["contextual"]["candidate"] == "baseline"
    assert (
        campaign.selected_config(
            config, selected, "contrastive"
        ).training.learning_rate_scale
        == 0.5
    )
    assert locks.validate_selection() == selected
    # The final gate validates the winner-specific config for every method.
    finals = lock_helpers._runs((config, methods), "final", selection=selected)
    for directory in finals:
        value = read_json(directory / "run-manifest.json")
        identity = value["identity"]
        method = identity["method"]
        effective = campaign.selected_config(config, selected, method)
        identity.update(
            candidate=selected["methods"][method]["candidate"],
            configuration=effective.model_dump(mode="json"),
            benchmark_sha256=benchmark_digest(effective),
        )
        body = read_json(directory / "attempt.json")
        body["identity"] = identity
        _json(directory / "attempt.json", body)
        value["identity"] = identity
        _json(directory / "run-manifest.json", value)
        _rehash(directory)
    final = locks.lock_final_runs(finals)
    assert len(final["runs"]) == 156
    assert locks.validate_final_runs() == final


@pytest.mark.parametrize(
    "problem", ["missing", "initialization", "policy", "predeclaration", "duplicate"]
)
def test_complete_campaign_rejects_incomplete_or_unpaired_trials(
    declared, monkeypatch, problem
):
    config, methods, _, _ = declared
    directories = _matrix(declared, monkeypatch)
    if problem == "missing":
        directories = directories[:-1]
    elif problem == "duplicate":
        directories.append(directories[0])
    elif problem == "initialization":
        _json(
            directories[-1] / "initialization.json",
            {"encoder": "changed", "head": "changed"},
        )
        _rehash(directories[-1])
    elif problem == "policy":
        value = read_json(directories[-1] / "development-result.json")
        value["policy"]["exclusion"] = "none"
        _json(directories[-1] / "development-result.json", value)
        _rehash(directories[-1])
    else:
        value = read_json(directories[-1] / "attempt.json")
        value["started_at"] = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        _json(directories[-1] / "attempt.json", value)
        _rehash(directories[-1])
    with pytest.raises(ValueError):
        campaign.selection_content(
            directories, config, methods, locks._candidate_selection_content
        )


def test_operational_retry_is_disclosed_but_numerical_failure_blocks(
    declared, monkeypatch
):
    config, methods, declaration, _ = declared
    directories = _matrix(declared, monkeypatch)
    failed = artifact_root() / "campaign" / "failed-attempt"
    attempt = read_json(directories[0] / "attempt.json")
    attempt["identity"]["input_paths"]["configuration"] = str(
        failed / "effective-configuration.json"
    )
    _json(failed / "attempt.json", attempt)
    earlier = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    _json(
        failed / "outcome.json",
        {"status": "failed", "error": "scheduler preemption", "completed_at": earlier},
    )
    with pytest.raises(FileNotFoundError):
        campaign.audit_trials(declaration, directories)
    monkeypatch.setattr(campaign, "now", lambda: datetime.now(UTC).isoformat())
    campaign.review_failure(
        failed,
        category="preemption",
        reason="Scheduler preempted the job before its next optimizer step.",
    )
    ledger = campaign.audit_trials(declaration, directories)
    assert len(ledger) == 469
    assert any("review" in row for row in ledger)
    _json(
        failed / "outcome.json",
        {"status": "failed", "error": "non-finite gradient", "completed_at": earlier},
    )
    with pytest.raises(ValueError, match="numerical instability"):
        campaign.review_failure(
            failed,
            category="preemption",
            reason="This attempted classification must be rejected automatically.",
        )
    # Forging and rehashing a review does not bypass the instability gate.
    review = read_json(failed / "failure-review.json")
    review["outcome_sha256"] = sha256_file(failed / "outcome.json")
    _json(failed / "failure-review.json", review)
    with pytest.raises(ValueError, match="numerical instability"):
        campaign.audit_trials(declaration, directories)


def test_an_omitted_prior_attempt_cannot_be_hidden_by_narrow_roots(declared):
    config, _, _, _ = declared
    hidden = artifact_root() / "undisclosed-old-pilot"
    _json(
        hidden / "attempt.json",
        {
            "started_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "identity": {},
        },
    )
    _json(hidden / "outcome.json", {"status": "failed"})
    with pytest.raises(ValueError, match="omit an existing"):
        campaign.validate_campaign(config)


def test_declared_gpu_profile_cannot_omit_actual_retrieval_cost(declared):
    config, _, _, args = declared
    directory = args["profiles"][0]
    telemetry = read_json(directory / "telemetry.json")
    telemetry.pop("retrieval_profile")
    _json(directory / "telemetry.json", telemetry)
    _rehash(directory)
    with pytest.raises(ValueError, match="real retrieval"):
        campaign._profile_evidence(args["profiles"], config)


def test_original_priority_checkpoint_and_source_release_are_verified(declared):
    _, _, _, args = declared
    proof = campaign.verify_priority_comparison(args["priority_comparison"])
    assert proof["original_code_sha256"] == "a" * 64
    assert "metrics" not in proof
    directory = args["prior_trial_roots"][0] / "contextual"
    (directory / "checkpoint.pt").write_bytes(b"changed archival checkpoint")
    with pytest.raises(ValueError, match="checkpoint content changed"):
        campaign.verify_priority_comparison(args["priority_comparison"])


def test_base_configuration_source_is_immutable(declared, monkeypatch):
    from pose_embed.benchmark.config import load_benchmark

    config, _, _, args = declared
    monkeypatch.setattr(campaign, "load_benchmark", load_benchmark)
    payload = read_json(args["config_path"])
    payload["training"]["learning_rate"] *= 2
    _json(args["config_path"], payload)
    with pytest.raises(ValueError, match="source configuration changed"):
        campaign.validate_campaign(config, verify_evidence=False)


def test_unfinished_segment_needs_explicit_interruption_attestation(
    declared, monkeypatch
):
    _, _, _, _ = declared
    directory = artifact_root() / "campaign/segment-interruption"
    _json(
        directory / "attempt.json",
        {"started_at": datetime.now(UTC).isoformat(), "identity": {}},
    )
    monkeypatch.setattr(campaign, "now", lambda: datetime.now(UTC).isoformat())
    with pytest.raises(ValueError, match="explicit interruption"):
        campaign.review_failure(
            directory,
            category="filesystem",
            reason="The previous process did not leave a terminal outcome artifact.",
        )
    review = campaign.review_failure(
        directory,
        category="process_interruption",
        reason="Scheduler confirms termination before the segment was sealed.",
    )
    outcome = read_json(directory / "outcome.json")
    assert outcome["status"] == "failed"
    assert outcome["origin"] == "researcher_confirmed_process_termination"
    assert review["outcome_sha256"] == sha256_file(directory / "outcome.json")
    with pytest.raises(ValueError, match="immutable artifact"):
        campaign.review_failure(
            directory,
            category="process_interruption",
            reason="The same interruption must not replace the original attestation.",
        )


def test_archival_input_compatibility_allows_only_exact_declared_code_pair():
    definition = read_json(campaign.DEFINITION)
    exception = definition["archival_input_compatibility"][0]
    prior = {"source": "same", "code_sha256": exception["prior_motionbert_code_sha256"]}
    current = {
        "source": "same",
        "code_sha256": exception["profile_motionbert_code_sha256"],
    }
    proof = campaign._priority_input_compatibility(prior, current, definition)
    assert proof["prior_input_bindings"] == prior
    assert proof["profile_input_bindings"] == current
    assert proof["prior_input_sha256"] != proof["profile_input_sha256"]
    assert proof["compatibility_declaration"] == exception
    with pytest.raises(ValueError, match="inputs differ"):
        campaign._priority_input_compatibility(
            prior, current | {"source": "changed"}, definition
        )
    with pytest.raises(ValueError, match="exact archival"):
        campaign._priority_input_compatibility(
            prior, current | {"code_sha256": "b" * 64}, definition
        )
    with pytest.raises(ValueError, match="exact archival"):
        campaign._priority_input_compatibility(current, prior, definition)


def test_trial_ledger_retains_sealed_and_failed_segments_as_one_cell(
    declared, monkeypatch
):
    config, _, declaration, _ = declared
    directory = artifact_root() / "campaign" / "segmented-cell"
    identity = {
        "method": config.final_methods[0],
        "seed": config.training.seeds[0],
        "stage": "development",
        "candidate": "baseline",
        "campaign_sha256": sha256_file(campaign.campaign_path()),
        "campaign_base_config_path": declaration["base_configuration_path"],
        "configuration": config.model_dump(mode="json"),
        "input_paths": {
            "configuration": str(directory / "effective-configuration.json")
        },
    }
    _json(
        directory / "attempt.json",
        {"identity": identity, "started_at": datetime.now(UTC).isoformat()},
    )
    _json(directory / "outcome.json", {"status": "succeeded"})
    for number, status in ((1, "resumable"), (3, "complete")):
        segment = directory / "segments" / f"{number:06d}"
        _json(segment / "attempt.json", {"identity": identity})
        _json(segment / "segment-manifest.json", {"status": status, "outputs": {}})
    failed = directory / "segments" / "000002"
    _json(failed / "attempt.json", {"identity": identity})
    _json(
        failed / "outcome.json",
        {
            "status": "failed",
            "error": "scheduler preemption",
            "completed_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )
    monkeypatch.setattr(campaign, "now", lambda: datetime.now(UTC).isoformat())
    campaign.review_failure(
        failed,
        category="preemption",
        reason="Scheduler preempted this segment before it could be sealed.",
    )
    ledger = campaign.audit_trials(declaration, [directory])
    assert len(ledger) == 1 and len(ledger[0]["segments"]) == 3
    assert "review" in ledger[0]["segments"][1]
    unfinished = directory / "segments" / "000004"
    _json(unfinished / "attempt.json", {"identity": identity})
    with pytest.raises(ValueError, match="unfinished or contradictory"):
        campaign.audit_trials(declaration, [directory])
