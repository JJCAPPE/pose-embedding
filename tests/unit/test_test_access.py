from __future__ import annotations

import json
from pathlib import Path

import pytest

from pose_embed.config import load_protocol
from pose_embed.protocol import (
    EvaluationManifestValidation,
    final_run_set_digest,
    protocol_digest,
)
from pose_embed.test_access import open_final_test_once
from tests.scientific_fixtures import materialize_final_run_set, write_lock_bundle


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

    lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_payload["advisor_approved_by"] = "Changed"
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
