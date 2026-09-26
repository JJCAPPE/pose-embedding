from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from pose_embed.config import load_protocol
from pose_embed.data.inventory import NTUInventoryRecord
from pose_embed.data.manifest import ManifestRecord
from pose_embed.data.motionbert import preprocess_annotation
from pose_embed.models.action_head import ActionHeadEmbed
from pose_embed.motionbert_parity import (
    PANEL_SELECTION,
    _compare,
    _confidence_fixtures,
    _confidence_oracle,
    _model_checks,
    _order_hash,
    _preprocessing_reference,
    _tracking_oracle,
    _upstream_oracles,
    run_motionbert_parity,
    select_parity_panel,
    validate_parity_report,
)
from pose_embed.provenance import sha256_file


def _inventory() -> list[NTUInventoryRecord]:
    records = []
    for people in (1, 2):
        for frames in (73, 100, 147):
            for _ in range(12):
                index = len(records)
                records.append(
                    NTUInventoryRecord(
                        sample_id=f"S001C001P{index + 1:03d}R001A003",
                        annotation_index=index,
                        setup=1,
                        camera=1,
                        performer=index + 1,
                        repetition=1,
                        action=3,
                        label=2,
                        pose_track_count=people,
                        nonempty_track_count=people,
                        total_frames=frames,
                        keypoint_shape=(people, frames, 17, 2),
                        keypoint_score_shape=(people, frames, 17),
                        image_shape=(1080, 1920),
                        original_shape=(1080, 1920),
                    )
                )
    return records


def _manifests(inventory: list[NTUInventoryRecord]) -> list[ManifestRecord]:
    return [
        ManifestRecord(sample_id=row.sample_id, split="final_train")
        for row in inventory
    ]


def _passing_report(tmp_path: Path) -> dict:
    inventory = _inventory()
    manifests = _manifests(inventory)
    panel = select_parity_panel(inventory, manifests)
    inventory_path = tmp_path / "source-inventory.jsonl"
    manifest_path = tmp_path / "final-train.jsonl"
    inventory_path.write_text("\n".join(row.model_dump_json() for row in inventory))
    manifest_path.write_text("\n".join(row.model_dump_json() for row in manifests))
    bundle_path = tmp_path / "manifest-set.json"
    bundle_path.write_text(
        json.dumps(
            {
                "protocol_sha256": "a" * 64,
                "files": {
                    path.name: {"sha256": sha256_file(path)}
                    for path in (inventory_path, manifest_path)
                },
            }
        )
    )
    ids = [row.sample_id for row in panel]
    layers = {}
    for name in (
        "camera_normalization",
        "person_tracking",
        "coordinate_mapping",
        "temporal_sampling",
        "single_person_padding",
        "spatial_normalization",
        "tracking_indices",
        "temporal_indices",
        "confidence_mapping",
        "encoder_representation",
        "pooled_head_input",
        "action_head",
    ):
        exact = name in {"tracking_indices", "temporal_indices", "confidence_mapping"}
        model = name in {"encoder_representation", "pooled_head_input", "action_head"}
        layers[name] = {
            "checks": 2 if model else 50 if name == "confidence_mapping" else 48,
            "passed": True,
            "atol": 0.0 if exact else 1e-6,
            "rtol": 0.0 if exact else 1e-5 if model else 1e-6,
            "max_abs_error": 0.0,
            "max_tolerance_ratio": 0.0,
        }
    return {
        "schema_version": 1,
        "status": "passed",
        "bindings": {
            "protocol_sha256": "a" * 64,
            "manifest_set_sha256": sha256_file(bundle_path),
            "source_inventory_sha256": sha256_file(inventory_path),
        },
        "configuration": {
            "device": "cpu",
            "dtype": "float32",
            "batch_size": 32,
            "head_seed": 7,
            "deterministic_algorithms": True,
            "mixed_precision": False,
            "tf32": False,
        },
        "environment": {
            "device_type": "cpu",
            "hostname": "test",
            "cuda": None,
            "numpy": "2.0",
            "torch": "2.9",
            "dtype": "float32",
            "batch_size": 32,
            "deterministic_algorithms": True,
            "cuda_matmul_allow_tf32": False,
            "cudnn_allow_tf32": False,
            "cudnn_benchmark": False,
            "deterministic_warn_only": False,
            "cudnn_deterministic": True,
            "float32_matmul_precision": "highest",
            "cublas_workspace_config": ":4096:8",
        },
        "panel": {
            "count": 48,
            "selection": PANEL_SELECTION,
            "source": "final-train.jsonl",
            "sample_ids": ids,
            "sample_order_sha256": _order_hash(ids),
            "samples": [
                {
                    "sample_id": row.sample_id,
                    "people": row.pose_track_count,
                    "frames": row.total_frames,
                    "annotation_index": row.annotation_index,
                }
                for row in panel
            ],
        },
        "confidence_compatibility": (
            "local_corrected_h36m_mapping_not_upstream_bit_parity"
        ),
        "layers": layers,
        "provenance": {
            "git_dirty": False,
            "git_sha": "b" * 40,
            "inputs": {str(bundle_path): sha256_file(bundle_path)},
            "environment": {
                "dependencies": {"numpy": "2.0", "torch": "2.9"},
                "torch": "2.9",
                "cuda_version": None,
            },
        },
    }


