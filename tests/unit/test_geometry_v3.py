from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from pose_embed.corruptions.pose import apply_corruption_v3
from pose_embed.geometry_v3 import (
    geometry_damage,
    run_geometry_panel,
    select_geometry_panel,
    summarize_geometry,
    verify_geometry_case,
)
from pose_embed.provenance import sha256_file, write_immutable_json


def _pose() -> torch.Tensor:
    clean = torch.zeros(2, 100, 17, 3)
    clean[0, ..., 2] = 1
    clean[0, :, [4, 1], 1] = 2
    return clean


def test_mask_damage_counts_newly_observed_locations_and_undefined_denominators():
    clean = _pose()
    output = clean.clone()
    output[0, 0, 0] = 0
    row = geometry_damage(clean, output, "joint_mask", None)
    assert row["original_observed_count"] == 1700
    assert row["newly_masked_observed_count"] == 1
    assert row["damage"] == 1 / 1700
    already_masked = apply_corruption_v3(
        clean, family="joint_mask", severity=3, sample_id="missing"
    )
    repeated = apply_corruption_v3(
        already_masked, family="joint_mask", severity=3, sample_id="missing"
    )
    assert geometry_damage(already_masked, repeated, "joint_mask", None)["damage"] == 0
    empty = torch.zeros_like(clean)
    assert geometry_damage(empty, empty, "frame_mask", None)["damage"] is None


def test_jitter_damage_is_per_coordinate_rms_over_original_support_and_actual_scale():
    clean = _pose()
    output = clean.clone()
    output[0, ..., 0] += 3
    output[0, ..., 1] += 4
    assert geometry_damage(clean, output, "coordinate_jitter", 2)["damage"] == (
        math.sqrt(25 / 2) / 2
    )
    empty = torch.zeros_like(clean)
    row = geometry_damage(empty, empty, "coordinate_jitter", 2)
    assert row["damage"] is None
    assert row["fallback_used"] is True
    with pytest.raises(ValueError, match="own scale"):
        geometry_damage(clean, output, "coordinate_jitter", 3)
    with pytest.raises(ValueError, match="positive torso scale"):
        geometry_damage(empty, empty, "coordinate_jitter", None)


def test_geometry_summary_preserves_zero_undefined_and_linear_quantiles():
    row = geometry_damage(_pose(), _pose(), "coordinate_jitter", 2)
    rows = [{**row, "damage": value} for value in (0, 0.2, 0.5)]
    rows.append({**row, "damage": None, "fallback_used": True})
    summary = summarize_geometry(rows)
    assert summary["query_count"] == 4
    assert summary["finite_count"] == 3
    assert summary["undefined_count"] == 1
    assert summary["zero_damage_count"] == 1
    assert summary["minimum"] == 0
    assert summary["median"] == 0.2
    assert summary["p95"] == pytest.approx(0.47)
    assert summary["maximum"] == 0.5
    assert summary["fallback_fraction"] == 0.25
    assert summarize_geometry([rows[-1]])["minimum"] is None
    with pytest.raises(ValueError, match="nonfinite"):
        summarize_geometry([{**row, "damage": float("nan")}])


@pytest.mark.parametrize("defect", ["nonfinite", "confidence", "missing", "mask"])
def test_geometry_rejects_source_and_operator_defects(defect: str):
    clean = _pose()
    output = clean.clone()
    family = "coordinate_jitter"
    if defect == "nonfinite":
        output[0, 0, 0, 0] = float("nan")
    elif defect == "confidence":
        output[1, 0, 0, 2] = -0.0
    elif defect == "missing":
        output[1, 0, 0, 0] = 1
    else:
        family = "joint_mask"
        output[0, 0, 0, 0] = 1
    with pytest.raises(ValueError):
        geometry_damage(clean, output, family, 2)


def _panel_rows():
    return [
        {
            "sample_id": f"S001C001P{performer:03}R001A{action:03}",
            "observed_support": 1700,
            "second_person_support": 0,
            "own_scale": 2,
        }
        for action in range(2, 121, 6)
        for performer in (1, 2, 3)
    ]


def test_panel_selection_uses_fixed_hashes_deduplicates_sentinels_and_records_absence():
    rows = _panel_rows()
    panel = select_geometry_panel(rows)
    expected = []
    for action in range(2, 121, 6):
        ids = [
            row["sample_id"]
            for row in rows
            if row["sample_id"].endswith(f"A{action:03}")
        ]
        expected.extend(
            sorted(
                ids,
                key=lambda sample_id: (
                    hashlib.sha256(
                        f"protocol-v3|geometry-panel-v1|{sample_id}".encode()
                    ).hexdigest(),
                    sample_id,
                ),
            )[:2]
        )
    assert panel["base_sample_ids"] == sorted(expected)
    assert panel == select_geometry_panel(rows[::-1])
    assert len(panel["sample_ids"]) == 40
    assert "minimum_positive_second_person_support" in panel["absent_categories"]
    assert "invalid_own_scale" in panel["absent_categories"]
    assert "all_missing" in panel["absent_categories"]
    rows[0].update(observed_support=0, own_scale=None)
    rows[1].update(observed_support=1, own_scale=None)
    rows[2].update(observed_support=3400, second_person_support=1700, own_scale=5)
    panel = select_geometry_panel(rows)
    assert panel["sentinels"]["all_missing"] == rows[0]["sample_id"]
    assert panel["sentinels"]["invalid_own_scale"] == rows[1]["sample_id"]
    assert panel["sentinels"]["maximum_support"] == rows[2]["sample_id"]
    assert 40 <= len(panel["sample_ids"]) <= 48
    with pytest.raises(ValueError, match="repeats"):
        select_geometry_panel(rows + [rows[0]])
    rows[0]["sample_id"] = rows[0]["sample_id"][:-3] + "001"
    with pytest.raises(ValueError, match="development action"):
        select_geometry_panel(rows)


