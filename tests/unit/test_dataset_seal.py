import json
import multiprocessing
import shutil

import pytest

from pose_embed.dataset_seal import (
    OPENING,
    canonical_artifact_root,
    dataset_access,
    record_dataset_opening,
    register_artifact_roots,
    require_dataset_unopened,
)


@pytest.fixture
def roots(tmp_path, monkeypatch):
    data = tmp_path / "data"
    root = tmp_path / "artifacts"
    old = tmp_path / "old"
    for path in (data, root, old):
        path.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    register_artifact_roots([str(old)])
    return data, root, old


@pytest.mark.parametrize(
    "relative",
    [
        "locks/test-opening.v1.json",
        "benchmark-v2/locks/test-opening.json",
        "study-v3/locks/test-opening.v3.json",
        OPENING,
    ],
)
def test_any_historical_opening_blocks_auxiliary(roots, relative):
    _, _, old = roots
    path = old / relative
    path.parent.mkdir(parents=True)
    path.write_text("malformed but still an opening")
    with pytest.raises(ValueError, match="test opening"):
        require_dataset_unopened(require_registry=True)


def test_changed_namespace_cannot_bypass_registry(roots, monkeypatch):
    _, root, _ = roots
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root / "different"))
    with pytest.raises(ValueError, match="registered dataset root"):
        canonical_artifact_root()


def test_unresolved_historical_root_blocks(roots):
    _, _, old = roots
    shutil.rmtree(old)
    with pytest.raises(ValueError, match="unresolved"):
        require_dataset_unopened(require_registry=True)


def test_partial_opening_only_retries_identical_authorization(roots):
    _, root, _ = roots
    with dataset_access(opening=True):
        original = record_dataset_opening(
            version="protocol-v3", authorization={"lock": "a"}
        )
    assert json.loads((root / OPENING).read_text()) == original
    with pytest.raises(ValueError, match="test opening"):
        require_dataset_unopened()
    with dataset_access(opening=True):
        assert (
            record_dataset_opening(version="protocol-v3", authorization={"lock": "a"})
            == original
        )
        with pytest.raises(ValueError, match="different authorization"):
            record_dataset_opening(version="protocol-v2", authorization={"lock": "b"})


def _attempt_opening(queue):
    try:
        with dataset_access(opening=True):
            queue.put("opened")
    except ValueError as error:
        queue.put(str(error))


def test_active_auxiliary_process_prevents_opening(roots):
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    with dataset_access():
        process = context.Process(target=_attempt_opening, args=(queue,))
        process.start()
        process.join(10)
        assert process.exitcode == 0
        assert "active" in queue.get(timeout=1)


def test_registry_requires_all_external_audits(tmp_path, monkeypatch):
    root, data = tmp_path / "artifacts", tmp_path / "data"
    root.mkdir()
    data.mkdir()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    audit = tmp_path / "external.json"
    audit.write_text(json.dumps({"status": "unresolved", "roots": ["other-host"]}))
    with pytest.raises(ValueError, match="resolved"):
        register_artifact_roots([], external_audits=[str(audit)])