def test_parity_panel_is_hash_selected_and_preserves_source_order() -> None:
    inventory = _inventory()
    manifest = list(reversed(_manifests(inventory)))
    selected = select_parity_panel(inventory, manifest)
    expected = set()
    for people in (1, 2):
        for frames in (73, 100, 147):
            group = [
                row
                for row in inventory
                if row.pose_track_count == people and row.total_frames == frames
            ]
            group.sort(
                key=lambda row: hashlib.sha256(
                    f"{PANEL_SELECTION}|{row.sample_id}".encode()
                ).digest()
            )
            expected.update(row.sample_id for row in group[:8])
    assert len(selected) == 48
    assert [row.sample_id for row in selected] == [
        row.sample_id for row in manifest if row.sample_id in expected
    ]


def test_parity_panel_rejects_missing_stratum_and_novel_samples() -> None:
    inventory = _inventory()
    with pytest.raises(ValueError, match="at least eight"):
        select_parity_panel(inventory, _manifests(inventory)[:40])
    manifest = _manifests(inventory)
    manifest[0] = ManifestRecord(sample_id="S001C001P001R001A001", split="final_train")
    with pytest.raises(ValueError, match="auxiliary"):
        select_parity_panel(inventory, manifest)
    with pytest.raises(ValueError, match="duplicate"):
        select_parity_panel(inventory, [*manifest[1:], manifest[1]])


def test_confidence_oracle_tracks_people_and_uses_minimum_sources() -> None:
    scores = np.tile(np.arange(17), (2, 2, 1)).astype(np.float32)
    scores[1] += 20
    camera = np.zeros((2, 2, 17, 2), dtype=np.float32)
    camera[1, 0] = 1
    camera[0, 1] = 1
    tracking = _tracking_oracle(camera)
    np.testing.assert_array_equal(tracking, [[0, 1], [1, 0]])
    mapped = _confidence_oracle(scores, tracking)
    assert mapped[0, 0, 7] == 5
    assert mapped[0, 1, 7] == 25
    assert mapped[1, 1, 10] == 1


@pytest.mark.parametrize("dtype", [np.float16, np.float32])
@pytest.mark.parametrize("people", [1, 2])
@pytest.mark.parametrize("frames", [1, 79, 100, 137])
def test_preprocessing_matches_each_pinned_upstream_layer(
    repository_root: Path, protocol_path: Path, dtype: type, people: int, frames: int
) -> None:
    root = repository_root / ".cache/upstreams/MotionBERT"
    if not root.is_dir():
        pytest.skip("pinned upstream checkout is not fetched")
    upstream, _ = _upstream_oracles(root)
    rng = np.random.default_rng(31)
    annotation = {
        "keypoint": rng.uniform(0, 1000, (people, frames, 17, 2)).astype(dtype),
        "keypoint_score": rng.uniform(0, 1, (people, frames, 17)).astype(dtype),
        "img_shape": (1080, 1920),
        "total_frames": frames,
    }
    protocol = load_protocol(protocol_path)
    _, actual = preprocess_annotation(annotation, protocol, return_stages=True)
    expected = _preprocessing_reference(annotation, upstream)
    layers = {}
    for name in expected:
        _compare(layers, name, actual[name], expected[name])
    assert all(layer["passed"] for layer in layers.values())


def test_confidence_hand_calculated_fixtures(protocol_path: Path) -> None:
    layers = {}
    _confidence_fixtures(load_protocol(protocol_path), preprocess_annotation, layers)
    assert layers["confidence_mapping"]["checks"] == 2
    assert layers["confidence_mapping"]["max_abs_error"] == 0


