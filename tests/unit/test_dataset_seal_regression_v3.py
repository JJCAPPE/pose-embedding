from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from pose_embed.dataset_seal import (
    LEGACY_OPENINGS,
    OPENING,
    REGISTRY,
    REGISTRY_BINDING,
    canonical_artifact_root,
    register_artifact_roots,
    registered_roots,
    require_dataset_unopened,
    require_no_v3_opening,
    validate_registered_source_inventory,
)


@pytest.fixture
def roots(tmp_path, monkeypatch):
    data, root, historical = [tmp_path / name for name in ("data", "root", "old")]
    for path in (data, root, historical):
        path.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    return data, root, historical


def test_omitting_data_root_cannot_forget_historical_opening(roots, monkeypatch):
    _, _, historical = roots
    register_artifact_roots([str(historical)])
    path = historical / LEGACY_OPENINGS[2]
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    monkeypatch.delenv("POSE_EMBED_DATA_ROOT")
    with pytest.raises(ValueError, match="test opening"):
        require_dataset_unopened()


def test_switching_to_historical_root_cannot_hide_registry(roots, monkeypatch):
    _, _, historical = roots
    register_artifact_roots([str(historical)])
    monkeypatch.delenv("POSE_EMBED_DATA_ROOT")
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(historical))
    with pytest.raises(ValueError, match="registered dataset root"):
        canonical_artifact_root()


def test_switching_data_root_is_denied_by_persistent_artifact_binding(
    roots, tmp_path, monkeypatch
):
    _, _, historical = roots
    register_artifact_roots([str(historical)])
    other = tmp_path / "other-data"
    other.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(other))
    with pytest.raises(ValueError, match="data root differs"):
        require_dataset_unopened()


@pytest.mark.parametrize("relative", [LEGACY_OPENINGS[2], OPENING])
def test_dangling_opening_markers_deny_direct_legacy_source_access(roots, relative):
    _, _, historical = roots
    register_artifact_roots([str(historical)])
    path = historical / relative
    path.parent.mkdir(parents=True)
    path.symlink_to(historical / "missing-target")
    with pytest.raises(ValueError):
        require_no_v3_opening()


def test_malformed_common_record_cannot_claim_legacy_authorization(roots):
    _, _, historical = roots
    register_artifact_roots([str(historical)])
    path = historical / OPENING
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"protocol_version": "protocol-v1"}))
    with pytest.raises(ValueError, match="malformed"):
        require_no_v3_opening()


def test_directory_opening_marker_is_unresolved_during_registration(roots):
    _, _, historical = roots
    (historical / OPENING).mkdir(parents=True)
    with pytest.raises(ValueError, match="opening requires investigation"):
        register_artifact_roots([str(historical)])


def test_missing_historical_pointer_fails_closed_and_identical_retry_repairs(roots):
    _, _, historical = roots
    original = register_artifact_roots([str(historical)])
    (historical / REGISTRY_BINDING).unlink()
    with pytest.raises(ValueError, match="registry binding"):
        registered_roots()
    assert register_artifact_roots([str(historical)]) == original
    assert historical.resolve() in registered_roots()


def test_registry_content_mutation_invalidates_every_persistent_pointer(roots):
    data, _, historical = roots
    register_artifact_roots([str(historical)])
    path = data / REGISTRY
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="changed after registration"):
        require_dataset_unopened()


def _audit():
    return {
        "schema_version": 1,
        "status": "sealed",
        "host": "other-authorized-host",
        "source_inventory_sha256": "a" * 64,
        "recorded_at": datetime.now(UTC).isoformat(),
        "roots": [{"path": "/artifacts", "status": "sealed", "readable": True}],
    }


@pytest.mark.parametrize(
    "mutation",
    ["root_unresolved", "unreadable", "relative", "future", "naive", "source", "host"],
)
def test_external_audit_requires_every_root_resolved_and_dated_source_binding(
    roots, tmp_path, mutation
):
    _, _, historical = roots
    document = _audit()
    if mutation == "root_unresolved":
        document["roots"][0]["status"] = "unresolved"
    elif mutation == "unreadable":
        document["roots"][0]["readable"] = False
    elif mutation == "relative":
        document["roots"][0]["path"] = "relative"
    elif mutation == "future":
        document["recorded_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    elif mutation == "naive":
        document["recorded_at"] = "2026-01-01T00:00:00"
    elif mutation == "source":
        del document["source_inventory_sha256"]
    else:
        document["host"] = " "
    audit = tmp_path / "external.json"
    audit.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        register_artifact_roots([str(historical)], external_audits=[str(audit)])


def test_external_observation_must_bind_the_actual_source_and_remain_unchanged(
    roots, tmp_path
):
    _, _, historical = roots
    audit = tmp_path / "external.json"
    document = _audit()
    # Old evidence remains an explicitly dated observation; no fake freshness.
    document["recorded_at"] = "2026-01-01T00:00:00+00:00"
    audit.write_text(json.dumps(document))
    registry = register_artifact_roots([str(historical)], external_audits=[str(audit)])
    assert registry["external_audits"][0]["path"] == str(audit.resolve())
    validate_registered_source_inventory("a" * 64)
    with pytest.raises(ValueError, match="different source"):
        validate_registered_source_inventory("b" * 64)
    audit.write_text(audit.read_text() + "\n")
    with pytest.raises(ValueError, match="audit changed"):
        registered_roots()
