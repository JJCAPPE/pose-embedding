"""Result-blind, layer-by-layer compatibility checks for frozen MotionBERT."""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import math
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from pose_embed.data.inventory import NTUInventoryRecord, load_inventory
from pose_embed.data.manifest import ManifestRecord, load_manifest
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.provenance import (
    capture_provenance,
    require_path_within,
    sha256_file,
    write_immutable_json,
)

PANEL_SELECTION = "protocol-v1|week-3-parity-v1"
_PREPROCESSING_LAYERS = (
    "camera_normalization",
    "person_tracking",
    "coordinate_mapping",
    "temporal_sampling",
    "single_person_padding",
    "spatial_normalization",
)
_EXACT_LAYERS = ("tracking_indices", "temporal_indices", "confidence_mapping")
_MODEL_LAYERS = ("encoder_representation", "pooled_head_input", "action_head")
_LAYERS = (*_PREPROCESSING_LAYERS, *_EXACT_LAYERS, *_MODEL_LAYERS)


def _order_hash(sample_ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(sample_ids).encode()).hexdigest()


def _stratum(people: int, frames: int) -> str:
    duration = "lt100" if frames < 100 else "eq100" if frames == 100 else "gt100"
    return f"{people}-person-{duration}"


def select_parity_panel(
    inventory: Sequence[NTUInventoryRecord],
    final_train: Sequence[ManifestRecord],
) -> list[NTUInventoryRecord]:
    """Select eight samples per metadata stratum, preserving manifest order."""
    by_id = {row.sample_id: row for row in inventory}
    manifest_ids = [row.sample_id for row in final_train]
    if len(set(manifest_ids)) != len(manifest_ids):
        raise ValueError("parity source manifest contains duplicate sample IDs")
    groups: dict[str, list[NTUInventoryRecord]] = {}
    for row in final_train:
        if row.split != "final_train" or row.ntu.action % 6 == 1:
            raise ValueError("parity panel requires auxiliary final-training samples")
        record = by_id.get(row.sample_id)
        if record is None:
            raise ValueError("parity manifest sample is absent from the inventory")
        groups.setdefault(
            _stratum(record.pose_track_count, record.total_frames), []
        ).append(record)
    selected: set[str] = set()
    for people in (1, 2):
        for frames in (99, 100, 101):
            name = _stratum(people, frames)
            rows = groups.get(name, [])
            if len(rows) < 8:
                raise ValueError(
                    f"parity stratum {name} requires at least eight samples"
                )
            rows = sorted(
                rows,
                key=lambda row: (
                    hashlib.sha256(
                        f"{PANEL_SELECTION}|{row.sample_id}".encode()
                    ).digest(),
                    row.sample_id,
                ),
            )
            selected.update(row.sample_id for row in rows[:8])
    return [by_id[sample_id] for sample_id in manifest_ids if sample_id in selected]


def _tracking_oracle(camera: np.ndarray) -> np.ndarray:
    people, frames = camera.shape[:2]
    indices = np.broadcast_to(np.arange(people)[:, None], (people, frames)).copy()
    if people == 2:
        same = np.linalg.norm(camera[0, 1:] - camera[0, :-1], axis=-1).sum(axis=-1)
        other = np.linalg.norm(camera[0, 1:] - camera[1, :-1], axis=-1).sum(axis=-1)
        swaps = np.cumsum(same > other) % 2
        indices[0, 1:] = swaps
        indices[1, 1:] = 1 - swaps
    return indices


def _confidence_oracle(scores: np.ndarray, tracking: np.ndarray) -> np.ndarray:
    """Independent explicit H36M source rule, including four-source belly."""
    tracked = scores[tracking, np.arange(scores.shape[1])[None, :]]
    direct = tracked[
        ..., [11, 12, 14, 16, 11, 13, 15, 11, 5, 0, 1, 5, 7, 9, 6, 8, 10]
    ].copy()
    direct[..., 0] = np.minimum(tracked[..., 11], tracked[..., 12])
    direct[..., 7] = np.minimum.reduce(tracked[..., [11, 12, 5, 6]], axis=-1)
    direct[..., 8] = np.minimum(tracked[..., 5], tracked[..., 6])
    direct[..., 10] = np.minimum(tracked[..., 1], tracked[..., 2])
    return direct


