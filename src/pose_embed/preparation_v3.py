"""Result-blind auxiliary packaging and exact-identity rebinding for v3."""

from __future__ import annotations

import json
import pickle
import shutil
from pathlib import Path
from typing import Any

import torch
import yaml

from pose_embed.artifacts import sample_order_digest
from pose_embed.config import load_protocol
from pose_embed.data.development import (
    build_development_episode,
    generate_development_episode,
)
from pose_embed.data.motionbert import preprocess_annotation
from pose_embed.dataset_seal import (
    canonical_artifact_root,
    guarded_auxiliary,
    require_dataset_unopened,
    validate_registered_source_inventory,
)
from pose_embed.motionbert_inputs import (
    load_motionbert_inputs,
    require_clean_repository,
)
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json


def auxiliary_preprocessing_digest(protocol) -> str:
    """The input contract precedes fallback binding, avoiding a circular digest."""
    import hashlib

    payload = {
        "source_contract": protocol.dataset.source_contract.model_dump(mode="json"),
        "input_pipeline": protocol.input_pipeline.model_dump(mode="json"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _binding(path: Path, root: Path) -> dict[str, str]:
    return {"relative_path": str(path.relative_to(root)), "sha256": sha256_file(path)}


def auxiliary_annotations(payload: dict, inventory, novel_actions) -> dict[int, dict]:
    """Package by authorized metadata without inspecting novel pose arrays."""
    annotations = payload["annotations"]
    if len(annotations) != len(inventory):
        raise ValueError("trusted aggregate length differs from the verified inventory")
    allowed = {}
    for row in inventory:
        if row.action in novel_actions:
            continue
        annotation = annotations[row.annotation_index]
        if (
            annotation["frame_dir"] != row.sample_id
            or annotation["label"] != row.action - 1
        ):
            raise ValueError("auxiliary annotation identity differs from its inventory")
        allowed[row.annotation_index] = annotation
    return allowed


@guarded_auxiliary
def prepare_v3(
    *,
    template_path: str | Path,
    historical_protocol_path: str | Path,
    manifest_set_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Create auxiliary-only input, fallback evidence, and a resolved protocol draft.

    This is the separately documented packaging step: the trusted upstream pickle
    must deserialize its shared container. Only authorized auxiliary annotations
    are retained, preprocessed, or inspected by scientific code.
    """
    from pose_embed.corruptions.fallback import (
        collect_torso_fallback_v3,
        write_torso_fallback_v3,
    )
    from pose_embed.models.motionbert import verify_motionbert_assets

    require_dataset_unopened(require_registry=True)
    require_clean_repository()
    protocol = load_protocol(template_path)
    if protocol.protocol_id != "protocol-v3" or protocol.preparation is not None:
        raise ValueError("preparation requires the unresolved v3 template")
    historical_protocol = load_protocol(historical_protocol_path)
    if protocol_digest(historical_protocol) != (
        protocol.provenance.adopted_input_protocol_sha256
    ):
        raise ValueError("preparation requires the exact adopted historical protocol")
    inputs = load_motionbert_inputs(
        historical_protocol_path, manifest_set_path, load_annotations=False
    )
    if (
        protocol_digest(inputs.protocol)
        != protocol.provenance.adopted_input_protocol_sha256
        or inputs.protocol.dataset != protocol.dataset
        or inputs.protocol.input_pipeline != protocol.input_pipeline
    ):
        raise ValueError("v3 must retain the adopted source and preprocessing contract")
    validate_registered_source_inventory(inputs.bindings["source_inventory_sha256"])
    assets = verify_motionbert_assets(inputs.data_root)
    root = canonical_artifact_root()
    output = require_path_within(output_dir, root / "study-v3", label="v3 preparation")
    output.mkdir(parents=True, exist_ok=False)
    aggregate = (
        inputs.data_root / protocol.dataset.source_contract.aggregate_relative_path
    )
    # load_motionbert_inputs already checked the exact trusted source bytes/hash.
    with aggregate.open("rb") as stream:
        source = pickle.load(stream)  # noqa: S301 - hash-verified trusted source
    annotations = auxiliary_annotations(
        source, inputs.inventory, set(protocol.dataset.novel_actions)
    )
    del source
    if len(annotations) != 95001:
        raise ValueError("v3 auxiliary container must contain exactly 95,001 rows")
    container = output / "auxiliary.pkl"
    with container.open("xb") as stream:
        pickle.dump(annotations, stream, protocol=5)
    allowed_ids = [
        row.sample_id for row in inputs.inventory if row.annotation_index in annotations
    ]
    write_immutable_json(
        container.with_suffix(".metadata.json"),
        {
            "schema_version": 1,
            "scope": "auxiliary_only",
            "sample_count": len(allowed_ids),
            "sample_order_sha256": sample_order_digest(allowed_ids),
            "container_sha256": sha256_file(container),
            "aggregate_sha256": protocol.dataset.source_contract.aggregate_sha256,
            "source_inventory_sha256": inputs.bindings["source_inventory_sha256"],
            "packaging": (
                "shared_pickle_deserialization_then_metadata_only_auxiliary_selection"
            ),
            "novel_preprocessing": False,
        },
    )
    training = inputs.manifests["development-train.jsonl"]
    by_id = {row.sample_id: row.annotation_index for row in inputs.inventory}
    fallback = collect_torso_fallback_v3(
        (
            (
                row.sample_id,
                torch.from_numpy(
                    preprocess_annotation(annotations[by_id[row.sample_id]], protocol)
                ),
            )
            for row in training
        ),
        expected_sample_ids=[row.sample_id for row in training],
        source_inventory_sha256=inputs.bindings["source_inventory_sha256"],
        source_manifest_sha256=sha256_file(
            inputs.manifest_set_path.parent / "development-train.jsonl"
        ),
        preprocessing_sha256=auxiliary_preprocessing_digest(protocol),
    )
    fallback_path = output / "torso-fallback.json"
    write_torso_fallback_v3(fallback_path, fallback)
    gallery, queries, _ = build_development_episode(
        inputs.manifests["development-validation.jsonl"], protocol
    )
    identities = {
        name.removesuffix(".jsonl").replace("-", "_"): [row.sample_id for row in rows]
        for name, rows in inputs.manifests.items()
        if name != "official-novel.jsonl"
    }
    identities.update(
        development_gallery=[row.sample_id for row in gallery],
        development_queries=[row.sample_id for row in queries],
    )
    identity_path = output / "identities.json"
    write_immutable_json(
        identity_path,
        {
            "schema_version": 1,
            "ordered_sample_ids": identities,
            "selection_prefix": "protocol-v1|dev-anchor-v1|",
            "historical_episode_sha256": (
                "88f30f96e35dedfd34b42f8e8ee2b561db44bbaf1f93d82d0522ffe011abba46"
            ),
            "source_inventory_sha256": inputs.bindings["source_inventory_sha256"],
        },
    )
    preparation = {
        "auxiliary_container": _binding(container, root),
        "fallback_evidence": _binding(fallback_path, root),
        "fallback_value": fallback["fallback_scale"],
        "source_inventory": _binding(
            inputs.manifest_set_path.parent / "source-inventory.jsonl", root
        ),
        "identities": _binding(identity_path, root),
        "encoder_checkpoint_sha256": assets["checkpoint_sha256"],
        "upstream_sha256": {
            key: str(assets[key])
            for key in ("upstream_sha256", "config_sha256", "license_sha256")
        },
    }
    document = protocol.model_dump(mode="json")
    document.update(status="resolved", preparation=preparation)
    resolved = output / "protocol.v3.yaml"
    with resolved.open("x") as stream:
        yaml.safe_dump(document, stream, sort_keys=False)
    # Validate the exact resolved document before publishing the completion record.
    load_protocol(resolved)
    record = {
        "schema_version": 1,
        "protocol": _binding(resolved, root),
        "preparation": preparation,
        "source_manifest_set": _binding(inputs.manifest_set_path, root),
        "git_commit": require_clean_repository(),
    }
    write_immutable_json(output / "preparation.json", record)
    return record


def load_auxiliary_annotations(protocol, inventory, root: Path) -> dict[int, dict]:
    """Deserialize only the verified auxiliary container after design authorization."""
    from pose_embed.protocol_v3 import require_v3_design

    require_dataset_unopened(require_registry=True)
    require_v3_design(protocol)
    binding = protocol.preparation.auxiliary_container
    path = require_path_within(
        root / binding.relative_path, root / "study-v3", label="auxiliary container"
    )
    if sha256_file(path) != binding.sha256:
        raise ValueError("auxiliary container hash mismatch")
    with path.open("rb") as stream:
        annotations = pickle.load(stream)  # noqa: S301 - immutable hash-bound auxiliary data
    expected = {
        row.annotation_index: row.sample_id
        for row in inventory
        if row.action not in protocol.dataset.novel_actions
    }
    if not isinstance(annotations, dict) or set(annotations) != set(expected):
        raise ValueError(
            "auxiliary container does not match the complete authorized indices"
        )
    for index, sample_id in expected.items():
        if annotations[index]["frame_dir"] != sample_id:
            raise ValueError("auxiliary container contains an unauthorized annotation")
    return annotations


@guarded_auxiliary
def rebind_v3_manifests(
    *,
    protocol_path: str | Path,
    historical_manifest_set: str | Path,
    output_dir: str | Path,
) -> dict:
    """Keep every historical sample identity and byte-identical manifest unchanged."""
    from pose_embed.motionbert_inputs import verify_manifest_bundle

    require_dataset_unopened(require_registry=True)
    protocol = load_protocol(protocol_path)
    if protocol.protocol_id != "protocol-v3" or protocol.preparation is None:
        raise ValueError("manifest rebinding requires resolved v3 preparation")
    root = canonical_artifact_root()
    source = require_path_within(
        historical_manifest_set, root, label="historical manifest bundle"
    )
    document = json.loads(source.read_text())
    if document.get("protocol_sha256") != (
        protocol.provenance.adopted_input_protocol_sha256
    ):
        raise ValueError("manifest rebinding requires the adopted historical protocol")
    inventory_sha256 = sha256_file(source.parent / "source-inventory.jsonl")
    if inventory_sha256 != protocol.preparation.source_inventory.sha256:
        raise ValueError("rebound source inventory differs from measured preparation")
    validate_registered_source_inventory(inventory_sha256)
    identity_path = require_path_within(
        root / protocol.preparation.identities.relative_path,
        root / "study-v3",
        label="v3 identities",
    )
    if sha256_file(identity_path) != protocol.preparation.identities.sha256:
        raise ValueError("v3 preparation identities changed before manifest rebinding")
    expected = json.loads(identity_path.read_text())["ordered_sample_ids"]
    output = require_path_within(output_dir, root / "study-v3", label="v3 manifests")
    output.mkdir(parents=True, exist_ok=False)
    for name, binding in document["files"].items():
        path = source.parent / name
        if Path(name).name != name or sha256_file(path) != binding["sha256"]:
            raise ValueError("historical manifest content changed")
        shutil.copyfile(path, output / name)
    document["protocol_sha256"] = protocol_digest(protocol)
    write_immutable_json(output / "manifest-set.json", document)
    _, manifests = verify_manifest_bundle(protocol, output / "manifest-set.json")
    for name, rows in manifests.items():
        if name == "official-novel.jsonl":
            continue
        if [row.sample_id for row in rows] != expected[
            name.removesuffix(".jsonl").replace("-", "_")
        ]:
            raise ValueError("v3 manifest identities changed")
    episode = generate_development_episode(
        output / "development-validation.jsonl", output / "development", protocol_path
    )
    return {
        "manifest_set": str(output / "manifest-set.json"),
        "development_episode": episode,
    }
