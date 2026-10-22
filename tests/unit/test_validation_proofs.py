"""Command-local numerical reuse never replaces artifact or authority validation."""

from __future__ import annotations

import asyncio
import contextvars
import json
import os
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

import pose_embed.artifacts as artifacts
import pose_embed.report as report
import pose_embed.training.runner as training
import pose_embed.validation_proofs as proofs
from pose_embed.config import load_protocol, validate_experiment_against_protocol
from pose_embed.features import apply_trained_head
from pose_embed.provenance import sha256_file
from tests.unit.test_training_v3 import _inputs


@pytest.fixture
def numerical_check(tmp_path):
    dependency = tmp_path / "input.json"
    dependency.write_text('{"x":1}')
    calls = []
    arguments = {
        "enabled": True,
        "files": {dependency: sha256_file(dependency)},
        "metadata": {"protocol": "v3", "stage": "engineering", "epoch": 5},
        "check": lambda: calls.append("checked"),
    }
    return dependency, calls, arguments


def test_nested_scopes_reuse_success_but_independent_commands_start_cold(
    numerical_check,
):
    _, calls, arguments = numerical_check
    with proofs.validation_session() as outer:
        proofs.check_numerical_proof("test", **arguments)
        with proofs.validation_session():
            proofs.check_numerical_proof("test", **arguments)
        with proofs.validation_session(fresh=True):
            proofs.check_numerical_proof("test", **arguments)
        proofs.check_numerical_proof("test", **arguments)
        assert outer.statistics()["hits"] == 2
        assert outer.statistics()["checks"] == 1
        assert outer.statistics()["rehash_seconds"] > 0
    assert not outer.files and not outer.proofs
    with proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
    assert len(calls) == 3
    assert proofs.validation_statistics()["hits"] == 0


@pytest.mark.parametrize("mutation", ["same_size", "missing", "retarget", "rebound"])
def test_changed_dependencies_cannot_reuse_success(numerical_check, mutation, tmp_path):
    path, calls, arguments = numerical_check
    old = path.stat()
    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        if mutation == "missing":
            path.unlink()
        elif mutation == "retarget":
            other = tmp_path / "other.json"
            other.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(other)
        else:
            path.write_text('{"x":2}')
            os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
            if mutation == "rebound":
                arguments["files"][path] = sha256_file(path)
        proofs.check_numerical_proof("test", **arguments)
    assert len(calls) == 1


def test_metadata_and_actual_runtime_changes_recompute(numerical_check, monkeypatch):
    _, calls, arguments = numerical_check
    threads = torch.get_num_threads()
    with proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        arguments["metadata"]["epoch"] = 10
        proofs.check_numerical_proof("test", **arguments)
        monkeypatch.setattr(torch, "get_num_threads", lambda: threads + 1)
        proofs.check_numerical_proof("test", **arguments)
        proofs.check_numerical_proof("test", **arguments)
    assert len(calls) == 3


@pytest.mark.parametrize("mutation", ["file", "metadata", "runtime"])
def test_mid_check_mutation_is_not_published(numerical_check, monkeypatch, mutation):
    path, _, arguments = numerical_check

    def changed():
        if mutation == "file":
            path.write_text('{"x":2}')
        elif mutation == "metadata":
            arguments["metadata"]["epoch"] = 10
        else:
            monkeypatch.setenv("MKL_CBWR", "different")

    arguments["check"] = changed
    with (
        pytest.raises(ValueError, match="changed|verification failed"),
        proofs.validation_session() as session,
    ):
        proofs.check_numerical_proof("test", **arguments)
    assert not session.proofs


def test_failure_and_recursive_check_never_become_proofs(numerical_check):
    _, calls, arguments = numerical_check

    def failure():
        raise ValueError("numeric failure")

    with proofs.validation_session() as session:
        with pytest.raises(ValueError, match="numeric failure"):
            proofs.check_numerical_proof("test", **{**arguments, "check": failure})
        assert not session.proofs
        proofs.check_numerical_proof("test", **arguments)
    assert len(calls) == 1
    arguments["check"] = lambda: proofs.check_numerical_proof("recursive", **arguments)
    with pytest.raises(ValueError, match="recursive"), proofs.validation_session():
        proofs.check_numerical_proof("recursive", **arguments)


def test_publication_recheck_rejects_mutation_after_numeric_success(numerical_check):
    path, _, arguments = numerical_check
    published = []
    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        path.write_text('{"x":2}')
        proofs.verify_validation_proofs()
        published.append(True)
    assert not published