def _upstream_oracles(root: Path) -> tuple[Any, Any]:
    sys.path.insert(0, str(root))
    try:
        data = importlib.import_module("lib.data.dataset_action")
        action = importlib.import_module("lib.model.model_action")
    finally:
        sys.path.remove(str(root))
    for module, suffix in (
        (data, "lib/data/dataset_action.py"),
        (action, "lib/model/model_action.py"),
    ):
        if Path(inspect.getfile(module)).resolve() != (root / suffix).resolve():
            raise ValueError("parity oracle imported outside the pinned checkout")
    return data, action


def _compare(
    layers: dict[str, dict[str, Any]],
    name: str,
    actual: np.ndarray | torch.Tensor,
    expected: np.ndarray | torch.Tensor,
) -> None:
    def array(value: np.ndarray | torch.Tensor) -> np.ndarray:
        return (
            value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else value
        )

    actual, expected = array(actual), array(expected)
    atol = 0.0 if name in _EXACT_LAYERS else 1e-6
    rtol = 0.0 if name in _EXACT_LAYERS else 1e-5 if name in _MODEL_LAYERS else 1e-6
    record = layers.setdefault(
        name,
        {
            "checks": 0,
            "passed": True,
            "atol": atol,
            "rtol": rtol,
            "max_abs_error": 0.0,
            "max_tolerance_ratio": 0.0,
        },
    )
    valid = (
        actual.shape == expected.shape
        and np.isfinite(actual).all()
        and np.isfinite(expected).all()
    )
    if valid:
        difference = np.abs(actual.astype(np.float64) - expected.astype(np.float64))
        error = float(np.max(difference))
        record["max_abs_error"] = max(record["max_abs_error"], error)
        if name not in _EXACT_LAYERS:
            ratio = float(np.max(difference / (atol + rtol * np.abs(expected))))
            record["max_tolerance_ratio"] = max(record["max_tolerance_ratio"], ratio)
        valid = bool(
            np.array_equal(actual, expected) if name in _EXACT_LAYERS else ratio <= 1
        )
    record["checks"] += 1
    record["passed"] = bool(record["passed"] and valid)
    if not valid:
        raise ValueError(f"MotionBERT parity failed at {name}")


def _preprocessing_reference(
    annotation: Mapping[str, Any], upstream: Any
) -> dict[str, np.ndarray]:
    camera = upstream.make_cam(annotation["keypoint"], annotation["img_shape"])
    tracked = upstream.human_tracking(camera)
    mapped = upstream.coco2h36m(tracked)
    tracking = _tracking_oracle(camera)
    confidence = _confidence_oracle(annotation["keypoint_score"], tracking)
    indices = np.asarray(
        upstream.resample(annotation["total_frames"], 100, randomness=False)
    )
    sampled = np.concatenate(
        (mapped[:, indices], confidence[:, indices, :, None]), axis=-1
    )
    padded = sampled
    if sampled.shape[0] == 1:
        padded = np.concatenate((sampled, np.zeros_like(sampled)), axis=0)
    padded = padded.astype(np.float32)
    # Supply corrected confidence to the spatial oracle, as the protocol requires.
    spatial = upstream.crop_scale(padded, scale_range=[1, 1]).astype(np.float32)
    return {
        "camera_normalization": camera,
        "person_tracking": tracked,
        "coordinate_mapping": mapped,
        "confidence_mapping": confidence,
        "tracking_indices": tracking,
        "temporal_indices": indices,
        "temporal_sampling": sampled,
        "single_person_padding": padded,
        "spatial_normalization": spatial,
    }


def _confidence_fixtures(
    protocol: Any, preprocess: Any, layers: dict[str, Any]
) -> None:
    scores = np.arange(17, dtype=np.float32) / 16
    expected = (
        np.array(
            [11, 12, 14, 16, 11, 13, 15, 5, 5, 0, 1, 5, 7, 9, 6, 8, 10],
            dtype=np.float32,
        )
        / 16
    )
    for zero_hip in (False, True):
        source = scores.copy()
        target = expected.copy()
        if zero_hip:
            source[11] = 0
            target[[0, 4, 7]] = 0
        annotation = {
            "keypoint": np.arange(34, dtype=np.float32).reshape(1, 1, 17, 2),
            "keypoint_score": source.reshape(1, 1, 17),
            "img_shape": (100, 100),
            "total_frames": 1,
        }
        _, stages = preprocess(annotation, protocol, return_stages=True)
        _compare(
            layers,
            "confidence_mapping",
            stages["confidence_mapping"],
            target.reshape(1, 1, 17),
        )