def test_parity_comparison_rejects_wrong_order_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="temporal_indices"):
        _compare({}, "temporal_indices", np.array([1, 0]), np.array([0, 1]))
    with pytest.raises(ValueError, match="camera_normalization"):
        _compare({}, "camera_normalization", np.array([np.nan]), np.array([0.0]))


def test_model_parity_uses_upstream_wrapper_and_pooling(repository_root: Path) -> None:
    root = repository_root / ".cache/upstreams/MotionBERT"
    if not root.is_dir():
        pytest.skip("pinned upstream checkout is not fetched")
    _, action = _upstream_oracles(root)

    class Encoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pre_logits = nn.Linear(3, 4)

        def get_representation(self, poses: torch.Tensor) -> torch.Tensor:
            return self.pre_logits(poses)

    encoder = Encoder().requires_grad_(False).eval()
    head = ActionHeadEmbed(representation_dimension=4, embedding_dimension=8).eval()
    reference = action.ActionNet(
        encoder, dim_rep=4, hidden_dim=8, version="embed"
    ).eval()
    reference.head.fc1.load_state_dict(head.projection.state_dict())
    layers = {}
    _model_checks(torch.randn(3, 2, 7, 17, 3), encoder, head, reference, layers)
    assert set(layers) == {"encoder_representation", "pooled_head_input", "action_head"}
    assert all(layer["passed"] for layer in layers.values())


def test_complete_report_validates_and_rejects_changed_bindings(tmp_path: Path) -> None:
    report = _passing_report(tmp_path)
    path = tmp_path / "parity.json"
    path.write_text(json.dumps(report))
    assert validate_parity_report(path, report["bindings"]) == report
    with pytest.raises(ValueError, match="bindings"):
        validate_parity_report(path, {"protocol_sha256": "f" * 64})


def test_cuda_runtime_build_suffix_can_differ_from_distribution_version(
    tmp_path: Path,
) -> None:
    report = _passing_report(tmp_path)
    report["configuration"]["device"] = "cuda"
    report["environment"].update(
        device_type="cuda",
        device_index=0,
        cuda_device_name="NVIDIA L40S",
        cuda_device_uuid="test-uuid",
        torch="2.9.1+cu128",
        cuda="12.8",
    )
    report["provenance"]["environment"].update(torch="2.9.1+cu128", cuda_version="12.8")
    report["provenance"]["environment"]["dependencies"]["torch"] = "2.9.1"
    path = tmp_path / "parity.json"
    path.write_text(json.dumps(report))
    assert validate_parity_report(path, report["bindings"])["status"] == "passed"
    report["provenance"]["environment"]["torch"] = "2.9.1+cu126"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="library environment"):
        validate_parity_report(path, report["bindings"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "failed",
        "relaxed",
        "duplicate",
        "stratum",
        "dirty",
        "mixed",
        "environment",
        "nan",
        "order",
        "ratio",
        "annotation",
        "libraries",
        "device",
    ],
)
def test_parity_validator_rejects_incomplete_or_incompatible_evidence(
    tmp_path: Path, mutation: str
) -> None:
    report = copy.deepcopy(_passing_report(tmp_path))
    if mutation == "missing":
        del report["layers"]["pooled_head_input"]
    elif mutation == "failed":
        report["layers"]["person_tracking"]["passed"] = False
    elif mutation == "relaxed":
        report["layers"]["action_head"]["rtol"] = 1e-3
    elif mutation == "duplicate":
        report["panel"]["sample_ids"][1] = report["panel"]["sample_ids"][0]
    elif mutation == "stratum":
        report["panel"]["samples"][0]["frames"] = 100
    elif mutation == "dirty":
        report["provenance"]["git_dirty"] = True
    elif mutation == "mixed":
        report["configuration"]["mixed_precision"] = True
    elif mutation == "environment":
        report["environment"]["cuda_matmul_allow_tf32"] = True
    elif mutation == "nan":
        report["layers"]["person_tracking"]["max_abs_error"] = float("nan")
    elif mutation == "ratio":
        report["layers"]["person_tracking"]["max_tolerance_ratio"] = 1.001
    elif mutation == "annotation":
        report["panel"]["samples"][0]["annotation_index"] += 1
    elif mutation == "libraries":
        report["environment"]["torch"] = "changed"
    elif mutation == "device":
        report["configuration"]["device"] = "mps"
    else:
        report["panel"]["sample_order_sha256"] = "0" * 64
    path = tmp_path / "parity.json"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        validate_parity_report(path, report["bindings"])


