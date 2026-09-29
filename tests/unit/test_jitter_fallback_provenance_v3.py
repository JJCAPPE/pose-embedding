from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
import torch

from pose_embed.artifacts import load_feature_sidecar, sample_order_digest
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.data.manifest import ManifestRecord
from pose_embed.motionbert_features import (
    _validate_jitter_fallback_provenance,
    extract_motionbert_features,
)
from pose_embed.provenance import sha256_file


@pytest.fixture
def jitter_cache(tmp_path, monkeypatch):
    # Isolate the real CPU extraction loop and sidecar publication; source/parity
    # authorization and GPU numerics have their own independent fixture suites.
    monkeypatch.delenv("POSE_EMBED_ARTIFACT_ROOT", raising=False)
    study = tmp_path / "study-v3"
    study.mkdir()
    evidence = study / "fallback.json"
    evidence.write_text('{"fixture_only":true}\n')
    binding = ArtifactBinding(
        relative_path="study-v3/fallback.json", sha256=sha256_file(evidence)
    )
    protocol = SimpleNamespace(
        protocol_id="protocol-v3",
        preparation=SimpleNamespace(fallback_evidence=binding, fallback_value=2.0),
        corruptions=SimpleNamespace(
            coordinate_jitter_fractions=(0.01, 0.025, 0.05),
            joint_mask_counts=(3, 6, 8),
            consecutive_frame_mask_counts=(10, 25, 40),
        ),
    )
    ids = [f"S001C{camera:03}P001R001A002" for camera in (1, 2, 3)]
    rows = [
        ManifestRecord(sample_id=item, split="development_validation") for item in ids
    ]
    poses = [torch.ones(2, 100, 17, 3) for _ in ids]
    for pose in poses:
        pose[:, :, [4, 1], 1] = 3
    poses[1][:, :, [11, 14, 4, 1], 2] = 0  # Exactly the middle query needs fallback.
    paths = {}
    for name in (
        "aggregate",
        "manifest-set",
        "source-inventory",
        "queries",
        "protocol",
        "parity",
        "checkpoint",
        "encoder",
    ):
        path = tmp_path / f"{name}.jsonl"
        path.write_text("synthetic fixture\n")
        paths[name] = path
    inputs = SimpleNamespace(
        protocol=protocol,
        artifact_root=tmp_path,
        data_root=tmp_path,
        manifest_set_path=paths["manifest-set"],
        inventory=[
            SimpleNamespace(sample_id=item, annotation_index=i)
            for i, item in enumerate(ids)
        ],
        manifests={},
        annotations=poses,
        bindings={"source_inventory_sha256": "a" * 64},
    )
    assets = {"checkpoint_path": paths["checkpoint"], "config_path": paths["encoder"]}
    monkeypatch.setattr(
        "pose_embed.motionbert_features.load_protocol", lambda _: protocol
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_features.resolve_scientific_paths",
        lambda _: SimpleNamespace(root=tmp_path),
    )
    monkeypatch.setattr("pose_embed.protocol_v3.require_v3_design", lambda _: None)
    monkeypatch.setattr(
        "pose_embed.motionbert_features.load_motionbert_inputs", lambda *args: inputs
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_features._source_paths", lambda _: [paths["aggregate"]]
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_features.validate_selected_manifest",
        lambda *args, **kwargs: rows,
    )
    monkeypatch.setattr(
        "pose_embed.data.motionbert.preprocess_annotation", lambda pose, _: pose.numpy()
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_features.build_motionbert_bindings",
        lambda *args: {
            "protocol_sha256": "a" * 64,
            "upstream_sha256": "b" * 64,
            "checkpoint_sha256": "c" * 64,
        },
    )
    monkeypatch.setattr("pose_embed.motionbert_features.MOTIONBERT_CODE_PATHS", ())
    monkeypatch.setattr(
        "pose_embed.motionbert_features.preprocessing_digest", lambda _: "d" * 64
    )
    monkeypatch.setattr(
        "pose_embed.models.motionbert.inference_environment", lambda _: {}
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_parity.validate_parity_report",
        lambda *args: {"environment": {}},
    )

    class Encoder:
        def get_representation(self, tensor):
            return tensor[..., :1].expand(-1, -1, -1, 512)

    monkeypatch.setattr(
        "pose_embed.models.motionbert.load_frozen_encoder",
        lambda *args, **kwargs: (Encoder(), assets),
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_features.validate_motionbert_cache",
        lambda sidecar, protocol, _: _validate_jitter_fallback_provenance(
            sidecar, protocol
        ),
    )
    output = study / "jitter.npz"
    extract_motionbert_features(
        paths["aggregate"],
        output,
        protocol_path=paths["protocol"],
        manifest_path=paths["queries"],
        manifest_set_path=paths["manifest-set"],
        parity_evidence_path=paths["parity"],
        role="query_corrupted",
        split="development_validation",
        device="cpu",
        corruption_family="coordinate_jitter",
        corruption_severity=0.025,
    )
    return load_feature_sidecar(output), protocol, evidence


def test_jitter_extraction_records_exact_fallback_use_and_bound_evidence(jitter_cache):
    sidecar, protocol, evidence = jitter_cache
    record = sidecar.provenance["jitter_fallback"]
    assert record["sample_count"] == 3
    assert record["fallback_count"] == 1
    assert record["fallback_fraction"] == 1 / 3
    assert record["fallback_sample_ids"] == [sidecar.sample_ids[1]]
    assert record["fallback_value"] == 2.0
    assert (
        record["fallback_evidence"]
        == protocol.preparation.fallback_evidence.model_dump()
    )
    assert sidecar.provenance["inputs"][str(evidence)] == sha256_file(evidence)
    _validate_jitter_fallback_provenance(sidecar, protocol)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "count",
        "shape",
        "duplicate",
        "foreign",
        "order",
        "hash",
        "value",
        "binding",
        "frequency",
        "input",
        "file",
    ],
)
def test_v3_jitter_fallback_provenance_rejects_tampering(jitter_cache, change):
    sidecar, protocol, evidence = jitter_cache
    provenance = deepcopy(sidecar.provenance)
    record = provenance["jitter_fallback"]
    if change == "missing":
        provenance.pop("jitter_fallback")
    elif change == "count":
        record["fallback_count"] = 0
    elif change == "shape":
        record["sample_count"] = 4
    elif change in {"duplicate", "foreign", "order"}:
        ids = {
            "duplicate": [sidecar.sample_ids[1], sidecar.sample_ids[1]],
            "foreign": ["S001C001P001R001A008"],
            "order": list(sidecar.sample_ids[::-1]),
        }[change]
        record.update(
            fallback_sample_ids=ids,
            fallback_count=len(ids),
            fallback_fraction=len(ids) / 3,
            fallback_sample_order_sha256=sample_order_digest(ids),
        )
    elif change == "hash":
        record["fallback_sample_order_sha256"] = "0" * 64
    elif change == "value":
        record["fallback_value"] = 3.0
    elif change == "binding":
        record["fallback_evidence"]["sha256"] = "0" * 64
    elif change == "frequency":
        record["fallback_fraction"] = float("nan")
    elif change == "input":
        provenance["inputs"].pop(str(evidence))
    else:
        evidence.write_text(json.dumps({"changed": True}))
    with pytest.raises(ValueError, match="fallback"):
        _validate_jitter_fallback_provenance(
            sidecar.model_copy(update={"provenance": provenance}), protocol
        )