def test_copied_context_cannot_export_proofs_to_thread_or_task(numerical_check):
    _, calls, arguments = numerical_check
    with proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        context = contextvars.copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(
                context.run, proofs.check_numerical_proof, "test", **arguments
            ).result()

        async def task():
            proofs.check_numerical_proof("test", **arguments)

        asyncio.run(task())
        assert proofs.validation_statistics()["hits"] == 0
    assert len(calls) == 3


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork is unavailable")
def test_fork_does_not_inherit_success(numerical_check):
    _, _, arguments = numerical_check
    with proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            try:
                arguments["check"] = lambda: os.write(write_fd, b"checked")
                proofs.check_numerical_proof("test", **arguments)
            finally:
                os.close(write_fd)
                os._exit(0)
        os.close(write_fd)
        assert os.read(read_fd, 32) == b"checked"
        os.close(read_fd)
        assert os.waitpid(pid, 0)[1] == 0


def test_reuse_is_successor_or_explicit_v3_fixture_only():
    protocol = load_protocol("configs/protocol.v3.yaml")
    assert proofs.proof_reuse_allowed(protocol, scientific_use_allowed=False)
    assert not proofs.proof_reuse_allowed(protocol, scientific_use_allowed=True)
    for path, expected in [
        ("study-v3/revisions/execution-r1/locks/protocol.v3.json", False),
        ("wrong/execution-r2/locks/protocol.v3.json", False),
        ("study-v3/revisions/execution-r2/locks/protocol.v3.json", True),
    ]:
        candidate = protocol.model_copy(
            update={
                "test_access": protocol.test_access.model_copy(
                    update={"resolved_protocol_relative_path": path}
                )
            }
        )
        assert (
            proofs.proof_reuse_allowed(candidate, scientific_use_allowed=True)
            is expected
        )
    legacy = load_protocol("configs/protocol.v1.yaml")
    assert not proofs.proof_reuse_allowed(legacy, scientific_use_allowed=False)


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    # Same explicit dimension-only adapter as the CLI software rehearsal.
    # Every artifact remains fixture-only; all numeric/hash validators are real.
    def fixture_dimensions(config, active):
        assert (config.input_dimension, config.embedding_dimension) == (32, 16)
        validate_experiment_against_protocol(
            config.model_copy(
                update={"input_dimension": 8704, "embedding_dimension": 2048}
            ),
            active,
        )

    monkeypatch.setattr(
        training, "validate_experiment_against_protocol", fixture_dimensions
    )
    inputs = _inputs(tmp_path, Path("configs/protocol.v3.yaml").resolve())
    run = tmp_path / "pilot"
    training.train_head(**inputs, output_dir=run)
    return run, inputs


def test_full_pilot_validator_reuses_only_numeric_checks_and_preserves_rng(
    pilot, monkeypatch
):
    run, _ = pilot
    calls = []
    replay = training._replay_pilot_scores
    metadata = training._validate_pilot_scientific_provenance
    guards = []

    def counted(*args):
        calls.append(args[1])
        return replay(*args)

    def guard(*args):
        guards.append(True)
        return metadata(*args)

    monkeypatch.setattr(training, "_replay_pilot_scores", counted)
    monkeypatch.setattr(training, "_validate_pilot_scientific_provenance", guard)
    with proofs.validation_session():
        before = torch.random.get_rng_state()
        first = training.validate_engineering_pilot(run)
        after = torch.random.get_rng_state()
        torch.random.set_rng_state(before)
        second = training.validate_engineering_pilot(run)
        assert torch.equal(torch.random.get_rng_state(), after)
        assert first == second
        assert proofs.validation_statistics()["hits"] == 4
    assert calls == [5, 10, 15, 20]
    assert len(guards) == 2
    with proofs.validation_session():
        training.validate_engineering_pilot(run)
    assert calls == [5, 10, 15, 20] * 2


@pytest.mark.parametrize(
    "name", ["epochs/005/queries.npz", "head.pt", "epoch-005.json"]
)
def test_full_pilot_hit_still_rejects_changed_artifacts(pilot, name):
    run, _ = pilot
    with pytest.raises(ValueError), proofs.validation_session():
        training.validate_engineering_pilot(run)
        path = run / name
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        training.validate_engineering_pilot(run)


def test_pilot_caller_metadata_mutation_replays_and_rejects(pilot):
    run, _ = pilot
    manifest = json.loads((run / "run-manifest.json").read_text())
    record = json.loads((run / "epoch-005.json").read_text())
    with proofs.validation_session():
        training._validate_pilot_scores(run, 5, record, manifest)
        changed = deepcopy(record)
        changed["scores"]["top1"] += 1
        with pytest.raises(ValueError, match="complete scores differ"):
            training._validate_pilot_scores(run, 5, changed, manifest)


