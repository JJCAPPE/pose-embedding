from __future__ import annotations

import json
from pathlib import Path

import pytest

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import register_artifact_roots
from pose_embed.protocol import (
    EvaluationManifestValidation,
    final_run_set_digest,
    protocol_digest,
)
from pose_embed.test_access import open_final_test_once, validate_recorded_test_opening
from tests.scientific_fixtures import materialize_final_run_set, write_lock_bundle


def test_legacy_test_opening_rejects_v2_opening_before_reading_novel_inputs(
    protocol_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = load_protocol(protocol_path)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    ledger = tmp_path / "benchmark-v2/locks/test-opening.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="forbidden after benchmark v2 opening"):
        open_final_test_once(protocol, protocol_sha256=protocol_digest(protocol))
    assert not (tmp_path / "locks/test-opening.v1.json").exists()


def test_test_opening_is_atomic_immutable_and_bound_to_lock_and_plan(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    protocol_sha256 = protocol_digest(protocol)
    lock_path, _, _ = write_lock_bundle(tmp_path, protocol_sha256)
    ledger_path = tmp_path / "locks/test-opening.v1.json"
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    register_artifact_roots([])
    monkeypatch.setattr(
        "pose_embed.test_access.validate_evaluation_manifests",
        lambda *args, **kwargs: EvaluationManifestValidation(
            paths={},
            source_file_count=114480,
            source_files_sha256="a" * 64,
            source_files_verified=kwargs.get("check_source_files", True),
        ),
    )
    validated_runs: list[tuple[str, int]] = []
    monkeypatch.setattr(
        "pose_embed.test_access.validate_final_run_artifacts",
        lambda _run_set, run, *_args, **_kwargs: validated_runs.append(
            (run.method, run.seed)
        ),
    )

    first = open_final_test_once(
        protocol,
        protocol_sha256=protocol_sha256,
    )
    second = open_final_test_once(
        protocol,
        protocol_sha256=protocol_sha256,
    )
    assert second == first
    assert ledger_path.is_file()
    assert first.final_run_set_sha256
    assert len(validated_runs) == 9
    assert validate_recorded_test_opening(protocol) == first
    original_ledger = ledger_path.read_text()
    forged = json.loads(original_ledger)
    forged["evaluation_plan_sha256"] = "f" * 64
    ledger_path.write_text(json.dumps(forged))
    with pytest.raises(ValueError, match="canonical authorization"):
        validate_recorded_test_opening(protocol)
    ledger_path.write_text(original_ledger)
    common_path = tmp_path / "locks/dataset-opening.json"
    original_common = common_path.read_text()
    common_path.unlink()
    with pytest.raises(ValueError, match="dataset opening record"):
        validate_recorded_test_opening(protocol)
    assert not common_path.exists()
    common_path.write_text(original_common)

    lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_payload["recorded_by"] = "Changed"
    lock_path.write_text(json.dumps(lock_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="different protocol lock"):
        open_final_test_once(
            protocol,
            protocol_sha256=protocol_sha256,
        )


def test_initial_opening_rejects_missing_core_artifact_without_writing_ledger(
    repository_root: Path,
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    protocol_sha256 = protocol_digest(protocol)
    lock_path, _, run_set_path = write_lock_bundle(tmp_path, protocol_sha256)
    run_set = materialize_final_run_set(tmp_path, repository_root, protocol)
    run_set_path.write_text(
        json.dumps(run_set.model_dump(mode="json")), encoding="utf-8"
    )
    lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_payload["final_run_set_sha256"] = final_run_set_digest(run_set)
    lock_path.write_text(json.dumps(lock_payload), encoding="utf-8")
    (tmp_path / run_set.runs[0].checkpoint_relative_path).unlink()
    ledger_path = tmp_path / "locks/test-opening.v1.json"
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "pose_embed.test_access.validate_evaluation_manifests",
        lambda *args, **kwargs: EvaluationManifestValidation(
            paths={},
            source_file_count=114480,
            source_files_sha256="a" * 64,
            source_files_verified=kwargs.get("check_source_files", True),
        ),
    )

    with pytest.raises(FileNotFoundError):
        open_final_test_once(protocol, protocol_sha256=protocol_sha256)

    assert not ledger_path.exists()


@pytest.mark.parametrize("crash_after_common", [False, True])
def test_v3_capacity_precedes_opening_and_partial_retry_reuses_receipt(
    protocol_path, tmp_path, monkeypatch, crash_after_common
):
    from datetime import UTC, datetime

    import pose_embed.opening_capacity_v3 as capacity_module
    import pose_embed.test_access as access
    from pose_embed.config_v3 import ArtifactBinding
    from pose_embed.dataset_seal import OPENING
    from pose_embed.provenance import sha256_file, write_immutable_json

    protocol = load_protocol(protocol_path).model_copy(
        update={"protocol_id": "protocol-v3"}
    )
    digest = protocol_digest(protocol)
    write_lock_bundle(tmp_path, digest)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    register_artifact_roots([])
    monkeypatch.setattr(
        "pose_embed.protocol_v3.require_v3_final_authorization", lambda _: None
    )
    monkeypatch.setattr(access, "validate_final_run_artifacts", lambda *a, **k: None)
    monkeypatch.setattr(access, "verify_protocol_lock", lambda *a, **k: digest)
    monkeypatch.setattr(
        access,
        "validate_evaluation_manifests",
        lambda *a, **k: EvaluationManifestValidation(
            paths={},
            source_file_count=114480,
            source_files_sha256="a" * 64,
            source_files_verified=k.get("check_source_files", True),
        ),
    )
    capacity_path = tmp_path / "capacity.json"
    recorded_at = datetime.now(UTC)
    write_immutable_json(capacity_path, {"fixture_only": True})
    binding = ArtifactBinding(
        relative_path="capacity.json", sha256=sha256_file(capacity_path)
    )
    calls = []

    def blocked(*args):
        raise ValueError("current storage reserve is insufficient")

    monkeypatch.setattr(capacity_module, "record_opening_capacity", blocked)
    with pytest.raises(ValueError, match="storage reserve"):
        access.open_final_test_once(protocol, protocol_sha256=digest)
    assert not (tmp_path / OPENING).exists()
    ledger_path = tmp_path / protocol.test_access.opening_ledger_relative_path
    assert not ledger_path.exists()

    def record(*args):
        calls.append(args)
        return binding

    def validate(active, observed, lock_hash):
        assert active == protocol and observed == binding
        assert sha256_file(tmp_path / observed.relative_path) == observed.sha256
        assert len(lock_hash) == 64
        return recorded_at

    monkeypatch.setattr(capacity_module, "record_opening_capacity", record)
    monkeypatch.setattr(capacity_module, "validate_opening_capacity", validate)
    if crash_after_common:

        def crash(path, payload):
            assert path == ledger_path
            raise RuntimeError("injected crash after common event")

        monkeypatch.setattr(access, "write_immutable_json", crash)
        with pytest.raises(RuntimeError, match="injected crash"):
            access.open_final_test_once(protocol, protocol_sha256=digest)
        assert (tmp_path / OPENING).is_file() and not ledger_path.exists()
        monkeypatch.setattr(access, "write_immutable_json", write_immutable_json)
    first = access.open_final_test_once(protocol, protocol_sha256=digest)
    assert first.opening_capacity == binding
    monkeypatch.setattr(capacity_module, "record_opening_capacity", blocked)
    assert access.open_final_test_once(protocol, protocol_sha256=digest) == first
    assert access.validate_recorded_test_opening(protocol) == first
    assert len(calls) == 1
