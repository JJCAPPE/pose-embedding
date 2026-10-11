"""Development-only geometry panel and accuracy-independent damage telemetry."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

from pose_embed.corruptions.pose import (
    apply_corruption_v3,
    corruption_randomness_v3,
    torso_scale_v3,
    validate_pose_v3,
)
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

LEVELS = {
    "coordinate_jitter": (0.01, 0.025, 0.05),
    "joint_mask": (3, 6, 8),
    "frame_mask": (10, 25, 40),
}


def geometry_damage(
    clean: torch.Tensor,
    corrupted: torch.Tensor,
    family: str,
    scale: float | None,
) -> dict[str, Any]:
    """Measure effective damage over originally observed person/frame/joint rows."""
    validate_pose_v3(clean)
    validate_pose_v3(corrupted)
    if family not in LEVELS:
        raise ValueError("unknown geometry corruption family")
    observed = clean[..., 2] > 0
    count = int(observed.sum())
    newly_masked = int((observed & (corrupted[..., 2] == 0)).sum())
    fallback_used = False
    if family == "coordinate_jitter":
        own_scale = torso_scale_v3(clean)
        if scale is None or not math.isfinite(scale) or scale <= 0:
            raise ValueError("jitter damage requires the actual positive torso scale")
        if own_scale is not None and scale != own_scale:
            raise ValueError("jitter damage scale differs from the clean own scale")
        if not torch.equal(
            clean[..., 2].view(torch.int32), corrupted[..., 2].view(torch.int32)
        ) or not torch.equal(
            clean[~observed].view(torch.int32), corrupted[~observed].view(torch.int32)
        ):
            raise ValueError("jitter changed confidence or an unobserved location")
        fallback_used = own_scale is None
        squared = (corrupted[..., :2].double() - clean[..., :2].double()).square()
        damage = (
            math.sqrt(float(squared[observed].sum()) / (2 * count)) / scale
            if count
            else None
        )
    else:
        changed = (clean.view(torch.int32) != corrupted.view(torch.int32)).any(dim=-1)
        if bool((corrupted[changed] != 0).any()):
            raise ValueError("masking changed an observation without zeroing it")
        damage = newly_masked / count if count else None
    if damage is not None and not math.isfinite(damage):
        raise ValueError("nonfinite geometry damage cannot be excluded")
    return {
        "family": family,
        "original_observed_count": count,
        "newly_masked_observed_count": newly_masked,
        "damage": damage,
        "fallback_used": fallback_used,
    }


def summarize_geometry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep undefined denominators separate and use linear per-query quantiles."""
    if not rows or len({row["family"] for row in rows}) != 1:
        raise ValueError("geometry summary requires one nonempty corruption family")
    finite = [row["damage"] for row in rows if row["damage"] is not None]
    if any(not math.isfinite(value) or value < 0 for value in finite):
        raise ValueError("nonfinite or negative geometry damage cannot be summarized")
    fallback_count = sum(row["fallback_used"] for row in rows)
    return {
        "family": rows[0]["family"],
        "query_count": len(rows),
        "finite_count": len(finite),
        "undefined_count": len(rows) - len(finite),
        "zero_damage_count": sum(value == 0 for value in finite),
        "fallback_count": fallback_count,
        "fallback_fraction": fallback_count / len(rows),
        "original_observed_count": sum(row["original_observed_count"] for row in rows),
        "newly_masked_observed_count": sum(
            row["newly_masked_observed_count"] for row in rows
        ),
        **dict(
            zip(
                ("minimum", "median", "p95", "maximum"),
                np.quantile(finite, (0, 0.5, 0.95, 1), method="linear").tolist()
                if finite
                else (None,) * 4,
                strict=True,
            )
        ),
    }


