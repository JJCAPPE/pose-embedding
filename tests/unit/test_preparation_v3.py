from types import SimpleNamespace

import pytest
import yaml

from pose_embed.config import load_protocol
from pose_embed.motionbert_features import extraction_condition
from pose_embed.preparation_v3 import (
    auxiliary_annotations,
    auxiliary_preprocessing_digest,
    prepare_v3,
    rebind_v3_manifests,
)
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file


class ForbiddenNovelAnnotation:
    def __getitem__(self, key):
        pytest.fail("packaging inspected a novel annotation")


def test_packaging_never_inspects_novel_annotations():
    auxiliary = {"frame_dir": "S001C001P001R001A003", "label": 2}
    inventory = [
        SimpleNamespace(action=1, annotation_index=0, sample_id="S001C001P001R001A001"),
        SimpleNamespace(action=3, annotation_index=1, sample_id=auxiliary["frame_dir"]),
    ]
    result = auxiliary_annotations(
        {"annotations": [ForbiddenNovelAnnotation(), auxiliary]}, inventory, {1}
    )
    assert result == {1: auxiliary}


def test_auxiliary_packaging_rejects_wrong_identity():
    inventory = [
        SimpleNamespace(action=3, annotation_index=0, sample_id="S001C001P001R001A003")
    ]
    with pytest.raises(ValueError, match="identity"):
        auxiliary_annotations(
            {"annotations": [{"frame_dir": "S001C001P001R001A001", "label": 0}]},
            inventory,
            {1},
        )


@pytest.mark.parametrize(
    "role,split,family,severity",
    [
        ("training", "development_train", "coordinate_jitter", 0.01),
        ("gallery_clean", "development_validation", "joint_mask", 3),
        ("query_corrupted", "development_validation", "frame_mask", 12),
        ("query_corrupted", "development_validation", None, 0),
        ("query_clean", "novel_query_primary", None, 0),
    ],
)
def test_invalid_v3_extraction_roles_and_conditions_fail_before_input_loading(
    role, split, family, severity
):
    protocol = load_protocol("configs/protocol.v3.yaml")
    with pytest.raises(ValueError):
        extraction_condition(
            protocol, role=role, split=split, family=family, severity=severity
        )


def test_v3_corrupted_development_is_explicitly_authorized_condition():
    protocol = load_protocol("configs/protocol.v3.yaml")
    assert (
        extraction_condition(
            protocol,
            role="query_corrupted",
            split="development_validation",
            family="frame_mask",
            severity=25,
        )
        == "frame_mask:25"
    )


def test_fallback_preprocessing_hash_is_independent_of_later_binding():
    protocol = load_protocol("configs/protocol.v3.yaml")
    assert auxiliary_preprocessing_digest(protocol) == auxiliary_preprocessing_digest(
        protocol.model_copy(update={"preparation": object()})
    )


def test_preparation_rejects_unadopted_historical_protocol_before_loading_inputs(
    tmp_path, monkeypatch
):
    historical = load_protocol("configs/protocol.v1.yaml").model_dump(mode="json")
    historical["title"] = "Unadopted alternate protocol"
    path = tmp_path / "alternate.yaml"
    path.write_text(yaml.safe_dump(historical))
    monkeypatch.setattr(
        "pose_embed.preparation_v3.require_dataset_unopened", lambda **_: None
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.require_clean_repository", lambda: "a" * 40
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.load_motionbert_inputs",
        lambda *_, **__: pytest.fail("unadopted inputs reached source verification"),
    )
    with pytest.raises(ValueError, match="exact adopted historical protocol"):
        prepare_v3.__wrapped__(
            template_path="configs/protocol.v3.yaml",
            historical_protocol_path=path,
            manifest_set_path=tmp_path / "missing.json",
            output_dir=tmp_path / "output",
        )
    assert not (tmp_path / "output").exists()


def test_preparation_audits_actual_inventory_before_deserializing_poses(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "pose_embed.preparation_v3.require_dataset_unopened", lambda **_: None
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.require_clean_repository", lambda: "a" * 40
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.load_motionbert_inputs",
        lambda *_, **__: SimpleNamespace(
            protocol=load_protocol("configs/protocol.v1.yaml"),
            bindings={"source_inventory_sha256": "b" * 64},
        ),
    )

    def mismatched_audit(actual):
        assert actual == "b" * 64
        raise ValueError("external historical audit source inventory mismatch")

    monkeypatch.setattr(
        "pose_embed.preparation_v3.validate_registered_source_inventory",
        mismatched_audit,
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.pickle.load",
        lambda _: pytest.fail("unaudited source was deserialized"),
    )
    with pytest.raises(ValueError, match="audit source inventory mismatch"):
        prepare_v3.__wrapped__(
            template_path="configs/protocol.v3.yaml",
            historical_protocol_path="configs/protocol.v1.yaml",
            manifest_set_path=tmp_path / "missing.json",
            output_dir=tmp_path / "output",
        )