def _model_checks(
    poses: torch.Tensor, encoder: Any, head: Any, reference: Any, layers: dict[str, Any]
) -> None:
    from pose_embed.models.action_head import pool_action_features

    captured: dict[str, torch.Tensor] = {}

    def capture_representation(
        _module: Any, _inputs: Any, output: torch.Tensor
    ) -> None:
        captured["representation"] = output

    def capture_pool(_module: Any, inputs: tuple[torch.Tensor, ...]) -> None:
        captured["pool"] = inputs[0]

    # get_representation calls forward directly, bypassing the encoder's hooks.
    # pre_logits produces the representation used by upstream ActionNet.
    batch, people, frames, joints, channels = poses.shape
    with torch.inference_mode():
        represented = encoder.get_representation(
            poses.reshape(batch * people, frames, joints, channels)
        )
        represented = represented.reshape(batch, people, frames, joints, -1)
        pooled = pool_action_features(represented)
        embedding = head(represented)
        representation_hook = encoder.pre_logits.register_forward_hook(
            capture_representation
        )
        pool_hook = reference.head.fc1.register_forward_pre_hook(capture_pool)
        try:
            expected = reference(poses)
        finally:
            representation_hook.remove()
            pool_hook.remove()
    _compare(
        layers,
        "encoder_representation",
        represented,
        captured["representation"].reshape_as(represented),
    )
    _compare(layers, "pooled_head_input", pooled, captured["pool"])
    _compare(layers, "action_head", embedding, expected)