def test_projected_feature_reuse_keeps_lineage_guards_fresh(pilot, monkeypatch):
    run, inputs = pilot
    output = run.parent / "gallery-projected.npz"
    apply_trained_head(
        inputs["development_gallery_path"],
        output,
        checkpoint_path=run / "head.pt",
        run_manifest_path=run / "run-manifest.json",
        protocol_path=inputs["protocol_path"],
        manifest_path=inputs["development_gallery_manifest_path"],
        allow_fixture=True,
    )
    calls = []
    original = artifacts._validate_head_projection

    def counted(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(artifacts, "_validate_head_projection", counted)
    arguments = dict(
        protocol=load_protocol(inputs["protocol_path"]),
        manifest_path=inputs["development_gallery_manifest_path"],
        allow_fixture=True,
    )
    with proofs.validation_session():
        artifacts.validate_feature_artifact(output, **arguments)
        artifacts.validate_feature_artifact(output, **arguments)
        assert len(calls) == 1
        # Fixture permission is checked afresh, before an existing numeric proof.
        with pytest.raises(ValueError, match="not approved"):
            artifacts.validate_feature_artifact(
                output, **{**arguments, "allow_fixture": False}
            )
    with proofs.validation_session():
        artifacts.validate_feature_artifact(output, **arguments)
    assert len(calls) == 2


def test_independent_report_recertification_starts_fresh(
    numerical_check, tmp_path, monkeypatch
):
    _, calls, arguments = numerical_check
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "schema_version": 5,
                "analysis_scope": "core_confirmatory",
                "protocol_sha256": "a" * 64,
                "matrix": {},
                "primary_analysis": None,
                "curve_data": None,
                "error_analysis": None,
                "telemetry": None,
                "failures": None,
                "figures": [],
                "results": [],
            }
        )
    )
    monkeypatch.setattr(
        report,
        "resolve_scientific_paths",
        lambda _: SimpleNamespace(
            protocol_lock=None, evaluation_plan=None, final_run_set=None
        ),
    )

    def reach_independent_validation(*args, **kwargs):
        proofs.check_numerical_proof("test", **arguments)
        raise ValueError("stop after independent first check")

    monkeypatch.setattr(report, "verify_protocol", reach_independent_validation)
    with proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)
        with pytest.raises(ValueError, match="independent first"):
            report.validate_core_report_summary(summary, "configs/protocol.v3.yaml")
        proofs.check_numerical_proof("test", **arguments)
    assert len(calls) == 2


def test_mutable_results_are_never_stored(numerical_check):
    _, _, arguments = numerical_check
    with proofs.validation_session() as session:
        with pytest.raises(ValueError, match="must not return mutable"):
            proofs.check_numerical_proof(
                "test", **{**arguments, "check": lambda: {"mutable": []}}
            )
        assert not session.proofs


def _projected(pilot):
    run, inputs = pilot
    output = run.parent / "projected.npz"
    arguments = {
        "checkpoint_path": run / "head.pt",
        "run_manifest_path": run / "run-manifest.json",
        "protocol_path": inputs["protocol_path"],
        "manifest_path": inputs["development_gallery_manifest_path"],
        "allow_fixture": True,
    }
    apply_trained_head(inputs["development_gallery_path"], output, **arguments)
    validation = {
        "protocol": load_protocol(inputs["protocol_path"]),
        "manifest_path": inputs["development_gallery_manifest_path"],
        "allow_fixture": True,
    }
    return output, arguments, validation


@pytest.mark.parametrize("dependency", ["base", "sidecar"])
def test_projected_feature_hit_rejects_changed_transitive_base(pilot, dependency):
    _, inputs = pilot
    output, _, validation = _projected(pilot)
    with pytest.raises(ValueError), proofs.validation_session():
        artifacts.validate_feature_artifact(output, **validation)
        artifacts.validate_feature_artifact(output, **validation)
        base = inputs["development_gallery_path"]
        path = base if dependency == "base" else artifacts.sidecar_path_for(base)
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        artifacts.validate_feature_artifact(output, **validation)


@pytest.mark.parametrize("point", ["before_npz", "before_sidecar"])
def test_feature_producer_cannot_publish_sidecar_after_dependency_mutation(
    pilot, monkeypatch, point
):
    import pose_embed.features as features

    run, inputs = pilot
    output, arguments, validation = _projected(pilot)
    destination = run.parent / "new-projection.npz"
    head = run / "head.pt"

    def corrupt():
        data = head.read_bytes()
        head.write_bytes(bytes([data[0] ^ 1]) + data[1:])

    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        artifacts.validate_feature_artifact(output, **validation)
        if point == "before_npz":
            original = features.functional.linear

            def mutate_after_projection(*args, **kwargs):
                result = original(*args, **kwargs)
                corrupt()
                return result

            monkeypatch.setattr(features.functional, "linear", mutate_after_projection)
        else:
            original = features.FeatureSidecar

            def mutate_before_sidecar(*args, **kwargs):
                result = original(*args, **kwargs)
                corrupt()
                return result

            monkeypatch.setattr(features, "FeatureSidecar", mutate_before_sidecar)
        apply_trained_head(inputs["development_gallery_path"], destination, **arguments)
    assert not artifacts.sidecar_path_for(destination).exists()
    assert destination.exists() is (point == "before_sidecar")