@pytest.mark.parametrize("mutation", ["protocol", "inventory", "identities"])
def test_rebinding_rejects_changed_preparation_before_writing(
    tmp_path, monkeypatch, mutation
):
    import json

    from pose_embed.config_v3 import ProtocolV3Config

    historical = tmp_path / "historical"
    historical.mkdir()
    inventory = historical / "source-inventory.jsonl"
    inventory.write_text("inventory-placeholder")
    preparation = tmp_path / "study-v3" / "preparation"
    preparation.mkdir(parents=True)
    identities = preparation / "identities.json"
    identities.write_text('{"ordered_sample_ids":{}}')
    binding = {"relative_path": "unused.json", "sha256": "a" * 64}
    payload = load_protocol("configs/protocol.v3.yaml").model_dump(mode="json")
    payload.update(
        status="resolved",
        preparation={
            "auxiliary_container": binding,
            "fallback_evidence": binding,
            "fallback_value": 1.0,
            "source_inventory": {
                "relative_path": str(inventory.relative_to(tmp_path)),
                "sha256": sha256_file(inventory),
            },
            "identities": {
                "relative_path": str(identities.relative_to(tmp_path)),
                "sha256": sha256_file(identities),
            },
            "encoder_checkpoint_sha256": "a" * 64,
            "upstream_sha256": {
                key: "a" * 64
                for key in ("upstream_sha256", "config_sha256", "license_sha256")
            },
        },
    )
    protocol = ProtocolV3Config.model_validate(payload)
    protocol_path = preparation / "protocol.v3.yaml"
    protocol_path.write_text(yaml.safe_dump(protocol.model_dump(mode="json")))
    manifest_set = historical / "manifest-set.json"
    original_hash = protocol_digest(load_protocol("configs/protocol.v1.yaml"))
    manifest_set.write_text(
        json.dumps(
            {"protocol_sha256": "b" * 64 if mutation == "protocol" else original_hash}
        )
    )
    if mutation == "inventory":
        inventory.write_text("changed inventory")
    if mutation == "identities":
        identities.write_text("changed identities")
    monkeypatch.setattr(
        "pose_embed.preparation_v3.require_dataset_unopened", lambda **_: None
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.canonical_artifact_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        "pose_embed.preparation_v3.validate_registered_source_inventory",
        lambda _: None,
    )
    with pytest.raises(
        ValueError, match="historical protocol|source inventory|identities"
    ):
        rebind_v3_manifests.__wrapped__(
            protocol_path=protocol_path,
            historical_manifest_set=manifest_set,
            output_dir=tmp_path / "study-v3" / "manifests",
        )
    assert not (tmp_path / "study-v3" / "manifests").exists()


def test_cli_freeze_binds_exact_eight_role_manifests(tmp_path, monkeypatch):
    from pose_embed.protocol_v3 import COUNTS
    from pose_embed.v3_commands import run_preparation_command

    directory = tmp_path / "study-v3" / "manifests"
    (directory / "development").mkdir(parents=True)
    for role in COUNTS:
        parent = (
            directory / "development"
            if role.startswith("development_g") or role == "development_queries"
            else directory
        )
        (parent / (role.replace("_", "-") + ".jsonl")).write_text(role)
    monkeypatch.setattr(
        "pose_embed.v3_commands.canonical_artifact_root", lambda: tmp_path
    )

    def freeze(protocol, *, manifests, recorded_by):
        assert protocol.protocol_id == "protocol-v3"
        assert set(manifests) == set(COUNTS)
        for role, binding in manifests.items():
            path = tmp_path / binding["relative_path"]
            assert path.read_text() == role
            assert sha256_file(path) == binding["sha256"]
        assert recorded_by == "researcher"
        return SimpleNamespace(model_dump=lambda **_: {"verified": True})

    monkeypatch.setattr("pose_embed.protocol_v3.freeze_v3_design", freeze)
    assert run_preparation_command(
        SimpleNamespace(
            operation="freeze-design",
            protocol_config="configs/protocol.v3.yaml",
            manifest_set=directory / "manifest-set.json",
            recorded_by="researcher",
        )
    ) == {"verified": True}
