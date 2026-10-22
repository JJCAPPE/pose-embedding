"""Subprocess faults exercise the shared seal, without opening real data."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from pose_embed.dataset_seal import (
    OPENING,
    register_artifact_roots,
    require_dataset_unopened,
)

WORKER = """
import json, os, sys
from pathlib import Path
from pose_embed.dataset_seal import dataset_access, record_dataset_opening
from pose_embed.provenance import write_immutable_json
version, authorization, action = sys.argv[1:]
with dataset_access(opening=True):
    event = record_dataset_opening(
        version=version, authorization=json.loads(authorization)
    )
    print(json.dumps(event, sort_keys=True), flush=True)
    if action == 'hold':
        sys.stdin.readline()
    elif action == 'crash':
        os._exit(71)
    elif action == 'publish':
        root = Path(os.environ['POSE_EMBED_ARTIFACT_ROOT'])
        path = root / 'study-v3/revisions/execution-r1/locks/test-opening.v3.json'
        write_immutable_json(path, {'fixture_only': True, 'dataset_event': event})
"""


@pytest.fixture
def isolated_roots(tmp_path, monkeypatch):
    data, root = tmp_path / "data", tmp_path / "artifacts"
    data.mkdir()
    root.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    register_artifact_roots([])
    return root


def _command(*, authorization="a", version="protocol-v3", action="retry"):
    return [
        sys.executable,
        "-c",
        WORKER,
        version,
        json.dumps({"lock": authorization}),
        action,
    ]


@pytest.mark.parametrize("second_authorization", ["a", "b"])
def test_competing_opening_processes_cannot_publish_two_authorizations(
    isolated_roots, second_authorization
):
    with subprocess.Popen(
        _command(action="hold"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as first:
        try:
            first_event = json.loads(first.stdout.readline())
            before = (isolated_roots / OPENING).read_bytes()
            blocked = subprocess.run(
                _command(authorization=second_authorization),
                capture_output=True,
                text=True,
                timeout=20,
            )
            assert blocked.returncode != 0
            assert "active" in blocked.stderr
            assert (isolated_roots / OPENING).read_bytes() == before
        finally:
            first.communicate("\n", timeout=20)
        assert first.returncode == 0
    retry = subprocess.run(
        _command(authorization=second_authorization),
        capture_output=True,
        text=True,
        timeout=20,
    )
    if second_authorization == "a":
        assert retry.returncode == 0
        assert json.loads(retry.stdout) == first_event
    else:
        assert retry.returncode != 0
        assert "different authorization" in retry.stderr
    assert (isolated_roots / OPENING).read_bytes() == before


def test_crash_after_shared_record_only_recovers_identical_authorization(
    isolated_roots,
):
    crashed = subprocess.run(
        _command(action="crash"), capture_output=True, text=True, timeout=20
    )
    assert crashed.returncode == 71
    original = (isolated_roots / OPENING).read_bytes()
    version_ledger = (
        isolated_roots / "study-v3/revisions/execution-r1/locks/test-opening.v3.json"
    )
    assert not version_ledger.exists()
    with pytest.raises(ValueError, match="test opening"):
        require_dataset_unopened()
    for version, authorization in (("protocol-v1", "a"), ("protocol-v3", "b")):
        refused = subprocess.run(
            _command(version=version, authorization=authorization, action="publish"),
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert refused.returncode != 0
        assert "different authorization" in refused.stderr
        assert not version_ledger.exists()
    recovered = subprocess.run(
        _command(action="publish"), capture_output=True, text=True, timeout=20
    )
    assert recovered.returncode == 0, recovered.stderr
    assert (isolated_roots / OPENING).read_bytes() == original
    assert json.loads(version_ledger.read_text())["dataset_event"] == json.loads(
        original
    )
    assert json.loads(version_ledger.read_text())["fixture_only"] is True
