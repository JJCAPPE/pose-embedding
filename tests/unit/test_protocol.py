from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pose_embed.config import (
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.data import ManifestRecord
from pose_embed.protocol import (
    SCIENTIFIC_CODE_PATHS,
    FinalRunSet,
    LockedManifest,
    current_code_hashes,
    derive_core_failure_status,
    evaluation_plan_digest,
    experiment_hyperparameters_digest,
    final_run_set_digest,
    load_evaluation_plan,
    protocol_digest,
    resolve_scientific_paths,
    validate_evaluation_manifests,
    validate_final_run_artifacts,
    validate_locked_manifest,
    verify_protocol,
)
from pose_embed.provenance import sha256_file
from tests.scientific_fixtures import (
    locked_plan,
    locked_run_set,
    materialize_final_run_set,
    write_lock_bundle,
)


def _write_locked_artifacts(
    directory: Path, protocol_sha256: str
) -> tuple[Path, Path, Path]:
    plan = locked_plan()
    run_set = locked_run_set(protocol_sha256, plan)
    plan_path = directory / "evaluation-plan.yaml"
    run_set_path = directory / "final-run-set.json"
    lock_path = directory / "protocol-lock.json"
    plan_path.write_text(json.dumps(plan.model_dump(mode="json")), encoding="utf-8")
    run_set_path.write_text(
        json.dumps(run_set.model_dump(mode="json")), encoding="utf-8"
    )
    approved = datetime(2026, 9, 1, 13, tzinfo=UTC)
    assert plan.source_inventory_manifest is not None
    assert plan.anchor_manifest is not None
    assert plan.official_query_manifest is not None
    assert plan.primary_query_manifest is not None
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
                "locked_at": (approved + timedelta(minutes=1)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return lock_path, plan_path, run_set_path


def test_protocol_has_locked_action_partitions(protocol_path: Path) -> None:
    protocol = load_protocol(protocol_path)

    assert protocol.dataset.novel_actions == tuple(range(1, 116, 6))
    assert protocol.dataset.development_validation_actions == tuple(range(2, 117, 6))
    assert protocol.training.final_training_actions == "all_100_auxiliary_actions"
    assert protocol.training.insufficient_compute_policy == (
        "block_and_require_advisor_approved_amendment_before_test_opening"
    )
    assert protocol.batch.physical_batch_size == 32
    assert protocol.objectives.core == ("contrastive", "supcon", "contextual")


def test_protocol_lock_detects_content_change(
    protocol_path: Path, evaluation_plan_path: Path, tmp_path: Path
) -> None:
    protocol = load_protocol(protocol_path)
    lock_path, locked_plan_path, run_set_path = _write_locked_artifacts(
        tmp_path, protocol_digest(protocol)
    )

    _, digest = verify_protocol(
        protocol_path,
        lock_path=lock_path,
        evaluation_plan_path=locked_plan_path,
        final_run_set_path=run_set_path,
        require_locked=True,
    )
    assert digest == protocol_digest(protocol)

    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    payload["protocol_sha256"] = "0" * 64
    lock_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        verify_protocol(
            protocol_path,
            lock_path=lock_path,
            evaluation_plan_path=locked_plan_path,
            final_run_set_path=run_set_path,
            require_locked=True,
        )


def test_final_operation_cannot_omit_protocol_lock(protocol_path: Path) -> None:
    with pytest.raises(ValueError, match="required"):
        verify_protocol(protocol_path, require_locked=True)


def test_lock_rejects_future_timestamps(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    lock_path, locked_plan_path, run_set_path = _write_locked_artifacts(
        tmp_path, protocol_digest(protocol)
    )

    with pytest.raises(ValueError, match="future"):
        verify_protocol(
            protocol_path,
            lock_path=lock_path,
            evaluation_plan_path=locked_plan_path,
            final_run_set_path=run_set_path,
            require_locked=True,
            now=datetime(2026, 8, 31, tzinfo=UTC),
        )


def test_experiment_configs_are_inside_registered_space(
    protocol_path: Path,
    repository_root: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    for name in ("contrastive", "supcon", "contextual", "multi_similarity"):
        experiment = load_experiment(
            repository_root / "configs" / "experiments" / f"{name}.yaml"
        )
        validate_experiment_against_protocol(experiment, protocol)


def test_scientific_paths_are_fixed_below_absolute_artifact_root(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))

    paths = resolve_scientific_paths(protocol)

    assert paths.protocol_lock == tmp_path / "locks/protocol-lock.v1.json"
    assert paths.evaluation_plan == tmp_path / "locks/evaluation-plan.v1.yaml"
    assert paths.final_run_set == tmp_path / "locks/final-run-set.v1.json"
    assert paths.test_opening_ledger == tmp_path / "locks/test-opening.v1.json"

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", "relative-artifacts")
    with pytest.raises(ValueError, match="absolute"):
        resolve_scientific_paths(protocol)


def test_required_protocol_verification_uses_only_canonical_paths(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    digest = protocol_digest(protocol)
    write_lock_bundle(tmp_path, digest)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))

    _, verified = verify_protocol(protocol_path, require_locked=True)

    assert verified == digest


def test_locked_plan_and_run_set_require_exact_complete_matrices() -> None:
    plan = locked_plan()
    run_set = locked_run_set("f" * 64, plan)
    assert len(run_set.runs) == 9

    invalid = run_set.model_dump(mode="json")
    invalid["runs"] = invalid["runs"][:-1]
    with pytest.raises(ValueError, match="nine"):
        FinalRunSet.model_validate(invalid)


def test_final_manifest_validation_rejects_a_tiny_claimed_source_inventory(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)

    with pytest.raises(ValueError, match="114480"):
        validate_evaluation_manifests(
            protocol,
            locked_plan(),
            tmp_path,
            check_source_files=False,
        )


def test_locked_manifest_requires_exact_hash_count_and_order(tmp_path: Path) -> None:
    manifest = tmp_path / "query.jsonl"
    sample_ids = (
        "S001C001P001R001A001",
        "S002C001P002R001A007",
    )
    manifest.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id, split="novel_query_official"
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )
    binding = LockedManifest(
        relative_path="manifests/query.jsonl",
        sha256=sha256_file(manifest),
        sample_count=2,
        sample_ids=sample_ids,
    )
    assert (
        validate_locked_manifest(
            binding, manifest, expected_split="novel_query_official"
        )
        == sample_ids
    )

    changed_order = binding.model_copy(
        update={"sample_ids": tuple(reversed(sample_ids))}
    )
    with pytest.raises(ValueError, match="identities/count"):
        validate_locked_manifest(changed_order, manifest)


def test_final_run_set_code_hashes_cover_all_scientific_surfaces(
    repository_root: Path,
) -> None:
    hashes = current_code_hashes(repository_root)
    assert set(hashes.model_dump()) == {
        "training",
        "evaluation",
        "sampler",
        "corruptions",
        "analysis",
    }
    assert all(len(value) == 64 for value in hashes.model_dump().values())
    declared_paths = [
        path
        for component_paths in SCIENTIFIC_CODE_PATHS.values()
        for path in component_paths
    ]
    package_root = repository_root / "src/pose_embed"
    expected_paths = {
        path.relative_to(repository_root).as_posix()
        for path in package_root.rglob("*.py")
    }
    assert len(declared_paths) == len(set(declared_paths))
    assert set(declared_paths) == expected_paths


def test_multi_similarity_is_bound_to_one_predeclared_configuration(
    repository_root: Path,
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    config = load_experiment(
        repository_root / "configs/experiments/multi_similarity.yaml"
    )
    assert experiment_hyperparameters_digest(config) == (
        protocol.objectives.stretch.predeclared_hyperparameters_sha256
    )

    paired_seed = config.model_copy(update={"name": "paired-seed-29", "seed": 29})
    validate_experiment_against_protocol(paired_seed, protocol)

    changed_optimizer = paired_seed.model_copy(
        update={"learning_rate": 0.001, "weight_decay": 0.0}
    )
    with pytest.raises(ValueError, match="predeclared Multi-Similarity"):
        validate_experiment_against_protocol(changed_optimizer, protocol)


def test_final_run_artifacts_must_match_locked_files_and_current_code(
    repository_root: Path,
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    run_set = materialize_final_run_set(
        tmp_path,
        repository_root,
        protocol,
    )
    run = run_set.runs[0]
    checkpoint = tmp_path / run.checkpoint_relative_path

    files = validate_final_run_artifacts(
        run_set,
        run,
        tmp_path,
        protocol=protocol,
    )
    assert files["checkpoint"] == checkpoint

    run_manifest = tmp_path / run.run_manifest_relative_path
    original_manifest = run_manifest.read_text(encoding="utf-8")
    run_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "command": "train",
                "configuration": {
                    "experiment": json.loads(original_manifest)["configuration"][
                        "experiment"
                    ]
                },
                "inputs": {str(tmp_path / run.config_relative_path): run.config_sha256},
                "scientific_use_allowed": True,
                "protocol_sha256": run_set.protocol_sha256,
                "initialization_sha256": run.initialization_sha256,
                "outputs": {
                    "checkpoint": run.checkpoint_sha256,
                    "batch_plan": run.batch_plan_sha256,
                },
            }
        ),
        encoding="utf-8",
    )
    run_set_payload = run_set.model_dump(mode="json")
    run_set_payload["runs"][0]["run_manifest_sha256"] = sha256_file(run_manifest)
    incomplete_run_set = FinalRunSet.model_validate(run_set_payload)
    with pytest.raises(ValueError, match="incomplete provenance"):
        validate_final_run_artifacts(
            incomplete_run_set,
            incomplete_run_set.runs[0],
            tmp_path,
            protocol=protocol,
        )
    run_manifest.write_text(original_manifest, encoding="utf-8")

    checkpoint.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checkpoint hash mismatch"):
        validate_final_run_artifacts(
            run_set,
            run,
            tmp_path,
            protocol=protocol,
        )


