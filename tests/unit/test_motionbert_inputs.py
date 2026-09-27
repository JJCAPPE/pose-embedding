from __future__ import annotations

import json
from pathlib import Path

import pytest

from pose_embed.data.inventory import inspect_ntu_aggregate, write_manifest_bundle
from pose_embed.motionbert_inputs import load_motionbert_inputs, verify_manifest_bundle
from tests.unit.test_ntu_inventory import (
    _complete_annotations,
    _synthetic_protocol,
    _write_source_files,
)


def _bundle(tmp_path: Path, protocol_path: Path):
    metadata = _write_source_files(tmp_path, _complete_annotations(protocol_path))
    protocol = _synthetic_protocol(protocol_path, metadata)
    inventory = inspect_ntu_aggregate(tmp_path, metadata, protocol)
    bundle = tmp_path / "release"
    write_manifest_bundle(inventory, protocol, bundle)
    return protocol, bundle / "manifest-set.json"


def test_complete_bundle_is_rederived_and_annotations_retained(
    tmp_path: Path, protocol_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, bundle = _bundle(tmp_path, protocol_path)
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.load_protocol", lambda _: protocol
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.motionbert_code_digest", lambda: "a" * 64
    )
    inputs = load_motionbert_inputs(protocol_path, bundle, require_clean=False)
    assert inputs.annotations is not None
    assert len(inputs.annotations) == len(inputs.inventory)
    assert inputs.annotations[0]["frame_dir"] == inputs.inventory[0].sample_id
    assert (
        inputs.bindings["aggregate_sha256"]
        == protocol.dataset.source_contract.aggregate_sha256
    )
    assert len(inputs.manifests["final-train.jsonl"]) == 100


@pytest.mark.parametrize("change", ["hash", "count", "protocol", "subset"])
def test_changed_bundle_fails_closed(
    tmp_path: Path, protocol_path: Path, change: str
) -> None:
    protocol, bundle = _bundle(tmp_path, protocol_path)
    document = json.loads(bundle.read_text())
    if change == "hash":
        document["files"]["final-train.jsonl"]["sha256"] = "0" * 64
    elif change == "count":
        document["files"]["final-train.jsonl"]["records"] = 99
    elif change == "protocol":
        document["protocol_sha256"] = "0" * 64
    else:
        path = bundle.parent / "final-train.jsonl"
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
        from pose_embed.provenance import sha256_file

        document["files"][path.name]["sha256"] = sha256_file(path)
    bundle.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        verify_manifest_bundle(protocol, bundle)


@pytest.mark.parametrize(
    "ledger_name",
    ["locks/test-opening.v1.json", "benchmark-v2/locks/test-opening.json"],
)
def test_opened_test_and_changed_source_fail_before_deserialization(
    tmp_path: Path,
    protocol_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ledger_name: str,
) -> None:
    protocol, bundle = _bundle(tmp_path, protocol_path)
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.load_protocol", lambda _: protocol
    )
    opening = tmp_path / ledger_name
    opening.parent.mkdir(parents=True)
    opening.write_text("{}")
    with pytest.raises(ValueError, match="after novel-test opening"):
        load_motionbert_inputs(protocol_path, bundle, require_clean=False)
    opening.unlink()
    (tmp_path / "ntu120_hrnet.pkl").write_bytes(b"not trusted pickle")
    monkeypatch.setattr(
        "pose_embed.data.inventory.pickle.load",
        lambda _: pytest.fail("changed source must never be deserialized"),
    )
    with pytest.raises(ValueError, match="verified aggregate source"):
        load_motionbert_inputs(protocol_path, bundle, require_clean=False)