@pytest.mark.parametrize("unsigned", [0, 2**64 - 1])
def test_complete_geometry_panel_covers_frame_boundaries_and_degenerate_scales(
    monkeypatch: pytest.MonkeyPatch, unsigned: int
):
    for module in ("pose_embed.corruptions.pose", "pose_embed.geometry_v3"):
        monkeypatch.setattr(
            f"{module}.corruption_randomness_v3",
            lambda *args: (unsigned, unsigned & (2**63 - 1)),
        )
    for clean in (_pose(), torch.zeros(2, 100, 17, 3), torch.ones(2, 100, 17, 3)):
        original = clean.clone()
        tensors, rows = verify_geometry_case(clean, "boundary", 2)
        assert len(tensors) == 10
        assert len(rows) == 9
        assert torch.equal(clean, original)
        assert all(array.shape == (2, 100, 17, 3) for array in tensors.values())
        if bool((clean == 0).all()):
            assert all(row["damage"] is None for row in rows)


def test_complete_geometry_generation_matches_in_fresh_processes():
    script = """
import hashlib, json, torch
from pose_embed.geometry_v3 import verify_geometry_case
p = torch.zeros(2,100,17,3)
p[0,...,2] = 1
p[0,:,[4,1],1] = 2
outputs = {}
for name, pose in [('one-person', p), ('all-missing', torch.zeros_like(p)),
                   ('degenerate-two-person', torch.ones_like(p))]:
    tensors, rows = verify_geometry_case(pose, name, 2)
    outputs[name] = {
        k: hashlib.sha256(v.tobytes()).hexdigest() for k,v in tensors.items()
    }
print(json.dumps(outputs, sort_keys=True))
"""
    first = subprocess.check_output([sys.executable, "-c", script], text=True)
    second = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert first == second
    assert sum(len(rows) for rows in json.loads(first).values()) == 30


def test_geometry_runner_does_not_load_inputs_without_resolved_design(
    repository_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def forbidden(*args, **kwargs):
        pytest.fail("unresolved geometry request loaded poses")

    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.load_motionbert_inputs", forbidden
    )
    with pytest.raises(ValueError, match="unresolved v3 template"):
        run_geometry_panel(
            repository_root / "configs/protocol.v3.yaml",
            tmp_path / "missing",
            tmp_path / "output",
        )
    assert not (tmp_path / "output").exists()