def run_motionbert_parity(
    *,
    protocol_path: str | Path,
    manifest_set_path: str | Path,
    output_path: str | Path,
    device: str = "cuda",
) -> dict[str, Any]:
    """Verify the fixed auxiliary panel and preserve immutable parity evidence."""
    from pose_embed.data.motionbert import preprocess_annotation
    from pose_embed.models.action_head import ActionHeadEmbed
    from pose_embed.models.motionbert import (
        configure_deterministic_inference,
        inference_environment,
        load_frozen_encoder,
    )
    from pose_embed.motionbert_inputs import (
        build_motionbert_bindings,
        load_motionbert_inputs,
    )

    started = datetime.now(UTC)
    inputs = load_motionbert_inputs(protocol_path, manifest_set_path)
    destination = require_path_within(
        output_path, inputs.artifact_root, label="parity report"
    )
    if destination.exists():
        raise ValueError("refusing to overwrite immutable parity report")
    panel = select_parity_panel(inputs.inventory, inputs.manifests["final-train.jsonl"])
    configure_deterministic_inference()
    encoder, assets = load_frozen_encoder(inputs.data_root, device=device)
    upstream, action = _upstream_oracles(Path(assets["upstream_root"]))
    bindings = build_motionbert_bindings(inputs, assets)
    sample_ids = [row.sample_id for row in panel]
    configuration = {
        "device": str(device),
        "dtype": "float32",
        "batch_size": 32,
        "head_seed": 7,
        "deterministic_algorithms": True,
        "mixed_precision": False,
        "tf32": False,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "failed",
        "bindings": bindings,
        "configuration": configuration,
        "environment": inference_environment(device),
        "panel": {
            "count": len(panel),
            "selection": PANEL_SELECTION,
            "source": "final-train.jsonl",
            "sample_ids": sample_ids,
            "sample_order_sha256": _order_hash(sample_ids),
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
        "layers": {},
    }
    try:
        assert inputs.annotations is not None
        tensors = []
        _confidence_fixtures(inputs.protocol, preprocess_annotation, report["layers"])
        for row in panel:
            annotation = inputs.annotations[row.annotation_index]
            tensor, stages = preprocess_annotation(
                annotation, inputs.protocol, return_stages=True
            )
            reference_stages = _preprocessing_reference(annotation, upstream)
            for name, expected in reference_stages.items():
                _compare(report["layers"], name, stages[name], expected)
            tensors.append(tensor)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(7)
            head = ActionHeadEmbed().to(device).eval()
            reference = action.ActionNet(encoder, version="embed").to(device).eval()
        reference.head.fc1.load_state_dict(head.projection.state_dict(), strict=True)
        for start in range(0, len(tensors), 32):
            poses = torch.from_numpy(np.stack(tensors[start : start + 32])).to(device)
            _model_checks(poses, encoder, head, reference, report["layers"])
        report["status"] = "passed"
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report["provenance"] = capture_provenance(
            command="features parity",
            configuration=configuration,
            inputs=[Path(protocol_path).resolve(), inputs.manifest_set_path],
            started_at=started,
            ended_at=datetime.now(UTC),
            repository=Path(__file__).resolve().parents[2],
        )
        write_immutable_json(destination, report)
    return report


def validate_parity_report(
    report_path: str | Path, expected_bindings: Mapping[str, str]
) -> dict[str, Any]:
    """Require a complete successful report bound to the current verified inputs."""
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("schema_version") != 1 or report.get("status") != "passed":
        raise ValueError("MotionBERT parity report is not a passing schema-v1 report")
    if not expected_bindings or report.get("bindings") != dict(expected_bindings):
        raise ValueError("MotionBERT parity report bindings differ from current inputs")
    configuration = report.get("configuration", {})
    required = {
        "dtype": "float32",
        "batch_size": 32,
        "head_seed": 7,
        "deterministic_algorithms": True,
        "mixed_precision": False,
        "tf32": False,
    }
    if any(
        configuration.get(key) != value for key, value in required.items()
    ) or not configuration.get("device"):
        raise ValueError(
            "MotionBERT parity configuration differs from the fixed contract"
        )
    environment = report.get("environment", {})
    if (
        environment.get("dtype") != "float32"
        or environment.get("batch_size") != 32
        or environment.get("deterministic_algorithms") is not True
        or environment.get("cuda_matmul_allow_tf32") is not False
        or environment.get("cudnn_allow_tf32") is not False
        or environment.get("cudnn_benchmark") is not False
        or environment.get("deterministic_warn_only") is not False
        or environment.get("cudnn_deterministic") is not True
        or environment.get("float32_matmul_precision") != "highest"
        or environment.get("cublas_workspace_config") != ":4096:8"
    ):
        raise ValueError("MotionBERT parity inference environment is invalid")
    try:
        device = torch.device(configuration["device"])
    except (TypeError, RuntimeError) as exc:
        raise ValueError("MotionBERT parity device is invalid") from exc
    if device.type not in {"cpu", "cuda"} or device.type != environment.get(
        "device_type"
    ):
        raise ValueError("MotionBERT parity device is invalid")
    if device.type == "cuda" and (
        not isinstance(environment.get("device_index"), int)
        or environment["device_index"] < 0
        or (device.index is not None and device.index != environment["device_index"])
        or not environment.get("cuda_device_name")
    ):
        raise ValueError("MotionBERT parity CUDA device evidence is invalid")
    if device.type == "cpu" and any(
        environment.get(key) is not None
        for key in ("device_index", "cuda_device_name", "cuda_device_uuid")
    ):
        raise ValueError("MotionBERT parity CPU device evidence is invalid")
    if (
        report.get("confidence_compatibility")
        != "local_corrected_h36m_mapping_not_upstream_bit_parity"
    ):
        raise ValueError(
            "parity report must declare the corrected confidence semantics"
        )
    panel = report.get("panel", {})
    sample_ids, samples = panel.get("sample_ids", []), panel.get("samples", [])
    if (
        panel.get("count") != 48
        or len(sample_ids) != 48
        or len(set(sample_ids)) != 48
        or panel.get("selection") != PANEL_SELECTION
        or panel.get("source") != "final-train.jsonl"
        or panel.get("sample_order_sha256") != _order_hash(sample_ids)
        or len(samples) != 48
        or [row.get("sample_id") for row in samples] != sample_ids
    ):
        raise ValueError("MotionBERT parity panel identity or order is invalid")
    strata: Counter[str] = Counter()
    for row in samples:
        if parse_ntu_sample_id(row["sample_id"]).action % 6 == 1:
            raise ValueError("MotionBERT parity panel contains a novel-test sample")
        if (
            row.get("people") not in (1, 2)
            or not isinstance(row.get("frames"), int)
            or row["frames"] <= 0
        ):
            raise ValueError("MotionBERT parity panel metadata is invalid")
        strata[_stratum(row["people"], row["frames"])] += 1
    if len(strata) != 6 or set(strata.values()) != {8}:
        raise ValueError("MotionBERT parity panel must have eight samples per stratum")
    layers = report.get("layers", {})
    if set(layers) != set(_LAYERS):
        raise ValueError("MotionBERT parity report is missing required layers")
    for name, layer in layers.items():
        checks = (
            2 if name in _MODEL_LAYERS else 50 if name == "confidence_mapping" else 48
        )
        atol = 0.0 if name in _EXACT_LAYERS else 1e-6
        rtol = 0.0 if name in _EXACT_LAYERS else 1e-5 if name in _MODEL_LAYERS else 1e-6
        error = layer.get("max_abs_error")
        ratio = layer.get("max_tolerance_ratio")
        if (
            layer.get("passed") is not True
            or layer.get("checks") != checks
            or layer.get("atol") != atol
            or layer.get("rtol") != rtol
            or not isinstance(error, (int, float))
            or not math.isfinite(error)
            or error < 0
            or (name in _EXACT_LAYERS and error != 0)
            or not isinstance(ratio, (int, float))
            or not math.isfinite(ratio)
            or not 0 <= ratio <= 1
        ):
            raise ValueError(f"MotionBERT parity layer evidence is invalid: {name}")
    provenance = report.get("provenance", {})
    if provenance.get("git_dirty") is not False or not provenance.get("git_sha"):
        raise ValueError("MotionBERT parity requires clean code provenance")
    runtime = provenance.get("environment", {})
    versions = runtime.get("dependencies", {})
    torch_runtime = environment.get("torch")
    torch_package = versions.get("torch")
    if (
        not environment.get("numpy")
        or environment["numpy"] != versions.get("numpy")
        or not isinstance(torch_runtime, str)
        or not isinstance(torch_package, str)
        or torch_runtime != runtime.get("torch")
        # PyPI CUDA wheels expose e.g. 2.9.1+cu128 at runtime but 2.9.1
        # in package metadata. The runtime comparison retains the CUDA suffix.
        or torch_runtime.split("+", maxsplit=1)[0]
        != torch_package.split("+", maxsplit=1)[0]
        or environment.get("cuda") != runtime.get("cuda_version")
        or not environment.get("hostname")
    ):
        raise ValueError(
            "MotionBERT parity library environment differs from provenance"
        )
    recorded_inputs = provenance.get("inputs", {})
    candidates = [
        Path(path)
        for path, digest in recorded_inputs.items()
        if digest == expected_bindings.get("manifest_set_sha256")
    ]
    if len(candidates) != 1 or any(
        sha256_file(path) != digest for path, digest in recorded_inputs.items()
    ):
        raise ValueError("MotionBERT parity source inputs are missing or changed")
    bundle_path = candidates[0]
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    inventory_path = bundle_path.parent / "source-inventory.jsonl"
    manifest_path = bundle_path.parent / "final-train.jsonl"
    files = bundle.get("files", {})
    if (
        bundle.get("protocol_sha256") != expected_bindings.get("protocol_sha256")
        or sha256_file(inventory_path)
        != expected_bindings.get("source_inventory_sha256")
        or sha256_file(inventory_path)
        != files.get("source-inventory.jsonl", {}).get("sha256")
        or sha256_file(manifest_path)
        != files.get("final-train.jsonl", {}).get("sha256")
    ):
        raise ValueError("MotionBERT parity bound source manifests have changed")
    selected = select_parity_panel(
        load_inventory(inventory_path), load_manifest(manifest_path)
    )
    expected_samples = [
        {
            "sample_id": row.sample_id,
            "people": row.pose_track_count,
            "frames": row.total_frames,
            "annotation_index": row.annotation_index,
        }
        for row in selected
    ]
    if samples != expected_samples:
        raise ValueError(
            "MotionBERT parity panel differs from the fixed source selection"
        )
    return report