def test_historical_fixture_validator_remains_cold(tmp_path, monkeypatch):
    inputs = _inputs(tmp_path, Path("configs/protocol.v1.yaml").resolve())
    run = tmp_path / "pilot"
    training.train_head(**inputs, output_dir=run)
    original = training._replay_pilot_scores
    calls = []

    def replay(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(training, "_replay_pilot_scores", replay)
    with proofs.validation_session():
        training.validate_engineering_pilot(run)
        training.validate_engineering_pilot(run)
        assert proofs.validation_statistics()["hits"] == 0
    assert len(calls) == 8


@pytest.mark.parametrize("mutation", ["source", "lock", "design", "protocol"])
def test_scientific_proof_commits_complete_design_sources(
    tmp_path, monkeypatch, mutation
):
    from datetime import UTC, datetime

    from pose_embed.protocol import protocol_digest
    from pose_embed.protocol_v3 import COUNTS, V3DesignLock

    repository = tmp_path / "repository"
    repository.mkdir()
    source, lock = repository / "model.py", repository / "uv.lock"
    source.write_text("model = 1\n")
    lock.write_text("locked\n")
    monkeypatch.setattr(proofs, "_REPOSITORY", repository)
    root = tmp_path / "artifacts"
    root.mkdir()
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    protocol = load_protocol("configs/protocol.v3.yaml")
    access = protocol.test_access.model_dump()
    for key, value in access.items():
        if key.endswith("relative_path"):
            access[key] = value.replace(
                "study-v3/locks", "study-v3/revisions/execution-r2/locks"
            )
    protocol = protocol.model_copy(
        update={"test_access": type(protocol.test_access).model_validate(access)}
    )
    protocol_path = root / protocol.test_access.resolved_protocol_relative_path
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text(protocol.model_dump_json())
    binding = {"relative_path": "fixture-only", "sha256": "a" * 64}
    design = V3DesignLock(
        schema_version=3,
        kind="v3_auxiliary_design_and_pilot_authorization",
        protocol_sha256=protocol_digest(protocol),
        protocol_relative_path=protocol.test_access.resolved_protocol_relative_path,
        predecessor_design=binding,
        recorded_at=datetime.now(UTC),
        recorded_by="isolated metadata fixture",
        manifests={name: binding for name in COUNTS},
        code_sha256={"model.py": sha256_file(source), "uv.lock": sha256_file(lock)},
        artifact_root_registry_sha256="b" * 64,
        pilot=protocol.training.pilot,
        epochs=20,
        novel_access_authorized=False,
    )
    design_path = root / protocol.test_access.design_lock_relative_path
    design_path.write_text(design.model_dump_json())
    files = proofs.proof_source_bindings(protocol, scientific_use_allowed=True)
    assert set(files) == {
        str(value.resolve()) for value in (source, lock, design_path, protocol_path)
    }
    chosen = {
        "source": source,
        "lock": lock,
        "design": design_path,
        "protocol": protocol_path,
    }[mutation]
    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        proofs.check_numerical_proof(
            "fixture-only-source-proof",
            enabled=True,
            files=files,
            metadata={},
            check=lambda: None,
        )
        chosen.write_text(chosen.read_text() + " ")
        proofs.verify_validation_proofs()


@pytest.mark.parametrize("island", ["pilot", "projection"])
def test_locked_source_hash_cannot_be_overwritten_by_observed_hash(
    pilot, monkeypatch, island
):
    run, _ = pilot
    if island == "pilot":
        target = training

        def callback():
            return training.validate_engineering_pilot(run)

    else:
        target = artifacts
        output, _, validation = _projected(pilot)

        def callback():
            return artifacts.validate_feature_artifact(output, **validation)

    monkeypatch.setattr(
        target,
        "proof_source_bindings",
        lambda *args, **kwargs: {str(Path(target.__file__)): "0" * 64},
    )
    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        callback()


def test_locked_proof_implementation_hash_wins(numerical_check):
    _, _, arguments = numerical_check
    arguments["files"][proofs.__file__] = "0" * 64
    with pytest.raises(ValueError, match="dependency"), proofs.validation_session():
        proofs.check_numerical_proof("test", **arguments)


def test_conflicting_normalized_dependency_aliases_cannot_override_expectations(
    numerical_check,
):
    _, _, arguments = numerical_check
    arguments["files"].update(
        {
            proofs.__file__: "0" * 64,
            Path(proofs.__file__): sha256_file(proofs.__file__),
        }
    )
    with (
        pytest.raises(ValueError, match="aliases conflict"),
        proofs.validation_session(),
    ):
        proofs.check_numerical_proof("test", **arguments)