@pytest.mark.parametrize(
    "source", ["manifest-set.json", "source-inventory.jsonl", "final-train.jsonl"]
)
def test_parity_rehashes_each_bound_panel_source(tmp_path: Path, source: str) -> None:
    report = _passing_report(tmp_path)
    path = tmp_path / "parity.json"
    path.write_text(json.dumps(report))
    changed = tmp_path / source
    changed.write_text(changed.read_text() + "\n")
    with pytest.raises(ValueError, match="changed"):
        validate_parity_report(path, report["bindings"])


@pytest.mark.parametrize("fail_layer", [False, True])
def test_parity_runner_preserves_immutable_pass_or_failure_report(
    tmp_path: Path,
    repository_root: Path,
    protocol_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fail_layer: bool,
) -> None:
    import pose_embed.models.action_head as head_module
    import pose_embed.models.motionbert as encoder_module
    import pose_embed.motionbert_inputs as input_module
    import pose_embed.motionbert_parity as parity_module

    root = repository_root / ".cache/upstreams/MotionBERT"
    if not root.is_dir():
        pytest.skip("pinned upstream checkout is not fetched")
    upstream, action = _upstream_oracles(root)
    template = _passing_report(tmp_path)
    inventory = _inventory()
    rng = np.random.default_rng(7)
    annotations = [
        {
            "keypoint": rng.uniform(0, 1000, row.keypoint_shape).astype(np.float32),
            "keypoint_score": rng.uniform(0, 1, row.keypoint_score_shape).astype(
                np.float32
            ),
            "img_shape": row.image_shape,
            "total_frames": row.total_frames,
        }
        for row in inventory
    ]
    inputs = SimpleNamespace(
        protocol=load_protocol(protocol_path),
        data_root=tmp_path,
        artifact_root=tmp_path,
        manifest_set_path=tmp_path / "manifest-set.json",
        inventory=inventory,
        manifests={"final-train.jsonl": _manifests(inventory)},
        annotations=annotations,
    )

    class Encoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pre_logits = nn.Linear(3, 4)

        def get_representation(self, poses: torch.Tensor) -> torch.Tensor:
            return self.pre_logits(poses)

    monkeypatch.setattr(input_module, "load_motionbert_inputs", lambda *_args: inputs)
    monkeypatch.setattr(
        input_module, "build_motionbert_bindings", lambda *_args: template["bindings"]
    )
    monkeypatch.setattr(
        encoder_module,
        "load_frozen_encoder",
        lambda *_args, **_kwargs: (
            Encoder().requires_grad_(False).eval(),
            {"upstream_root": str(root)},
        ),
    )
    monkeypatch.setattr(
        encoder_module, "inference_environment", lambda _device: template["environment"]
    )
    monkeypatch.setattr(
        head_module,
        "ActionHeadEmbed",
        lambda: ActionHeadEmbed(representation_dimension=4, embedding_dimension=8),
    )
    monkeypatch.setattr(
        parity_module,
        "_upstream_oracles",
        lambda _root: (
            upstream,
            SimpleNamespace(
                ActionNet=lambda encoder, **kwargs: action.ActionNet(
                    encoder, dim_rep=4, hidden_dim=8, **kwargs
                )
            ),
        ),
    )
    monkeypatch.setattr(
        parity_module, "capture_provenance", lambda **_kwargs: template["provenance"]
    )
    if fail_layer:

        def fail(*_args: object) -> None:
            raise ValueError("test parity error")

        monkeypatch.setattr(parity_module, "_model_checks", fail)
    destination = tmp_path / "parity.json"
    if fail_layer:
        with pytest.raises(ValueError, match="test parity error"):
            run_motionbert_parity(
                protocol_path=protocol_path,
                manifest_set_path=inputs.manifest_set_path,
                output_path=destination,
                device="cpu",
            )
        report = json.loads(destination.read_text())
        assert report["status"] == "failed"
        assert report["error"]["type"] == "ValueError"
    else:
        run_motionbert_parity(
            protocol_path=protocol_path,
            manifest_set_path=inputs.manifest_set_path,
            output_path=destination,
            device="cpu",
        )
        assert (
            validate_parity_report(destination, template["bindings"])["status"]
            == "passed"
        )
    original = destination.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        run_motionbert_parity(
            protocol_path=protocol_path,
            manifest_set_path=inputs.manifest_set_path,
            output_path=destination,
            device="cpu",
        )
    assert destination.read_bytes() == original
