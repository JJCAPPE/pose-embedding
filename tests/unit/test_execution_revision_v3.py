"""Execution completion cannot mutate an original lock or bypass its test seal."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from pose_embed.config import load_protocol
from pose_embed.config_v3 import ArtifactBinding, ProtocolV3Config
from pose_embed.protocol import protocol_digest
from pose_embed.protocol_v3 import COUNTS, V3DesignLock, validate_execution_revision
from pose_embed.provenance import sha256_file, write_immutable_json


def revision_payload():
    original = load_protocol("configs/protocol.v3.yaml").model_dump(mode="json")
    changed = deepcopy(original)
    for key, value in changed["test_access"].items():
        if key.endswith("_relative_path"):
            changed["test_access"][key] = value.replace(
                "study-v3/locks/", "study-v3/revisions/execution-r1/locks/"
            )
    return original, changed


def test_revision_paths_are_coherent_and_original_digest_unchanged():
    old, new = revision_payload()
    original = load_protocol("configs/protocol.v3.yaml")
    assert protocol_digest(original) == protocol_digest(
        ProtocolV3Config.model_validate(old)
    )
    successor = ProtocolV3Config.model_validate(new)
    assert protocol_digest(successor) != protocol_digest(original)
    new["test_access"]["opening_ledger_relative_path"] = old["test_access"][
        "opening_ledger_relative_path"
    ]
    with pytest.raises(ValueError, match="one declared revision"):
        ProtocolV3Config.model_validate(new)


def test_successor_binds_exact_predecessor_science_and_manifest_bytes(tmp_path):
    original, successor = revision_payload()
    protocol = ProtocolV3Config.model_validate(original)
    path = tmp_path / protocol.test_access.resolved_protocol_relative_path
    write_immutable_json(path, original)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("unchanged identities\n")
    binding = ArtifactBinding(relative_path=manifest.name, sha256=sha256_file(manifest))
    prior = V3DesignLock(
        schema_version=3,
        kind="v3_auxiliary_design_and_pilot_authorization",
        protocol_sha256=protocol_digest(protocol),
        protocol_relative_path=protocol.test_access.resolved_protocol_relative_path,
        recorded_at=datetime.now(UTC) - timedelta(seconds=2),
        recorded_by="fixture",
        manifests={name: binding for name in COUNTS},
        code_sha256={"x": "a" * 64},
        artifact_root_registry_sha256="b" * 64,
        pilot=protocol.training.pilot,
        epochs=20,
        novel_access_authorized=False,
    )
    prior_path = tmp_path / protocol.test_access.design_lock_relative_path
    write_immutable_json(prior_path, prior.model_dump(mode="json"))
    revised = ProtocolV3Config.model_validate(successor)
    lock = prior.model_copy(
        update={
            "protocol_relative_path": (
                revised.test_access.resolved_protocol_relative_path
            ),
            "protocol_sha256": protocol_digest(revised),
            "recorded_at": datetime.now(UTC),
            "predecessor_design": ArtifactBinding(
                relative_path=str(prior_path.relative_to(tmp_path)),
                sha256=sha256_file(prior_path),
            ),
        }
    )
    validate_execution_revision(revised, lock, tmp_path)
    changed = revised.model_copy(update={"title": "Changed scientific record"})
    with pytest.raises(ValueError, match="scientific design"):
        validate_execution_revision(changed, lock, tmp_path)
    manifest.write_text("changed identities\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_execution_revision(revised, lock, tmp_path)


def test_novel_loader_never_deserializes_before_full_opening(monkeypatch, tmp_path):
    from pose_embed.motionbert_inputs import load_motionbert_inputs

    order = []
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.load_protocol",
        lambda _: load_protocol("configs/protocol.v3.yaml"),
    )

    def reject(*args, **kwargs):
        order.append("authorization")
        raise ValueError("missing full final authorization")

    monkeypatch.setattr("pose_embed.test_access.open_final_test_once", reject)
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.require_clean_repository", lambda: "clean"
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.inspect_ntu_aggregate_sources",
        lambda *a, **k: pytest.fail("deserialized novel inputs"),
    )
    with pytest.raises(ValueError, match="missing full final"):
        load_motionbert_inputs("ignored", tmp_path / "manifest-set.json", novel=True)
    assert order == ["authorization"]


def test_new_revision_opening_blocks_all_auxiliary_access(tmp_path, monkeypatch):
    from pose_embed.dataset_seal import (
        register_artifact_roots,
        require_dataset_unopened,
        require_no_v3_opening,
    )

    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    register_artifact_roots([])
    ledger = tmp_path / "study-v3/revisions/execution-r1/locks/test-opening.v3.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="after test opening"):
        require_dataset_unopened()
    with pytest.raises(ValueError, match="after v3 test opening"):
        require_no_v3_opening()


def test_primary_subset_rechecks_ordered_feature_values(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from pose_embed.novel_subset_v3 import validate_primary_subset

    source = tmp_path / "official.npz"
    target = tmp_path / "primary.npz"
    ids = np.array(["a", "b", "c"])
    features = np.arange(12).reshape(3, 4)
    np.savez(source, features=features, labels=np.array([1, 2, 3]), sample_ids=ids)
    np.savez(
        target,
        features=features[[2, 0]],
        labels=np.array([3, 1]),
        sample_ids=ids[[2, 0]],
    )
    from pose_embed.artifacts import sidecar_path_for

    sidecar_path_for(source).write_text("{}")
    original = SimpleNamespace(
        split="novel_query_official",
        method="frozen_encoder_cache",
        condition="clean",
        artifact_sha256=sha256_file(source),
        sample_ids=tuple(ids),
    )
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.validate_feature_artifact", lambda *a, **k: original
    )
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.load_feature_sidecar", lambda *a, **k: original
    )
    subset = SimpleNamespace(
        split="novel_query_primary",
        method="frozen_encoder_cache",
        condition="clean",
        sample_ids=("c", "a"),
        provenance={
            "primary_subset": {
                "source": str(source),
                "source_manifest": "unused",
                "artifact_sha256": sha256_file(source),
                "sidecar_sha256": sha256_file(sidecar_path_for(source)),
            }
        },
    )
    validate_primary_subset(target, subset, None)
    np.savez(
        target,
        features=features[[0, 2]],
        labels=np.array([3, 1]),
        sample_ids=ids[[2, 0]],
    )
    with pytest.raises(ValueError, match="exact ordered official rows"):
        validate_primary_subset(target, subset, None)


def test_dirty_novel_loader_fails_before_recording_opening(monkeypatch, tmp_path):
    from pose_embed.motionbert_inputs import load_motionbert_inputs

    def dirty():
        raise ValueError("dirty release")

    monkeypatch.setattr("pose_embed.motionbert_inputs.require_clean_repository", dirty)
    monkeypatch.setattr(
        "pose_embed.test_access.open_final_test_once",
        lambda *a, **k: pytest.fail("opened from a dirty release"),
    )
    with pytest.raises(ValueError, match="dirty release"):
        load_motionbert_inputs(
            "configs/protocol.v3.yaml", tmp_path / "unused.json", novel=True
        )


def test_engineering_fixture_flag_cannot_bypass_real_cache_seal(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from pose_embed.evaluation.runner import evaluate_files

    monkeypatch.setattr(
        "pose_embed.evaluation.runner.load_feature_sidecar",
        lambda _: SimpleNamespace(scientific_use_allowed=True),
    )

    def sealed(**kwargs):
        raise ValueError("dataset already opened")

    monkeypatch.setattr("pose_embed.dataset_seal.require_dataset_unopened", sealed)
    monkeypatch.setattr(
        "pose_embed.evaluation.runner.validate_feature_artifact",
        lambda *a, **k: pytest.fail("loaded real arrays before seal authorization"),
    )
    with pytest.raises(ValueError, match="dataset already opened"):
        evaluate_files(
            tmp_path / "gallery",
            tmp_path / "query",
            tmp_path / "output",
            mode="engineering",
            protocol_path="configs/protocol.v3.yaml",
            gallery_manifest_path="unused",
            query_manifest_path="unused",
            method="contrastive",
            seed=7,
            condition="joint_dropout:0.1",
            query_definition="development",
            allow_fixture=True,
        )


def test_primary_subset_rejects_primary_source_before_recursive_validation(
    monkeypatch, tmp_path
):
    from types import SimpleNamespace

    from pose_embed.novel_subset_v3 import validate_primary_subset

    source = SimpleNamespace(split="novel_query_primary")
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.load_feature_sidecar", lambda _: source
    )
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.validate_feature_artifact",
        lambda *a, **k: pytest.fail("followed a primary-to-primary reference"),
    )
    subset = SimpleNamespace(
        split="novel_query_primary",
        method="frozen_encoder_cache",
        provenance={
            "primary_subset": {
                "source": str(tmp_path / "other-primary.npz"),
                "source_manifest": "unused",
                "artifact_sha256": "a" * 64,
                "sidecar_sha256": "b" * 64,
            }
        },
    )
    with pytest.raises(ValueError, match="official source binding"):
        validate_primary_subset(tmp_path / "primary.npz", subset, None)