@pytest.fixture
def archived_geometry(tmp_path, monkeypatch, repository_root):
    from pose_embed.config import load_protocol
    from pose_embed.config_v3 import ProtocolV3Config
    from pose_embed.dataset_seal import (
        dataset_access,
        record_dataset_opening,
        register_artifact_roots,
    )
    from pose_embed.geometry_v3 import _geometry_summary
    from pose_embed.motionbert_inputs import motionbert_code_digest
    from pose_embed.protocol import protocol_digest

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    register_artifact_roots([])
    payload = load_protocol(repository_root / "configs/protocol.v3.yaml").model_dump(
        mode="json"
    )
    binding = {"relative_path": "input.json", "sha256": "a" * 64}
    payload.update(
        status="resolved",
        preparation={
            "auxiliary_container": binding,
            "fallback_evidence": binding,
            "fallback_value": 2.0,
            "source_inventory": binding,
            "identities": binding,
            "encoder_checkpoint_sha256": "a" * 64,
            "upstream_sha256": {
                key: "a" * 64
                for key in ("upstream_sha256", "config_sha256", "license_sha256")
            },
        },
    )
    protocol = ProtocolV3Config.model_validate(payload)
    bundle = tmp_path / "manifest-set.json"
    inventory = tmp_path / "source-inventory.jsonl"
    bundle.write_text("{}")
    inventory.write_text("fixture metadata")
    metadata = _panel_rows()
    manifest = tmp_path / "queries.jsonl"
    manifest.write_text(
        "\n".join(
            json.dumps(
                {"sample_id": row["sample_id"], "split": "development_validation"}
            )
            for row in metadata
        )
    )
    monkeypatch.setattr(
        "pose_embed.protocol_v3.require_v3_design",
        lambda _: SimpleNamespace(
            manifests={
                "development_queries": SimpleNamespace(relative_path=manifest.name)
            }
        ),
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.verify_manifest_bundle", lambda *a: None
    )
    monkeypatch.setattr(
        "pose_embed.geometry_v3._load_panel_inputs",
        lambda *a: pytest.fail("archive validation reloaded auxiliary poses"),
    )
    destination = tmp_path / "study-v3/locks/geometry"
    destination.mkdir(parents=True)
    panel_path = destination / "panel.json"
    write_immutable_json(
        panel_path,
        {
            "schema_version": 1,
            "bindings": {
                "protocol_sha256": protocol_digest(protocol),
                "manifest_set_sha256": sha256_file(bundle),
                "source_inventory_sha256": sha256_file(inventory),
                "aggregate_sha256": protocol.dataset.source_contract.aggregate_sha256,
                "missing_list_sha256": (
                    protocol.dataset.source_contract.missing_list_sha256
                ),
                "code_sha256": motionbert_code_digest(),
                "dependency_lock_sha256": sha256_file(repository_root / "uv.lock"),
            },
            "manifest_sha256": sha256_file(manifest),
            "manifest_set_relative_path": bundle.name,
            "selection_code_sha256": sha256_file(
                repository_root / "src/pose_embed/geometry_v3.py"
            ),
            "candidate_metadata": metadata,
            **select_geometry_panel(metadata),
        },
    )
    tensors, rows = {}, []
    for sample_id in select_geometry_panel(metadata)["sample_ids"]:
        case, damage = verify_geometry_case(_pose(), sample_id, 2)
        tensors.update(
            {f"{sample_id}__{condition}": value for condition, value in case.items()}
        )
        rows.extend(damage)
    outputs = []
    for repeat in (1, 2):
        folder = destination / f"repeat-{repeat}"
        folder.mkdir()
        np.savez(folder / "tensors.npz", **tensors)
        output = {
            "panel_sha256": sha256_file(panel_path),
            "tensor_archive_sha256": sha256_file(folder / "tensors.npz"),
            "tensor_sha256": {
                key: hashlib.sha256(value.tobytes()).hexdigest()
                for key, value in tensors.items()
            },
            "rows": rows,
        }
        write_immutable_json(folder / "verification.json", output)
        outputs.append(output)
    summary = _geometry_summary(panel_path, outputs)
    path = destination / "summary.json"
    write_immutable_json(path, summary)
    with dataset_access(opening=True):
        record_dataset_opening(version="protocol-v3", authorization={"fixture": True})
    return path, protocol, summary


def test_geometry_archive_revalidation_remains_available_after_opening(
    archived_geometry,
):
    from pose_embed.geometry_v3 import validate_geometry_panel

    path, protocol, summary = archived_geometry
    assert validate_geometry_panel(path, protocol) == summary


def test_fresh_geometry_worker_rechecks_all_candidate_metadata_before_scoring(
    tmp_path, monkeypatch
):
    from pose_embed import geometry_v3

    manifest = tmp_path / "queries.jsonl"
    manifest.write_text("fixture metadata only")
    panel = tmp_path / "panel.json"
    inputs = SimpleNamespace(bindings={"fixture": True})
    write_immutable_json(
        panel,
        {
            "manifest_sha256": sha256_file(manifest),
            "selection_code_sha256": sha256_file(geometry_v3.__file__),
            "bindings": inputs.bindings,
            "candidate_metadata": [{"observed_support": 10}],
        },
    )
    monkeypatch.setattr(
        geometry_v3, "_load_panel_inputs", lambda *a: (inputs, [], manifest)
    )
    monkeypatch.setattr(
        geometry_v3, "_panel_metadata", lambda *a: [{"observed_support": 11}]
    )
    monkeypatch.setattr(
        geometry_v3, "verify_geometry_case", lambda *a: pytest.fail("scored early")
    )
    with pytest.raises(ValueError, match="frozen geometry panel provenance changed"):
        geometry_v3._panel_worker(
            "fixture", "fixture", str(panel), str(tmp_path / "out")
        )
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("mutation", ["tensor", "summary", "candidate_metadata"])
def test_geometry_archive_rejects_tampered_evidence(archived_geometry, mutation):
    from pose_embed.geometry_v3 import validate_geometry_panel

    path, protocol, summary = archived_geometry
    if mutation == "tensor":
        archive_path = path.parent / "repeat-2/tensors.npz"
        with np.load(archive_path) as archive:
            tensors = {key: archive[key] for key in archive.files}
        key = next(key for key in tensors if "coordinate_jitter" in key)
        tensors[key][0, 0, 0, 0] += 1
        np.savez(archive_path, **tensors)
    elif mutation == "summary":
        summary["tensor_count"] += 1
        path.write_text(json.dumps(summary))
    else:
        panel_path = path.parent / "panel.json"
        panel = json.loads(panel_path.read_text())
        panel["candidate_metadata"].pop()
        panel_path.write_text(json.dumps(panel))
    with pytest.raises(ValueError, match="geometry"):
        validate_geometry_panel(path, protocol)