def test_final_run_rejects_seed_specific_config_semantic_mismatch(
    repository_root: Path,
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    original = materialize_final_run_set(
        tmp_path,
        repository_root,
        protocol,
    )
    payload = original.model_dump(mode="json")
    target = next(
        run
        for run in payload["runs"]
        if (run["method"], run["seed"]) == ("contrastive", 17)
    )
    run_manifest = tmp_path / target["run_manifest_relative_path"]
    manifest_payload = json.loads(run_manifest.read_text(encoding="utf-8"))
    manifest_payload["configuration"]["experiment"]["learning_rate"] = 999
    run_manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
    target["run_manifest_sha256"] = sha256_file(run_manifest)
    run_set = FinalRunSet.model_validate(payload)
    run = next(
        item for item in run_set.runs if (item.method, item.seed) == ("contrastive", 17)
    )

    with pytest.raises(ValueError, match="configuration mismatch"):
        validate_final_run_artifacts(
            run_set,
            run,
            tmp_path,
            protocol=protocol,
        )


def test_core_failure_status_is_derived_from_every_final_training_attempt(
    repository_root: Path,
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    run_set = materialize_final_run_set(tmp_path, repository_root, protocol)
    run_set_path = tmp_path / protocol.test_access.final_run_set_relative_path
    run_set_path.write_text(run_set.model_dump_json(), encoding="utf-8")
    plan = load_evaluation_plan(
        tmp_path / protocol.test_access.evaluation_plan_relative_path
    )
    ledger_path = tmp_path / protocol.test_access.opening_ledger_relative_path
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "event_id": "fixture-opening",
                "protocol_sha256": protocol_digest(protocol),
                "protocol_lock_sha256": "a" * 64,
                "evaluation_plan_sha256": evaluation_plan_digest(plan),
                "final_run_set_sha256": final_run_set_digest(run_set),
                "source_inventory_manifest_sha256": (
                    plan.source_inventory_manifest.sha256
                ),
                "source_file_count": 1,
                "source_files_sha256": "f" * 64,
                "opened_at": "2026-09-02T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))

    complete = derive_core_failure_status(protocol)
    assert complete["attempt_count"] == 9
    assert complete["failed_attempt_count"] == 0
    assert complete["unresolved_failures"] == []

    selected_attempt_path = tmp_path / run_set.runs[0].attempt_relative_path
    failed_dir = tmp_path / "runs/contrastive-7-failed-after-success"
    failed_dir.mkdir()
    failed_attempt = json.loads(selected_attempt_path.read_text(encoding="utf-8"))
    failed_attempt["attempt_id"] = "unresolved-attempt"
    failed_attempt["started_at"] = "2026-08-31T12:03:00+00:00"
    failed_attempt["provenance"]["started_at"] = "2026-08-31T12:03:00+00:00"
    failed_attempt["provenance"]["ended_at"] = "2026-08-31T12:03:01+00:00"
    (failed_dir / "attempt.json").write_text(
        json.dumps(failed_attempt), encoding="utf-8"
    )
    (failed_dir / "outcome.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_id": "unresolved-attempt",
                "status": "failed",
                "ended_at": "2026-08-31T12:04:00+00:00",
                "error_type": "RuntimeError",
                "error_message": "fixture failure",
                "artifacts_written": {},
            }
        ),
        encoding="utf-8",
    )

    incomplete = derive_core_failure_status(protocol)
    assert incomplete["failed_attempt_count"] == 1
    assert incomplete["unresolved_failures"] == [
        "runs/contrastive-7-failed-after-success/attempt.json"
    ]

    post_opening_dir = tmp_path / "runs/contrastive-7-after-opening"
    post_opening_dir.mkdir()
    post_opening_attempt = json.loads(selected_attempt_path.read_text(encoding="utf-8"))
    post_opening_attempt["attempt_id"] = "post-opening-attempt"
    post_opening_attempt["started_at"] = "2026-09-02T00:01:00+00:00"
    post_opening_attempt["provenance"]["started_at"] = "2026-09-02T00:01:00+00:00"
    post_opening_attempt["provenance"]["ended_at"] = "2026-09-02T00:01:01+00:00"
    (post_opening_dir / "attempt.json").write_text(
        json.dumps(post_opening_attempt), encoding="utf-8"
    )
    (post_opening_dir / "outcome.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_id": "post-opening-attempt",
                "status": "success",
                "ended_at": "2026-09-02T00:02:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    violated = derive_core_failure_status(protocol)
    assert violated["attempt_count"] == 11
    assert violated["protocol_violation_count"] == 1
    assert violated["unresolved_failures"] == [
        "runs/contrastive-7-after-opening/attempt.json",
        "runs/contrastive-7-failed-after-success/attempt.json",
    ]
    assert (
        next(
            record
            for record in violated["attempts"]
            if record["attempt_path"] == "runs/contrastive-7-after-opening/attempt.json"
        )["status"]
        == "post_opening_protocol_violation"
    )


def test_lock_templates_match_seed_specific_and_stretch_contracts(
    repository_root: Path,
) -> None:
    run_set = json.loads(
        (repository_root / "configs/final-run-set.template.json").read_text(
            encoding="utf-8"
        )
    )
    for selected in run_set["selected_configs"]:
        assert set(selected) == {"method", "config_id", "hyperparameters_sha256"}
    for run in run_set["runs"]:
        assert run["config_relative_path"].endswith(f"-{run['seed']}.yaml")
        assert f"_{run['seed']}_CONFIG_SHA256" in run["config_sha256"]

    stretch = json.loads(
        (repository_root / "configs/stretch-gates.template.json").read_text(
            encoding="utf-8"
        )
    )
    assert {
        "protocol_sha256",
        "evaluation_plan_sha256",
        "final_run_set_sha256",
        "test_opening_ledger_sha256",
    }.issubset(stretch)
    assert set(stretch["gates"]) == {
        "nine_core_checkpoints_verified",
        "full_core_result_matrix_verified",
        "core_figures_reproducible",
        "no_unresolved_core_failures",
    }
    assert {name: gate["evidence_path"] for name, gate in stretch["gates"].items()} == {
        "nine_core_checkpoints_verified": "final-run-set.v1.json",
        "full_core_result_matrix_verified": "core-report/summary.json",
        "core_figures_reproducible": "core-report/summary.json",
        "no_unresolved_core_failures": "core-report/summary.json",
    }
    assert all(
        not Path(gate["evidence_path"]).is_absolute()
        and ".." not in Path(gate["evidence_path"]).parts
        for gate in stretch["gates"].values()
    )