def select_geometry_panel(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Freeze two hashed queries per development action plus declared sentinels."""
    by_id = {row["sample_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("geometry panel metadata repeats sample IDs")
    by_action: dict[int, list[str]] = {}
    for sample_id, row in by_id.items():
        parsed = parse_ntu_sample_id(sample_id)
        if parsed.sample_id != sample_id:
            raise ValueError("geometry panel requires canonical IDs")
        by_action.setdefault(parsed.action, []).append(sample_id)
        if (
            not 0 <= row["second_person_support"] <= row["observed_support"] <= 3400
            or row["second_person_support"] > 1700
        ):
            raise ValueError("invalid geometry panel support")
        scale = row["own_scale"]
        if scale is not None and (not math.isfinite(scale) or scale <= 0):
            raise ValueError("invalid geometry panel own scale")
    if set(by_action) != set(range(2, 121, 6)) or any(
        len(ids) < 2 for ids in by_action.values()
    ):
        raise ValueError("geometry panel needs two queries in every development action")

    def order(sample_id: str) -> tuple[str, str]:
        return (
            hashlib.sha256(
                f"protocol-v3|geometry-panel-v1|{sample_id}".encode()
            ).hexdigest(),
            sample_id,
        )

    base = {
        sample_id
        for ids in by_action.values()
        for sample_id in sorted(ids, key=order)[:2]
    }
    ordered = sorted(by_id, key=order)
    sentinels: dict[str, str | None] = {}
    for field, prefix in (
        ("observed_support", "support"),
        ("second_person_support", "second_person_support"),
        ("own_scale", "own_scale"),
    ):
        valid = [
            sample_id
            for sample_id in ordered
            if by_id[sample_id][field] is not None and by_id[sample_id][field] > 0
        ]
        sentinels[f"minimum_positive_{prefix}"] = (
            min(valid, key=lambda sample_id: by_id[sample_id][field]) if valid else None
        )
        maximum = [
            sample_id for sample_id in ordered if by_id[sample_id][field] is not None
        ]
        sentinels[f"maximum_{prefix}"] = (
            max(maximum, key=lambda sample_id: by_id[sample_id][field])
            if maximum
            else None
        )
    sentinels["invalid_own_scale"] = next(
        (
            sample_id
            for sample_id in ordered
            if by_id[sample_id]["own_scale"] is None
            and by_id[sample_id]["observed_support"] > 0
        ),
        None,
    )
    sentinels["all_missing"] = next(
        (
            sample_id
            for sample_id in ordered
            if by_id[sample_id]["observed_support"] == 0
        ),
        None,
    )
    return {
        "sample_ids": sorted(
            base
            | {sample_id for sample_id in sentinels.values() if sample_id is not None}
        ),
        "base_sample_ids": sorted(base),
        "sentinels": sentinels,
        "absent_categories": [
            name for name, sample_id in sentinels.items() if sample_id is None
        ],
    }


def verify_geometry_case(
    clean: torch.Tensor, sample_id: str, fallback_scale: float
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """Check the complete nested operator panel and retain all tensor hashes."""
    validate_pose_v3(clean)
    tensors = {"clean": clean.numpy()}
    rows = []
    own_scale = torso_scale_v3(clean)
    scale = own_scale if own_scale is not None else fallback_scale
    for family, levels in LEVELS.items():
        zero = apply_corruption_v3(
            clean, family=family, severity=0, sample_id=sample_id
        )
        if zero.numpy().tobytes() != clean.numpy().tobytes():
            raise ValueError("geometry severity zero changed the clean tensor")
        previous_mask = torch.zeros(clean.shape[:-1], dtype=torch.bool)
        unsigned, seed = corruption_randomness_v3(sample_id, family)
        generator = torch.Generator().manual_seed(seed)
        field = torch.randn(
            clean[..., :2].shape, generator=generator, dtype=torch.float32
        )
        for level in levels:
            output = apply_corruption_v3(
                clean,
                family=family,
                severity=level,
                sample_id=sample_id,
                fallback_scale=fallback_scale,
            )
            if family == "coordinate_jitter":
                expected = torch.where(
                    clean[..., 2:3] > 0,
                    clean[..., :2] + field * scale * level,
                    clean[..., :2],
                )
                if not torch.equal(
                    output[..., :2].view(torch.int32), expected.view(torch.int32)
                ):
                    raise ValueError("geometry jitter did not retain its shared field")
            else:
                probe = apply_corruption_v3(
                    torch.ones_like(clean),
                    family=family,
                    severity=level,
                    sample_id=sample_id,
                )
                mask = probe[..., 2] == 0
                nominal = 2 * (100 if family == "joint_mask" else 17) * level
                if int(mask.sum()) != nominal or bool((previous_mask & ~mask).any()):
                    raise ValueError(
                        "geometry masks have wrong counts or are not nested"
                    )
                expected = clean.clone()
                expected[mask] = 0
                if not torch.equal(
                    expected.view(torch.int32), output.view(torch.int32)
                ):
                    raise ValueError("geometry mask changed an unmasked observation")
                if family == "frame_mask":
                    start = unsigned * (101 - level) // 2**64
                    if not bool(mask[:, start : start + level].all()):
                        raise ValueError(
                            "geometry frame boundary differs from the fixed draw"
                        )
                previous_mask = mask
            condition = f"{family}:{level}"
            tensors[condition] = output.numpy()
            rows.append(
                {
                    "sample_id": sample_id,
                    "condition": condition,
                    "nominal_severity": level,
                    **geometry_damage(clean, output, family, scale),
                }
            )
    return tensors, rows


def _load_panel_inputs(protocol_path: str | Path, manifest_set_path: str | Path):
    from pose_embed.config import load_protocol
    from pose_embed.data.manifest import load_manifest
    from pose_embed.motionbert_inputs import load_motionbert_inputs
    from pose_embed.protocol_v3 import require_v3_design

    protocol = load_protocol(protocol_path)
    design = require_v3_design(protocol)
    if (
        torch.__version__.split("+")[0],
        np.__version__,
        f"{sys.version_info.major}.{sys.version_info.minor}",
    ) != (
        protocol.training.torch_version,
        protocol.training.numpy_version,
        protocol.training.python_version,
    ):
        raise ValueError("geometry requires the frozen Torch/NumPy/Python runtime")
    inputs = load_motionbert_inputs(protocol_path, manifest_set_path, novel=False)
    binding = design.manifests["development_queries"]
    manifest_path = inputs.artifact_root / binding.relative_path
    records = load_manifest(manifest_path)
    if any(
        row.split != "development_validation"
        or row.ntu.action not in protocol.dataset.development_validation_actions
        for row in records
    ):
        raise ValueError("geometry panel permits only development query poses")
    return inputs, records, manifest_path


def _panel_worker(
    protocol_path: str, manifest_set_path: str, panel_path: str, output_dir: str
) -> None:
    from pose_embed.data.motionbert import preprocess_annotation

    inputs, records, manifest_path = _load_panel_inputs(
        protocol_path, manifest_set_path
    )
    panel = json.loads(Path(panel_path).read_text())
    if (
        panel["manifest_sha256"] != sha256_file(manifest_path)
        or panel["selection_code_sha256"] != sha256_file(Path(__file__))
        or panel["bindings"] != inputs.bindings
        or panel["candidate_metadata"] != _panel_metadata(inputs, records)
        or any(
            panel[key] != value
            for key, value in select_geometry_panel(panel["candidate_metadata"]).items()
        )
    ):
        raise ValueError("frozen geometry panel provenance changed")
    selected = panel["sample_ids"]
    if (
        not 40 <= len(selected) <= 48
        or selected != sorted(set(selected))
        or not set(selected) <= {row.sample_id for row in records}
    ):
        raise ValueError("geometry panel includes unauthorized or duplicate query IDs")
    destination = require_path_within(
        output_dir,
        inputs.artifact_root
        / Path(inputs.protocol.test_access.resolved_protocol_relative_path).parent,
        label="geometry worker",
    )
    destination.mkdir(parents=True, exist_ok=False)
    by_id = {row.sample_id: row.annotation_index for row in inputs.inventory}
    tensors = {}
    rows = []
    assert inputs.annotations is not None and inputs.protocol.preparation is not None
    for sample_id in selected:
        clean = torch.from_numpy(
            preprocess_annotation(inputs.annotations[by_id[sample_id]], inputs.protocol)
        )
        case, damage = verify_geometry_case(
            clean, sample_id, inputs.protocol.preparation.fallback_value
        )
        tensors.update(
            {f"{sample_id}__{condition}": tensor for condition, tensor in case.items()}
        )
        rows.extend(damage)
    with (destination / "tensors.npz").open("xb") as stream:
        np.savez(stream, **tensors)
    tensor_hashes = {
        key: hashlib.sha256(value.tobytes()).hexdigest()
        for key, value in tensors.items()
    }
    with np.load(destination / "tensors.npz", allow_pickle=False) as archive:
        if tensor_hashes != {
            key: hashlib.sha256(archive[key].tobytes()).hexdigest()
            for key in archive.files
        }:
            raise ValueError("serialized geometry tensors changed")
    write_immutable_json(
        destination / "verification.json",
        {
            "panel_sha256": sha256_file(Path(panel_path)),
            "tensor_sha256": tensor_hashes,
            "tensor_archive_sha256": sha256_file(destination / "tensors.npz"),
            "rows": rows,
        },
    )


def run_geometry_panel(
    protocol_path: str | Path, manifest_set_path: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    """Freeze a metadata-selected panel before independent fresh-process checks."""
    inputs, records, manifest_path = _load_panel_inputs(
        protocol_path, manifest_set_path
    )
    destination = require_path_within(
        output_dir,
        inputs.artifact_root
        / Path(inputs.protocol.test_access.resolved_protocol_relative_path).parent,
        label="geometry panel",
    )
    destination.mkdir(parents=True, exist_ok=False)
    metadata = _panel_metadata(inputs, records)
    panel_path = destination / "panel.json"
    write_immutable_json(
        panel_path,
        {
            "schema_version": 1,
            "bindings": inputs.bindings,
            "manifest_sha256": sha256_file(manifest_path),
            "manifest_set_relative_path": str(
                inputs.manifest_set_path.relative_to(inputs.artifact_root)
            ),
            "selection_code_sha256": sha256_file(Path(__file__)),
            "candidate_metadata": metadata,
            **select_geometry_panel(metadata),
        },
    )
    # Release the auxiliary annotations before two sequential independent reloads.
    del inputs
    outputs = []
    for repeat in (1, 2):
        repeat_dir = destination / f"repeat-{repeat}"
        with (destination / f"repeat-{repeat}.log").open("xb") as log:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pose_embed.geometry_v3",
                    str(protocol_path),
                    str(manifest_set_path),
                    str(panel_path),
                    str(repeat_dir),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        outputs.append(json.loads((repeat_dir / "verification.json").read_text()))
    if any(
        outputs[0][key] != outputs[1][key]
        for key in ("panel_sha256", "tensor_sha256", "rows")
    ):
        raise ValueError("fresh-process geometry outputs or damage differ")
    summary = _geometry_summary(panel_path, outputs)
    write_immutable_json(destination / "summary.json", summary)
    return summary


def _geometry_summary(panel_path, outputs):
    destination = panel_path.parent
    return {
        "schema_version": 1,
        "panel_sha256": sha256_file(panel_path),
        "fresh_processes": 2,
        "exact_repeats": True,
        "tensor_count": len(outputs[0]["tensor_sha256"]),
        "conditions": {
            condition: summarize_geometry(
                [row for row in outputs[0]["rows"] if row["condition"] == condition]
            )
            for condition in sorted({row["condition"] for row in outputs[0]["rows"]})
        },
        "repeat_verification_sha256": [
            sha256_file(destination / f"repeat-{repeat}" / "verification.json")
            for repeat in (1, 2)
        ],
    }


def _panel_metadata(inputs, records):
    from pose_embed.data.motionbert import preprocess_annotation

    by_id = {row.sample_id: row.annotation_index for row in inputs.inventory}
    metadata = []
    assert inputs.annotations is not None
    for row in records:
        clean = torch.from_numpy(
            preprocess_annotation(
                inputs.annotations[by_id[row.sample_id]], inputs.protocol
            )
        )
        observed = clean[..., 2] > 0
        metadata.append(
            {
                "sample_id": row.sample_id,
                "observed_support": int(observed.sum()),
                "second_person_support": int(observed[1].sum()),
                "own_scale": torso_scale_v3(clean),
            }
        )
    return metadata


def validate_geometry_panel(summary_path: str | Path, protocol) -> dict[str, Any]:
    """Recheck bound metadata and both tensor archives without reopening poses."""
    from pose_embed.data.manifest import load_manifest
    from pose_embed.motionbert_inputs import (
        motionbert_code_digest,
        verify_manifest_bundle,
    )
    from pose_embed.protocol import protocol_digest, resolve_scientific_paths
    from pose_embed.protocol_v3 import require_v3_design

    root = resolve_scientific_paths(protocol).root
    design = require_v3_design(protocol)
    path = require_path_within(
        summary_path,
        root / Path(protocol.test_access.resolved_protocol_relative_path).parent,
        label="geometry evidence",
    )
    summary = json.loads(path.read_text())
    panel_path = path.parent / "panel.json"
    panel = json.loads(panel_path.read_text())
    bundle_path = require_path_within(
        root / panel["manifest_set_relative_path"], root, label="geometry manifests"
    )
    verify_manifest_bundle(protocol, bundle_path)
    manifest_path = root / design.manifests["development_queries"].relative_path
    records = load_manifest(manifest_path)
    metadata = panel["candidate_metadata"]
    if [row["sample_id"] for row in metadata] != [row.sample_id for row in records]:
        raise ValueError(
            "geometry metadata must describe every locked development query"
        )
    bindings = {
        "protocol_sha256": protocol_digest(protocol),
        "manifest_set_sha256": sha256_file(bundle_path),
        "source_inventory_sha256": sha256_file(
            bundle_path.parent / "source-inventory.jsonl"
        ),
        "aggregate_sha256": protocol.dataset.source_contract.aggregate_sha256,
        "missing_list_sha256": protocol.dataset.source_contract.missing_list_sha256,
        "code_sha256": motionbert_code_digest(),
        "dependency_lock_sha256": sha256_file(
            Path(__file__).resolve().parents[2] / "uv.lock"
        ),
    }
    expected_panel = {
        "schema_version": 1,
        "bindings": bindings,
        "manifest_sha256": sha256_file(manifest_path),
        "manifest_set_relative_path": str(bundle_path.relative_to(root)),
        "selection_code_sha256": sha256_file(Path(__file__)),
        "candidate_metadata": metadata,
        **select_geometry_panel(metadata),
    }
    if panel != expected_panel or summary["panel_sha256"] != sha256_file(panel_path):
        raise ValueError("geometry panel differs from source-derived frozen selection")
    tensors, rows = {}, []
    by_id = {row["sample_id"]: row for row in metadata}
    with np.load(path.parent / "repeat-1/tensors.npz", allow_pickle=False) as archive:
        for sample_id in panel["sample_ids"]:
            clean = torch.from_numpy(archive[f"{sample_id}__clean"])
            observed = clean[..., 2] > 0
            if by_id[sample_id] != {
                "sample_id": sample_id,
                "observed_support": int(observed.sum()),
                "second_person_support": int(observed[1].sum()),
                "own_scale": torso_scale_v3(clean),
            }:
                raise ValueError(
                    "geometry clean tensor differs from selection metadata"
                )
            case, damage = verify_geometry_case(
                clean, sample_id, protocol.preparation.fallback_value
            )
            tensors.update(
                {
                    f"{sample_id}__{condition}": tensor
                    for condition, tensor in case.items()
                }
            )
            rows.extend(damage)
    hashes = {
        key: hashlib.sha256(value.tobytes()).hexdigest()
        for key, value in tensors.items()
    }
    outputs = []
    for repeat in (1, 2):
        directory = path.parent / f"repeat-{repeat}"
        with np.load(directory / "tensors.npz", allow_pickle=False) as archive:
            if set(archive.files) != set(tensors) or any(
                archive[key].dtype != value.dtype
                or archive[key].shape != value.shape
                or archive[key].tobytes() != value.tobytes()
                for key, value in tensors.items()
            ):
                raise ValueError(
                    "geometry tensor archive differs from invariant replay"
                )
        expected = {
            "panel_sha256": sha256_file(panel_path),
            "tensor_sha256": hashes,
            "tensor_archive_sha256": sha256_file(directory / "tensors.npz"),
            "rows": rows,
        }
        if json.loads((directory / "verification.json").read_text()) != expected:
            raise ValueError("geometry per-case evidence differs from invariant replay")
        outputs.append(expected)
    if summary != _geometry_summary(panel_path, outputs):
        raise ValueError("geometry summary differs from recomputed evidence")
    return summary


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(
            "internal geometry worker requires protocol, manifests, panel and output"
        )
    _panel_worker(*sys.argv[1:])
