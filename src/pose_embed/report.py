"""Deterministic Markdown summary generation from immutable result JSON."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np
import torch
from pydantic import ValidationError

from pose_embed.artifacts import (
    sample_order_digest,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.config import load_protocol
from pose_embed.evaluation.analysis import (
    complete_core_curve_data,
    complete_core_error_data,
    primary_robustness_analysis,
)
from pose_embed.evaluation.metrics import evaluate_one_shot
from pose_embed.evaluation.result import EvaluationResult, ResultMetrics
from pose_embed.protocol import (
    EvaluationPlan,
    FinalRunSet,
    derive_core_failure_status,
    evaluation_plan_digest,
    final_run_for,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    resolve_scientific_paths,
    validate_evaluation_manifests,
    validate_exploratory_run_artifacts,
    validate_final_run_artifacts,
    validate_post_core_stretch_authorization,
    verify_protocol,
)
from pose_embed.provenance import RuntimeTelemetry, sha256_file, write_immutable_json
from pose_embed.test_access import TestOpeningLedger


def _load_result(path: Path) -> EvaluationResult:
    try:
        return EvaluationResult.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise ValueError(f"invalid result schema: {path}: {exc}") from exc


def _result_row(path: Path, result: EvaluationResult) -> dict[str, Any]:
    return {
        "file": str(path.resolve()),
        "sha256": sha256_file(path),
        "mode": result.mode,
        "protocol_sha256": result.protocol_sha256,
        "gallery_sample_order_sha256": result.gallery_sample_order_sha256,
        "query_sample_order_sha256": result.query_sample_order_sha256,
        "method": result.method,
        "seed": result.seed,
        "condition": result.condition,
        "query_definition": result.query_definition,
        "top1": result.metrics.top1,
        "mrr": result.metrics.mrr,
        "r_at_5": result.metrics.r_at_5,
        "queries": result.metrics.query_count,
    }


def _result_set_digest(rows: list[dict[str, Any]]) -> str:
    inputs = [{"file": row["file"], "sha256": row["sha256"]} for row in rows]
    encoded = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _payload_sha256(payload: object) -> str:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    return hashlib.sha256(encoded).hexdigest()


def _primary_analysis_payload(
    results: list[EvaluationResult],
    rows: list[dict[str, Any]],
    *,
    protocol_path: str | Path,
) -> dict[str, Any]:
    protocol = load_protocol(protocol_path)
    scientific_paths = resolve_scientific_paths(protocol)
    plan = load_evaluation_plan(scientific_paths.evaluation_plan)
    analysis = primary_robustness_analysis(
        results,
        seeds=plan.seeds,
        corruption_conditions=plan.conditions[1:],
        bootstrap_replicates=protocol.analysis.bootstrap_replicates,
        confidence_level=protocol.analysis.confidence_level,
    )
    payload = analysis.as_dict()
    payload.update(
        {
            "protocol_sha256": results[0].protocol_sha256,
            "evaluation_plan_sha256": results[0].evaluation_plan_sha256,
            "final_run_set_sha256": results[0].final_run_set_sha256,
            "result_set_sha256": _result_set_digest(rows),
            "inputs": [{"file": row["file"], "sha256": row["sha256"]} for row in rows],
        }
    )
    return payload


def _complete_curve_payload(
    results: list[EvaluationResult],
    *,
    plan: EvaluationPlan,
    result_set_sha256: str,
    primary_analysis_sha256: str,
) -> dict[str, Any]:
    payload = complete_core_curve_data(
        results,
        methods=plan.methods,
        seeds=plan.seeds,
        conditions=plan.conditions,
        query_definitions=plan.query_definitions,
        metrics=plan.metrics,
    )
    payload.update(
        {
            "protocol_sha256": results[0].protocol_sha256,
            "evaluation_plan_sha256": results[0].evaluation_plan_sha256,
            "final_run_set_sha256": results[0].final_run_set_sha256,
            "result_set_sha256": result_set_sha256,
            "primary_analysis_sha256": primary_analysis_sha256,
        }
    )
    return payload


def _complete_error_payload(
    results: list[EvaluationResult],
    *,
    plan: EvaluationPlan,
    novel_actions: tuple[int, ...],
    result_set_sha256: str,
) -> dict[str, Any]:
    payload = complete_core_error_data(
        results,
        methods=plan.methods,
        seeds=plan.seeds,
        conditions=plan.conditions,
        query_definitions=plan.query_definitions,
        actions=novel_actions,
    )
    payload.update(
        {
            "protocol_sha256": results[0].protocol_sha256,
            "evaluation_plan_sha256": results[0].evaluation_plan_sha256,
            "final_run_set_sha256": results[0].final_run_set_sha256,
            "result_set_sha256": result_set_sha256,
        }
    )
    return payload


def _telemetry_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    wall_times = [row["wall_time_seconds"] for row in rows]
    peaks: dict[str, int] = {}
    for row in rows:
        source = row["peak_memory_source"]
        peaks[source] = max(peaks.get(source, 0), row["peak_memory_bytes"])
    total = math.fsum(wall_times)
    return {
        "operation_count": len(rows),
        "total_wall_time_seconds": total,
        "mean_wall_time_seconds": total / len(rows),
        "maximum_peak_memory_bytes_by_source": {
            source: peaks[source] for source in sorted(peaks)
        },
    }


def _runtime_telemetry_payload(
    results: list[EvaluationResult],
    rows: list[dict[str, Any]],
    *,
    plan: EvaluationPlan,
    run_set: FinalRunSet,
    artifact_root: Path,
    result_set_sha256: str,
) -> dict[str, Any]:
    result_sources = {
        (
            row["method"],
            row["seed"],
            row["condition"],
            row["query_definition"],
        ): row
        for row in rows
    }
    result_index = {
        (
            result.method,
            result.seed,
            result.condition,
            result.query_definition,
        ): result
        for result in results
    }
    evaluation_rows: list[dict[str, Any]] = []
    for method in plan.methods:
        for seed in plan.seeds:
            for condition in plan.conditions:
                for query_definition in plan.query_definitions:
                    key = (method, seed, condition, query_definition)
                    result = result_index[key]
                    source = result_sources[key]
                    evaluation_rows.append(
                        {
                            "method": method,
                            "seed": seed,
                            "condition": condition,
                            "query_definition": query_definition,
                            "result_file": source["file"],
                            "result_sha256": source["sha256"],
                            **result.telemetry.model_dump(mode="json"),
                        }
                    )

    training_rows: list[dict[str, Any]] = []
    for method in plan.methods:
        for seed in plan.seeds:
            run = final_run_for(run_set, method, seed)
            manifest_path = artifact_root / run.run_manifest_relative_path
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                telemetry = RuntimeTelemetry.model_validate(manifest["telemetry"])
            except (OSError, json.JSONDecodeError, KeyError, ValidationError) as exc:
                raise ValueError(
                    f"locked run telemetry is invalid: {manifest_path}: {exc}"
                ) from exc
            if sha256_file(manifest_path) != run.run_manifest_sha256:
                raise ValueError("locked run telemetry source hash changed")
            training_rows.append(
                {
                    "method": method,
                    "seed": seed,
                    "run_manifest_file": str(manifest_path.resolve()),
                    "run_manifest_sha256": run.run_manifest_sha256,
                    **telemetry.model_dump(mode="json"),
                }
            )

    evaluation_by_method = {
        method: _telemetry_aggregate(
            [row for row in evaluation_rows if row["method"] == method]
        )
        for method in plan.methods
    }
    training_by_method = {
        method: _telemetry_aggregate(
            [row for row in training_rows if row["method"] == method]
        )
        for method in plan.methods
    }
    return {
        "schema_version": 1,
        "artifact": "core_runtime_and_peak_memory",
        "protocol_sha256": results[0].protocol_sha256,
        "evaluation_plan_sha256": results[0].evaluation_plan_sha256,
        "final_run_set_sha256": results[0].final_run_set_sha256,
        "result_set_sha256": result_set_sha256,
        "telemetry_contract": {
            "wall_time_seconds": "finite_float_greater_than_or_equal_to_zero",
            "peak_memory_bytes": "integer_greater_than_or_equal_to_zero",
            "peak_memory_source": [
                "torch_cuda_max_memory_allocated",
                "process_max_rss",
                "not_available",
            ],
        },
        "evaluation": {
            "rows": evaluation_rows,
            "all": _telemetry_aggregate(evaluation_rows),
            "by_method": evaluation_by_method,
        },
        "training": {
            "rows": training_rows,
            "all": _telemetry_aggregate(training_rows),
            "by_method": training_by_method,
        },
    }


def _metric_curve_svg(
    curve_payload: dict[str, Any],
    *,
    query_definition: str,
    metric: str,
    curves_sha256: str,
    result_set_sha256: str,
) -> str:
    """Render one exhaustive metric/query curve with all seed ranges."""
    metric_labels = {"top1": "Top-1", "mrr": "MRR", "r_at_5": "R@5"}
    query_labels = {"primary": "Primary", "official": "Exact official"}
    if metric not in metric_labels or query_definition not in query_labels:
        raise ValueError("curve request is outside the locked metrics or query sets")
    panels = [
        curve
        for curve in curve_payload["curves"]
        if curve["query_definition"] == query_definition and curve["metric"] == metric
    ]
    if [panel["corruption_family"] for panel in panels] != [
        "coordinate_jitter",
        "joint_mask",
        "frame_mask",
    ]:
        raise ValueError("curve payload omits a locked corruption family")
    methods = (
        ("contrastive", "Contrastive", "#0072b2"),
        ("supcon", "SupCon", "#d55e00"),
        ("contextual", "Contextual", "#009e73"),
    )
    family_labels = {
        "coordinate_jitter": "Coordinate jitter",
        "joint_mask": "Joint trajectories masked",
        "frame_mask": "Consecutive frames masked",
    }

    def severity_label(family: str, severity: str) -> str:
        if severity == "clean":
            return "Clean"
        if family == "coordinate_jitter":
            return f"{float(severity) * 100:g}%"
        return severity

    width = 1080
    height = 390
    panel_width = 300
    panel_lefts = (75, 405, 735)
    top = 105
    bottom = 315
    x_offsets = (0, 90, 180, 270)
    seeds = tuple(curve_payload["seeds"])
    seed_summary = ", ".join(str(seed) for seed in seeds)
    metric_label = metric_labels[metric]
    query_label = query_labels[query_definition]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="title description">',
        f'<title id="title">{query_label} query {metric_label} under pose '
        "corruption</title>",
        f'<desc id="description">Mean {metric_label} and full seed range for all '
        "three core methods and corruption levels.</desc>",
        f'<metadata id="source-binding">curves_sha256={curves_sha256};'
        f"result_set_sha256={result_set_sha256}</metadata>",
        '<rect width="1080" height="390" fill="#ffffff"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#17202a">',
        '<text x="540" y="30" text-anchor="middle" font-size="20" '
        f'font-weight="700">{query_label} query {metric_label} under pose '
        "corruption</text>",
        '<text x="540" y="52" text-anchor="middle" font-size="12">Mean '
        f"across paired seeds {seed_summary}; clean gallery throughout</text>",
    ]
    legend_x = 320
    for offset, (_, label, color) in enumerate(methods):
        x = legend_x + offset * 175
        parts.extend(
            [
                f'<line x1="{x}" y1="74" x2="{x + 28}" y2="74" '
                f'stroke="{color}" stroke-width="3"/>',
                f'<circle cx="{x + 14}" cy="74" r="3.5" fill="{color}"/>',
                f'<text x="{x + 36}" y="78" font-size="12">{label}</text>',
            ]
        )

    for panel_index, panel in enumerate(panels):
        family = panel["corruption_family"]
        left = panel_lefts[panel_index]
        right = left + panel_width - 30
        parts.append(
            f'<text x="{(left + right) / 2:.1f}" y="96" text-anchor="middle" '
            f'font-size="13" font-weight="700">{family_labels[family]}</text>'
        )
        for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - tick * (bottom - top)
            parts.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
                'stroke="#d9dee3" stroke-width="1"/>'
            )
            if panel_index == 0:
                parts.append(
                    f'<text x="{left - 9}" y="{y + 4:.1f}" text-anchor="end" '
                    f'font-size="10">{tick:.2f}</text>'
                )
        parts.extend(
            [
                f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
                'stroke="#65717c"/>',
                f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
                'stroke="#65717c"/>',
            ]
        )
        first_series = panel["series"][0]
        labels = [
            severity_label(family, point["severity"])
            for point in first_series["points"]
        ]
        for x_offset, label in zip(x_offsets, labels, strict=True):
            x = left + x_offset
            parts.append(
                f'<text x="{x}" y="333" text-anchor="middle" font-size="10">'
                f"{label}</text>"
            )
        series_by_method = {series["method"]: series for series in panel["series"]}
        for method, label, color in methods:
            series = series_by_method[method]
            means = [point["mean"] for point in series["points"]]
            points = " ".join(
                f"{left + x_offset},{bottom - value * (bottom - top):.2f}"
                for x_offset, value in zip(x_offsets, means, strict=True)
            )
            parts.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" '
                'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
            )
            for x_offset, point, value in zip(
                x_offsets, series["points"], means, strict=True
            ):
                x = left + x_offset
                y = bottom - value * (bottom - top)
                minimum_y = bottom - point["minimum"] * (bottom - top)
                maximum_y = bottom - point["maximum"] * (bottom - top)
                parts.append(
                    f'<line x1="{x}" y1="{maximum_y:.2f}" x2="{x}" '
                    f'y2="{minimum_y:.2f}" stroke="{color}" stroke-width="1"/>'
                )
                for seed_index, seed_value in enumerate(point["seed_values"]):
                    seed_x = x + (seed_index - 1) * 4
                    seed_y = bottom - seed_value["value"] * (bottom - top)
                    parts.append(
                        f'<circle cx="{seed_x}" cy="{seed_y:.2f}" r="2" '
                        f'fill="#ffffff" stroke="{color}" stroke-width="1"/>'
                    )
                values = ", ".join(
                    f"seed {item['seed']}={item['value']:.6f}"
                    for item in point["seed_values"]
                )
                parts.append(
                    f'<circle cx="{x}" cy="{y:.2f}" r="3.5" fill="{color}">'
                    f"<title>{label}, {point['condition']}: mean={value:.6f}; "
                    f"{values}</title></circle>"
                )
    parts.extend(
        [
            '<text x="19" y="210" transform="rotate(-90 19 210)" '
            f'text-anchor="middle" font-size="12">{metric_label}</text>',
            '<text x="540" y="368" text-anchor="middle" font-size="10" '
            'fill="#4d5963">Lines are three-seed means; whiskers span all three '
            "seed values. See core-metric-curves.json.</text>",
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def _core_report_artifacts(
    results: list[EvaluationResult],
    rows: list[dict[str, Any]],
    *,
    protocol_path: str | Path,
) -> dict[str, Any]:
    """Build every deterministic core artifact and its exact summary references."""
    protocol = load_protocol(protocol_path)
    scientific_paths = resolve_scientific_paths(protocol)
    plan = load_evaluation_plan(scientific_paths.evaluation_plan)
    run_set = load_final_run_set(scientific_paths.final_run_set)
    result_set_sha256 = _result_set_digest(rows)

    primary = _primary_analysis_payload(
        results,
        rows,
        protocol_path=protocol_path,
    )
    primary_sha256 = _payload_sha256(primary)
    curves = _complete_curve_payload(
        results,
        plan=plan,
        result_set_sha256=result_set_sha256,
        primary_analysis_sha256=primary_sha256,
    )
    curves_sha256 = _payload_sha256(curves)
    errors = _complete_error_payload(
        results,
        plan=plan,
        novel_actions=protocol.dataset.novel_actions,
        result_set_sha256=result_set_sha256,
    )
    errors_sha256 = _payload_sha256(errors)
    telemetry = _runtime_telemetry_payload(
        results,
        rows,
        plan=plan,
        run_set=run_set,
        artifact_root=scientific_paths.root,
        result_set_sha256=result_set_sha256,
    )
    telemetry_sha256 = _payload_sha256(telemetry)
    failures = derive_core_failure_status(protocol)
    if (
        failures.get("schema_version") != 1
        or failures.get("protocol_sha256") != results[0].protocol_sha256
        or failures.get("final_run_set_sha256") != results[0].final_run_set_sha256
        or not isinstance(failures.get("unresolved_failures"), list)
    ):
        raise ValueError("derived core failure status is inconsistent")
    failures_sha256 = _payload_sha256(failures)

    figure_contents: dict[str, str] = {}
    figures: list[dict[str, Any]] = []
    for query_definition in plan.query_definitions:
        for metric in plan.metrics:
            metric_slug = metric.replace("_", "-")
            filename = f"{query_definition}-{metric_slug}-corruption-curves.svg"
            content = _metric_curve_svg(
                curves,
                query_definition=query_definition,
                metric=metric,
                curves_sha256=curves_sha256,
                result_set_sha256=result_set_sha256,
            )
            figure_sha256 = hashlib.sha256(content.encode()).hexdigest()
            figure_contents[filename] = content
            figures.append(
                {
                    "id": f"{query_definition}_{metric}_corruption_curves",
                    "file": filename,
                    "sha256": figure_sha256,
                    "source_curves_sha256": curves_sha256,
                    "result_set_sha256": result_set_sha256,
                    "query_definition": query_definition,
                    "metric": metric,
                    "aggregation": "mean_and_range_across_three_paired_seeds",
                }
            )

    references = {
        "primary_analysis": {
            "file": "primary-analysis.json",
            "sha256": primary_sha256,
            "estimate": primary["estimate"],
            "confidence_interval": primary["bootstrap"],
            "claim_supported": primary["claim_supported"],
        },
        "curve_data": {
            "file": "core-metric-curves.json",
            "sha256": curves_sha256,
            "curve_count": len(curves["curves"]),
        },
        "error_analysis": {
            "file": "core-error-analysis.json",
            "sha256": errors_sha256,
            "per_class_row_count": len(errors["per_class"]),
            "representative_cell_count": len(errors["representative_errors"]),
        },
        "telemetry": {
            "file": "core-telemetry.json",
            "sha256": telemetry_sha256,
            "evaluation_operation_count": len(telemetry["evaluation"]["rows"]),
            "training_operation_count": len(telemetry["training"]["rows"]),
        },
        "failures": {
            "file": "core-failures.json",
            "sha256": failures_sha256,
            "attempt_count": failures["attempt_count"],
            "failed_attempt_count": failures["failed_attempt_count"],
            "unresolved_failure_count": len(failures["unresolved_failures"]),
        },
        "figures": figures,
    }
    return {
        "json": {
            "primary-analysis.json": primary,
            "core-metric-curves.json": curves,
            "core-error-analysis.json": errors,
            "core-telemetry.json": telemetry,
            "core-failures.json": failures,
        },
        "text": figure_contents,
        "references": references,
    }


def _write_immutable_text(path: Path, content: str) -> None:
    try:
        with path.open("x", encoding="utf-8", errors="strict") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite report: {path}") from exc


def _rehash_provenance_inputs(
    result: EvaluationResult,
    cache: dict[Path, str],
) -> dict[str, list[Path]]:
    """Rehash every evaluator-recorded input and index paths by digest."""
    paths_by_hash: dict[str, list[Path]] = {}
    for raw_path, expected_sha256 in result.provenance.inputs.items():
        path = Path(raw_path)
        actual_sha256 = cache.get(path)
        if actual_sha256 is None:
            try:
                actual_sha256 = sha256_file(path)
            except (OSError, ValueError) as exc:
                raise ValueError(
                    f"result provenance input is unavailable: {path}"
                ) from exc
            cache[path] = actual_sha256
        if actual_sha256 != expected_sha256:
            raise ValueError(f"result provenance input hash mismatch: {path}")
        paths_by_hash.setdefault(expected_sha256, []).append(path)
    return paths_by_hash


def _feature_path_for_hash(
    paths_by_hash: dict[str, list[Path]],
    digest: str,
    *,
    label: str,
) -> Path:
    candidates = [
        path for path in paths_by_hash.get(digest, []) if path.suffix == ".npz"
    ]
    if len(candidates) != 1:
        raise ValueError(f"final provenance does not identify one {label} feature file")
    return candidates[0]


def _validate_retrieval_metrics(
    result: EvaluationResult,
    gallery_path: Path,
    query_path: Path,
) -> None:
    """Recompute one result cell from its immutable feature artifacts."""

    def load(path: Path) -> tuple[torch.Tensor, torch.Tensor, tuple[str, ...]]:
        with np.load(path, allow_pickle=False) as archive:
            key = "embeddings" if "embeddings" in archive.files else "features"
            embeddings = torch.as_tensor(np.asarray(archive[key]), dtype=torch.float32)
            labels = torch.as_tensor(np.asarray(archive["labels"]), dtype=torch.long)
            sample_ids = tuple(np.asarray(archive["sample_ids"]).astype(str))
        return embeddings, labels, sample_ids

    gallery_embeddings, gallery_labels, _ = load(gallery_path)
    query_embeddings, query_labels, query_ids = load(query_path)
    recomputed = ResultMetrics.model_validate(
        evaluate_one_shot(
            gallery_embeddings,
            gallery_labels,
            query_embeddings,
            query_labels,
            query_ids=query_ids,
        ).as_dict()
    )
    if result.metrics != recomputed:
        raise ValueError("result metrics differ from deterministic feature retrieval")


def _validate_final_provenance(
    results: list[EvaluationResult],
    *,
    protocol_path: str | Path,
) -> tuple[int, set[tuple[str, int, str, str]]]:
    protocol = load_protocol(protocol_path)
    paths = resolve_scientific_paths(protocol)
    _, protocol_sha256 = verify_protocol(
        protocol_path,
        lock_path=paths.protocol_lock,
        evaluation_plan_path=paths.evaluation_plan,
        final_run_set_path=paths.final_run_set,
        require_locked=True,
    )
    plan = load_evaluation_plan(paths.evaluation_plan)
    run_set = load_final_run_set(paths.final_run_set)
    manifest_validation = validate_evaluation_manifests(
        protocol,
        plan,
        paths.root,
        check_source_files=False,
    )
    ledger = TestOpeningLedger.model_validate_json(
        paths.test_opening_ledger.read_text(encoding="utf-8")
    )
    plan_sha256 = evaluation_plan_digest(plan)
    run_set_sha256 = final_run_set_digest(run_set)
    lock_sha256 = sha256_file(paths.protocol_lock)
    ledger_sha256 = sha256_file(paths.test_opening_ledger)
    common = {
        "protocol_sha256": protocol_sha256,
        "evaluation_plan_sha256": plan_sha256,
        "final_run_set_sha256": run_set_sha256,
        "protocol_lock_sha256": lock_sha256,
        "test_opening_ledger_sha256": ledger_sha256,
    }
    assert plan.source_inventory_manifest is not None
    if (
        ledger.protocol_sha256,
        ledger.protocol_lock_sha256,
        ledger.evaluation_plan_sha256,
        ledger.final_run_set_sha256,
        ledger.source_inventory_manifest_sha256,
        ledger.source_file_count,
        ledger.source_files_sha256,
    ) != (
        protocol_sha256,
        lock_sha256,
        plan_sha256,
        run_set_sha256,
        plan.source_inventory_manifest.sha256,
        manifest_validation.source_file_count,
        manifest_validation.source_files_sha256,
    ):
        raise ValueError("test-opening ledger provenance differs from final locks")
    if ledger.opened_at < run_set.locked_at:
        raise ValueError("test-opening ledger predates the completed core run set")

    run_files = {
        (run.method, run.seed): validate_final_run_artifacts(
            run_set,
            run,
            paths.root,
            protocol=protocol,
        )
        for run in run_set.runs
    }
    bindings = {
        "source_inventory_manifest_sha256": plan.source_inventory_manifest,
        "anchor_manifest_sha256": plan.anchor_manifest,
        "official_query_manifest_sha256": plan.official_query_manifest,
        "primary_query_manifest_sha256": plan.primary_query_manifest,
    }
    assert all(binding is not None for binding in bindings.values())
    expected_keys = {
        (method, seed, condition, query_definition)
        for method in plan.methods
        for seed in plan.seeds
        for condition in plan.conditions
        for query_definition in plan.query_definitions
    }
    current_lock_sha256 = sha256_file(Path(__file__).resolve().parents[2] / "uv.lock")
    input_hash_cache: dict[Path, str] = {}
    encoder_lineages: set[tuple[str, str, str]] = set()
    gallery_base_lineages: set[tuple[str | None, str | None]] = set()
    query_base_lineages: dict[tuple[str, str], set[tuple[str | None, str | None]]] = {}
    for result in results:
        for field, expected in common.items():
            if getattr(result, field) != expected:
                raise ValueError(f"final result has mismatched {field}")
        for field, optional_binding in bindings.items():
            assert optional_binding is not None
            if getattr(result, field) != optional_binding.sha256:
                raise ValueError(f"final result has mismatched {field}")
        run = final_run_for(run_set, result.method, result.seed)
        if (
            result.run_manifest_sha256 != run.run_manifest_sha256
            or result.checkpoint_sha256 != run.checkpoint_sha256
        ):
            raise ValueError("final result differs from its locked run/checkpoint")
        if result.provenance.dependency_lock_sha256 != current_lock_sha256:
            raise ValueError(
                "final result dependency lock differs from the current lock"
            )
        if result.provenance.started_at < ledger.opened_at:
            raise ValueError("final result provenance predates the test opening")

        paths_by_hash = _rehash_provenance_inputs(result, input_hash_cache)
        for locked_path in (
            paths.protocol_lock,
            paths.test_opening_ledger,
            *manifest_validation.paths.values(),
            *run_files[(run.method, run.seed)].values(),
        ):
            expected_hash = input_hash_cache.get(locked_path)
            if expected_hash is None:
                expected_hash = sha256_file(locked_path)
                input_hash_cache[locked_path] = expected_hash
            if locked_path not in paths_by_hash.get(expected_hash, []):
                raise ValueError(
                    f"final result provenance omits locked input: {locked_path}"
                )

        gallery_path = _feature_path_for_hash(
            paths_by_hash,
            result.gallery_artifact_sha256,
            label="gallery",
        )
        query_path = _feature_path_for_hash(
            paths_by_hash,
            result.query_artifact_sha256,
            label="query",
        )
        if sidecar_path_for(gallery_path) not in paths_by_hash.get(
            result.gallery_sidecar_sha256, []
        ) or sidecar_path_for(query_path) not in paths_by_hash.get(
            result.query_sidecar_sha256, []
        ):
            raise ValueError("final result provenance omits a feature sidecar")
        assert plan.anchor_manifest is not None
        query_binding = (
            plan.primary_query_manifest
            if result.query_definition == "primary"
            else plan.official_query_manifest
        )
        assert query_binding is not None
        gallery_sidecar = validate_feature_artifact(
            gallery_path,
            protocol=protocol,
            manifest_path=manifest_validation.paths["anchor"],
        )
        query_sidecar = validate_feature_artifact(
            query_path,
            protocol=protocol,
            manifest_path=(
                manifest_validation.paths["primary"]
                if result.query_definition == "primary"
                else manifest_validation.paths["official"]
            ),
        )
        expected_query_role = (
            "query_clean" if result.condition == "clean" else "query_corrupted"
        )
        if (
            gallery_sidecar.backend != "motionbert"
            or query_sidecar.backend != "motionbert"
            or gallery_sidecar.method != result.method
            or query_sidecar.method != result.method
            or gallery_sidecar.training_seed != result.seed
            or query_sidecar.training_seed != result.seed
            or gallery_sidecar.role != "gallery_clean"
            or gallery_sidecar.condition != "clean"
            or query_sidecar.role != expected_query_role
            or query_sidecar.condition != result.condition
            or gallery_sidecar.head_checkpoint_sha256 != run.checkpoint_sha256
            or query_sidecar.head_checkpoint_sha256 != run.checkpoint_sha256
        ):
            raise ValueError(
                "final feature sidecars differ from the result matrix cell"
            )
        if (
            result.metrics.gallery_count != plan.anchor_manifest.sample_count
            or result.gallery_sample_order_sha256
            != sample_order_digest(plan.anchor_manifest.sample_ids)
        ):
            raise ValueError("final result gallery differs from the locked anchor set")
        if (
            result.metrics.query_count != query_binding.sample_count
            or result.query_sample_order_sha256
            != sample_order_digest(query_binding.sample_ids)
            or tuple(row.sample_id for row in result.metrics.per_query)
            != query_binding.sample_ids
        ):
            raise ValueError("final result queries differ from the locked query set")
        encoder_lineages.add(
            (
                gallery_sidecar.encoder_checkpoint_sha256,
                gallery_sidecar.upstream_sha256,
                gallery_sidecar.preprocessing_sha256,
            )
        )
        encoder_lineages.add(
            (
                query_sidecar.encoder_checkpoint_sha256,
                query_sidecar.upstream_sha256,
                query_sidecar.preprocessing_sha256,
            )
        )
        if len(encoder_lineages) != 1:
            raise ValueError("final matrix changes frozen-encoder lineage")
        gallery_base_lineages.add(
            (
                gallery_sidecar.base_artifact_sha256,
                gallery_sidecar.base_sidecar_sha256,
            )
        )
        if len(gallery_base_lineages) != 1:
            raise ValueError("final matrix changes the clean-gallery base cache")
        query_lineages = query_base_lineages.setdefault(
            (result.condition, result.query_definition), set()
        )
        query_lineages.add(
            (
                query_sidecar.base_artifact_sha256,
                query_sidecar.base_sidecar_sha256,
            )
        )
        if len(query_lineages) != 1:
            raise ValueError("final matrix changes a paired query corruption cache")
        _validate_retrieval_metrics(result, gallery_path, query_path)
        key = (
            result.method,
            result.seed,
            result.condition,
            result.query_definition,
        )
        if key not in expected_keys:
            raise ValueError(f"unexpected final result matrix cell: {key}")
    return plan.expected_rows, expected_keys


def _validate_exploratory_provenance(
    results: list[EvaluationResult],
    *,
    protocol_path: str | Path,
) -> tuple[int, set[tuple[str, int, str, str]]]:
    """Certify a separate 60-row stretch matrix without changing core status."""
    protocol = load_protocol(protocol_path)
    paths = resolve_scientific_paths(protocol)
    _, protocol_sha256 = verify_protocol(
        protocol_path,
        lock_path=paths.protocol_lock,
        evaluation_plan_path=paths.evaluation_plan,
        final_run_set_path=paths.final_run_set,
        require_locked=True,
    )
    plan = load_evaluation_plan(paths.evaluation_plan)
    run_set = load_final_run_set(paths.final_run_set)
    manifest_validation = validate_evaluation_manifests(
        protocol,
        plan,
        paths.root,
        check_source_files=False,
    )
    validate_post_core_stretch_authorization(
        protocol,
        paths.stretch_gate_evidence,
    )
    ledger = TestOpeningLedger.model_validate_json(
        paths.test_opening_ledger.read_text(encoding="utf-8")
    )
    common = {
        "protocol_sha256": protocol_sha256,
        "evaluation_plan_sha256": evaluation_plan_digest(plan),
        "final_run_set_sha256": final_run_set_digest(run_set),
        "protocol_lock_sha256": sha256_file(paths.protocol_lock),
        "test_opening_ledger_sha256": sha256_file(paths.test_opening_ledger),
        "stretch_gate_evidence_sha256": sha256_file(paths.stretch_gate_evidence),
    }
    expected_keys = {
        ("multi_similarity_with_miner", seed, condition, query_definition)
        for seed in plan.seeds
        for condition in plan.conditions
        for query_definition in plan.query_definitions
    }
    assert plan.source_inventory_manifest is not None
    assert plan.anchor_manifest is not None
    assert plan.official_query_manifest is not None
    assert plan.primary_query_manifest is not None
    bindings = {
        "source_inventory_manifest_sha256": plan.source_inventory_manifest,
        "anchor_manifest_sha256": plan.anchor_manifest,
        "official_query_manifest_sha256": plan.official_query_manifest,
        "primary_query_manifest_sha256": plan.primary_query_manifest,
    }
    current_lock_sha256 = sha256_file(Path(__file__).resolve().parents[2] / "uv.lock")
    input_hash_cache: dict[Path, str] = {}
    validated_runs: dict[int, tuple[str, str, dict[str, Path]]] = {}
    encoder_lineages: set[tuple[str, str, str]] = set()
    gallery_base_lineages: set[tuple[str | None, str | None]] = set()
    query_base_lineages: dict[tuple[str, str], set[tuple[str | None, str | None]]] = {}
    for result in results:
        for field, expected in common.items():
            if getattr(result, field) != expected:
                raise ValueError(f"exploratory result has mismatched {field}")
        for field, binding in bindings.items():
            if getattr(result, field) != binding.sha256:
                raise ValueError(f"exploratory result has mismatched {field}")
        if result.provenance.dependency_lock_sha256 != current_lock_sha256:
            raise ValueError(
                "exploratory result dependency lock differs from the current lock"
            )
        if result.provenance.started_at < ledger.opened_at:
            raise ValueError("exploratory result predates the core test opening")
        paths_by_hash = _rehash_provenance_inputs(result, input_hash_cache)
        assert result.run_manifest_sha256 is not None
        manifest_candidates = [
            path
            for path in paths_by_hash.get(result.run_manifest_sha256, [])
            if path.name == "run-manifest.json"
        ]
        if len(manifest_candidates) != 1:
            raise ValueError(
                "exploratory provenance does not identify one run manifest"
            )
        run_identity = (result.run_manifest_sha256, result.checkpoint_sha256)
        prior = validated_runs.get(result.seed)
        if prior is None:
            run_files = validate_exploratory_run_artifacts(
                protocol,
                manifest_candidates[0],
                seed=result.seed,
                checkpoint_sha256=result.checkpoint_sha256,
                evidence_path=paths.stretch_gate_evidence,
            )
            validated_runs[result.seed] = (*run_identity, run_files)
        elif prior[:2] != run_identity:
            raise ValueError("exploratory matrix changes run within a paired seed")
        run_files = validated_runs[result.seed][2]
        for locked_path in (
            paths.protocol_lock,
            paths.test_opening_ledger,
            *manifest_validation.paths.values(),
            *run_files.values(),
        ):
            expected_hash = input_hash_cache.get(locked_path)
            if expected_hash is None:
                expected_hash = sha256_file(locked_path)
                input_hash_cache[locked_path] = expected_hash
            if locked_path not in paths_by_hash.get(expected_hash, []):
                raise ValueError(
                    f"exploratory provenance omits locked input: {locked_path}"
                )

        gallery_path = _feature_path_for_hash(
            paths_by_hash,
            result.gallery_artifact_sha256,
            label="gallery",
        )
        query_path = _feature_path_for_hash(
            paths_by_hash,
            result.query_artifact_sha256,
            label="query",
        )
        gallery_sidecar = validate_feature_artifact(
            gallery_path,
            protocol=protocol,
            manifest_path=manifest_validation.paths["anchor"],
        )
        query_binding = (
            plan.primary_query_manifest
            if result.query_definition == "primary"
            else plan.official_query_manifest
        )
        query_sidecar = validate_feature_artifact(
            query_path,
            protocol=protocol,
            manifest_path=(
                manifest_validation.paths["primary"]
                if result.query_definition == "primary"
                else manifest_validation.paths["official"]
            ),
        )
        expected_query_role = (
            "query_clean" if result.condition == "clean" else "query_corrupted"
        )
        if (
            gallery_sidecar.backend != "motionbert"
            or query_sidecar.backend != "motionbert"
            or gallery_sidecar.method != "multi_similarity_with_miner"
            or query_sidecar.method != "multi_similarity_with_miner"
            or gallery_sidecar.training_seed != result.seed
            or query_sidecar.training_seed != result.seed
            or gallery_sidecar.head_checkpoint_sha256 != result.checkpoint_sha256
            or query_sidecar.head_checkpoint_sha256 != result.checkpoint_sha256
            or query_sidecar.role != expected_query_role
            or query_sidecar.condition != result.condition
        ):
            raise ValueError("exploratory sidecars differ from the matrix cell")
        if (
            result.metrics.gallery_count != plan.anchor_manifest.sample_count
            or result.gallery_sample_order_sha256
            != sample_order_digest(plan.anchor_manifest.sample_ids)
        ):
            raise ValueError("exploratory gallery differs from locked anchors")
        if (
            result.metrics.query_count != query_binding.sample_count
            or result.query_sample_order_sha256
            != sample_order_digest(query_binding.sample_ids)
            or tuple(row.sample_id for row in result.metrics.per_query)
            != query_binding.sample_ids
        ):
            raise ValueError("exploratory queries differ from the locked query set")
        encoder_lineages.add(
            (
                gallery_sidecar.encoder_checkpoint_sha256,
                gallery_sidecar.upstream_sha256,
                gallery_sidecar.preprocessing_sha256,
            )
        )
        encoder_lineages.add(
            (
                query_sidecar.encoder_checkpoint_sha256,
                query_sidecar.upstream_sha256,
                query_sidecar.preprocessing_sha256,
            )
        )
        if len(encoder_lineages) != 1:
            raise ValueError("exploratory matrix changes frozen-encoder lineage")
        gallery_base_lineages.add(
            (
                gallery_sidecar.base_artifact_sha256,
                gallery_sidecar.base_sidecar_sha256,
            )
        )
        if len(gallery_base_lineages) != 1:
            raise ValueError("exploratory matrix changes the clean-gallery base cache")
        query_lineages = query_base_lineages.setdefault(
            (result.condition, result.query_definition), set()
        )
        query_lineages.add(
            (
                query_sidecar.base_artifact_sha256,
                query_sidecar.base_sidecar_sha256,
            )
        )
        if len(query_lineages) != 1:
            raise ValueError(
                "exploratory matrix changes a paired query corruption cache"
            )
        _validate_retrieval_metrics(result, gallery_path, query_path)
        key = (
            result.method,
            result.seed,
            result.condition,
            result.query_definition,
        )
        if key not in expected_keys:
            raise ValueError(f"unexpected exploratory result matrix cell: {key}")
    return len(expected_keys), expected_keys


def build_report(
    result_paths: Iterable[str | Path],
    output_dir: str | Path,
    *,
    protocol_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build validated result tables and analyze only an exact final matrix."""
    paths = sorted((Path(path).resolve() for path in result_paths), key=str)
    if not paths:
        raise ValueError("at least one result file is required")
    results = [_load_result(path) for path in paths]
    modes = {result.mode for result in results}
    if len(modes) != 1:
        raise ValueError("report inputs cannot mix development and final results")
    matrix_keys: set[tuple[str, int, str, str]] = set()
    rows: list[dict[str, Any]] = []
    for path, result in zip(paths, results, strict=True):
        matrix_key = (
            result.method,
            result.seed,
            result.condition,
            result.query_definition,
        )
        if matrix_key in matrix_keys:
            raise ValueError(f"duplicate result matrix cell: {matrix_key}")
        matrix_keys.add(matrix_key)
        rows.append(_result_row(path, result))
    if len({result.protocol_sha256 for result in results}) != 1:
        raise ValueError("report inputs mix results from different protocol hashes")
    if len({result.gallery_sample_order_sha256 for result in results}) != 1:
        raise ValueError("result matrix changes the clean gallery sample order")
    for query_definition in {result.query_definition for result in results}:
        definition_rows = [
            result for result in results if result.query_definition == query_definition
        ]
        if len({result.query_sample_order_sha256 for result in definition_rows}) != 1:
            raise ValueError(
                f"result matrix changes {query_definition} query sample order"
            )
        if len({result.metrics.query_count for result in definition_rows}) != 1:
            raise ValueError(f"result matrix changes {query_definition} query count")

    expected_rows: int | None = None
    complete = False
    primary_analysis: dict[str, Any] | None = None
    core_artifacts: dict[str, Any] | None = None
    if modes in ({"final"}, {"exploratory"}):
        if protocol_path is None:
            raise ValueError("locked report requires the protocol configuration")
        validator = (
            _validate_final_provenance
            if modes == {"final"}
            else _validate_exploratory_provenance
        )
        expected_rows, authorized_keys = validator(results, protocol_path=protocol_path)
        complete = matrix_keys == authorized_keys and len(matrix_keys) == expected_rows
        if modes == {"final"} and complete:
            core_artifacts = _core_report_artifacts(
                results,
                rows,
                protocol_path=protocol_path,
            )
            primary_analysis = core_artifacts["json"]["primary-analysis.json"]

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "summary.md"
    summary_path = destination / "summary.json"
    output_paths = [summary_path, report_path]
    if core_artifacts is not None:
        output_paths.extend(
            destination / filename
            for filename in (
                *core_artifacts["json"],
                *core_artifacts["text"],
            )
        )
    for output_path in output_paths:
        if output_path.exists():
            raise ValueError(f"refusing to overwrite report: {output_path}")
    references = core_artifacts["references"] if core_artifacts is not None else {}
    if core_artifacts is not None:
        for filename, payload in core_artifacts["json"].items():
            artifact_path = destination / filename
            write_immutable_json(artifact_path, payload)
            if sha256_file(artifact_path) != _payload_sha256(payload):
                raise ValueError(f"written report artifact hash changed: {filename}")
        for filename, content in core_artifacts["text"].items():
            artifact_path = destination / filename
            _write_immutable_text(artifact_path, content)
            expected_sha256 = hashlib.sha256(content.encode()).hexdigest()
            if sha256_file(artifact_path) != expected_sha256:
                raise ValueError(f"written report figure hash changed: {filename}")
    summary = {
        "schema_version": 5,
        "analysis_scope": (
            "core_confirmatory"
            if modes == {"final"}
            else "exploratory_stretch"
            if modes == {"exploratory"}
            else "development"
        ),
        "protocol_sha256": results[0].protocol_sha256,
        "matrix": {
            "observed_rows": len(matrix_keys),
            "expected_rows": expected_rows,
            "complete": complete,
        },
        "primary_analysis": references.get("primary_analysis"),
        "curve_data": references.get("curve_data"),
        "error_analysis": references.get("error_analysis"),
        "telemetry": references.get("telemetry"),
        "failures": references.get("failures"),
        "figures": references.get("figures", []),
        "results": rows,
    }
    write_immutable_json(summary_path, summary)
    markdown = [
        "# Pose Embed validated result report",
        "",
        "This report includes every supplied immutable result. It does not select",
        "methods, seeds, conditions, metrics, query definitions, classes, or errors.",
        "",
    ]
    if primary_analysis is not None:
        bootstrap = primary_analysis["bootstrap"]
        support = (
            "supported" if primary_analysis["claim_supported"] else "not supported"
        )
        markdown.extend(
            [
                "## Preregistered primary analysis",
                "",
                "The estimate is the equal-weight mean of contextual degradation",
                "minus contrastive degradation over three paired seeds and nine",
                "corruption cells, using the primary query definition.",
                "",
                f"- Effect: {primary_analysis['estimate']:.6f}",
                f"- {bootstrap['confidence_level']:.0%} paired cluster-bootstrap "
                f"interval: [{bootstrap['lower']:.6f}, {bootstrap['upper']:.6f}]",
                f"- Bootstrap replicates / seed: {bootstrap['replicates']} / "
                f"{bootstrap['seed']}",
                f"- Preregistered robustness claim: {support}",
                "",
                "A negative effect means contextual training degraded less. This does",
                "not imply higher overall retrieval when clean accuracy differs.",
                "",
                "| Seed | Condition | Contextual clean | Contextual corrupted | "
                "Contextual drop | Contrastive clean | Contrastive corrupted | "
                "Contrastive drop | Effect |",
                "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for cell in primary_analysis["cells"]:
            markdown.append(
                f"| {cell['seed']} | {cell['condition']} | "
                f"{cell['contextual_clean_top1']:.4f} | "
                f"{cell['contextual_corrupted_top1']:.4f} | "
                f"{cell['contextual_drop']:.4f} | "
                f"{cell['contrastive_clean_top1']:.4f} | "
                f"{cell['contrastive_corrupted_top1']:.4f} | "
                f"{cell['contrastive_drop']:.4f} | {cell['effect']:.4f} |"
            )
        markdown.extend(
            [
                "",
                "## Complete core outputs",
                "",
                "The source-bound curve data includes Top-1, MRR, and R@5 for",
                "both query definitions, all three methods, every seed, and every",
                "corruption level. SVG lines show means and whiskers show the full",
                "three-seed range.",
                "",
            ]
        )
        assert core_artifacts is not None
        for figure in core_artifacts["references"]["figures"]:
            markdown.extend(
                [
                    f"![{figure['query_definition']} {figure['metric']} corruption "
                    f"curves]({figure['file']})",
                    "",
                ]
            )
        telemetry_payload = core_artifacts["json"]["core-telemetry.json"]
        failure_payload = core_artifacts["json"]["core-failures.json"]
        error_payload = core_artifacts["json"]["core-error-analysis.json"]
        training_seconds = telemetry_payload["training"]["all"][
            "total_wall_time_seconds"
        ]
        evaluation_seconds = telemetry_payload["evaluation"]["all"][
            "total_wall_time_seconds"
        ]
        markdown.extend(
            [
                "### Error, compute, and failure evidence",
                "",
                f"- Per-class rows: {len(error_payload['per_class'])}",
                "- Representative error rule: lexicographically first Top-1 error",
                "  in every matrix cell; cells without errors remain present as null",
                f"- Training wall time: {training_seconds:.3f} seconds",
                f"- Evaluation wall time: {evaluation_seconds:.3f} seconds",
                f"- Recorded / failed / unresolved attempts: "
                f"{failure_payload['attempt_count']} / "
                f"{failure_payload['failed_attempt_count']} / "
                f"{len(failure_payload['unresolved_failures'])}",
                "",
                "Exact per-operation peak-memory sources and values are in",
                "`core-telemetry.json`; per-class errors and deterministic examples",
                "are in `core-error-analysis.json`.",
                "",
            ]
        )
    elif modes == {"final"}:
        markdown.extend(
            [
                "The preregistered primary analysis was not computed because the",
                "authorized 180-row core matrix is incomplete.",
                "",
            ]
        )
    else:
        markdown.extend(
            [
                "No confirmatory robustness inference is computed for development or",
                "exploratory result sets.",
                "",
            ]
        )
    markdown.extend(
        [
            "## Result matrix",
            "",
            "| Method | Seed | Condition | Queries | Mode | Top-1 | MRR | R@5 | N |",
            "|---|---:|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        markdown.append(
            f"| {row['method']} | {row['seed']} | {row['condition']} | "
            f"{row['query_definition']} | {row['mode']} | {row['top1']:.4f} | "
            f"{row['mrr']:.4f} | {row['r_at_5']:.4f} | {row['queries']} |"
        )
    try:
        with report_path.open("x", encoding="utf-8", errors="strict") as stream:
            stream.write("\n".join(markdown) + "\n")
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite report: {report_path}") from exc
    return summary


def validate_core_report_summary(
    summary_path: str | Path,
    protocol_path: str | Path,
) -> dict[str, Any]:
    """Recertify every immutable core analysis artifact without writing."""
    path = Path(summary_path)
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid core report summary: {path}: {exc}") from exc
    expected_fields = {
        "schema_version",
        "analysis_scope",
        "protocol_sha256",
        "matrix",
        "primary_analysis",
        "curve_data",
        "error_analysis",
        "telemetry",
        "failures",
        "figures",
        "results",
    }
    if not isinstance(summary, dict) or set(summary) != expected_fields:
        raise ValueError("core report summary fields differ from schema v5")
    if summary["schema_version"] != 5 or summary["analysis_scope"] != (
        "core_confirmatory"
    ):
        raise ValueError("core report summary is not confirmatory schema v5")

    protocol = load_protocol(protocol_path)
    scientific_paths = resolve_scientific_paths(protocol)
    _, protocol_sha256 = verify_protocol(
        protocol_path,
        lock_path=scientific_paths.protocol_lock,
        evaluation_plan_path=scientific_paths.evaluation_plan,
        final_run_set_path=scientific_paths.final_run_set,
        require_locked=True,
    )
    plan = load_evaluation_plan(scientific_paths.evaluation_plan)
    expected_matrix = {
        "observed_rows": plan.expected_rows,
        "expected_rows": plan.expected_rows,
        "complete": True,
    }
    if summary["protocol_sha256"] != protocol_sha256:
        raise ValueError("core report protocol hash differs from the active lock")
    if summary["matrix"] != expected_matrix:
        raise ValueError("core report does not certify the exact complete matrix")

    rows = summary["results"]
    if not isinstance(rows, list) or len(rows) != plan.expected_rows:
        raise ValueError("core report result index is incomplete")
    result_paths: list[Path] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("file"), str):
            raise ValueError("core report contains an invalid result row")
        result_path = Path(row["file"])
        if not result_path.is_absolute():
            raise ValueError("core report result paths must be absolute")
        if sha256_file(result_path) != row.get("sha256"):
            raise ValueError(f"core report result hash mismatch: {result_path}")
        result_paths.append(result_path)
    if result_paths != sorted(result_paths, key=str) or len(set(result_paths)) != len(
        result_paths
    ):
        raise ValueError("core report result paths must be unique and sorted")

    results = [_load_result(result_path) for result_path in result_paths]
    validated_rows, validated_keys = _validate_final_provenance(
        results,
        protocol_path=protocol_path,
    )
    if validated_rows != plan.expected_rows:
        raise ValueError("core report failed full final provenance validation")
    recomputed_rows = [
        _result_row(result_path, result)
        for result_path, result in zip(result_paths, results, strict=True)
    ]
    if rows != recomputed_rows:
        raise ValueError("core report result rows differ from their immutable files")
    expected_keys = {
        (method, seed, condition, query_definition)
        for method in plan.methods
        for seed in plan.seeds
        for condition in plan.conditions
        for query_definition in plan.query_definitions
    }
    observed_keys = {
        (result.method, result.seed, result.condition, result.query_definition)
        for result in results
    }
    if observed_keys != expected_keys or len(observed_keys) != len(results):
        raise ValueError("core report result files do not form the exact final matrix")
    if validated_keys != expected_keys:
        raise ValueError("core report results failed full final provenance validation")

    expected_artifacts = _core_report_artifacts(
        results,
        recomputed_rows,
        protocol_path=protocol_path,
    )
    expected_references = expected_artifacts["references"]
    for field in (
        "primary_analysis",
        "curve_data",
        "error_analysis",
        "telemetry",
        "failures",
    ):
        if summary[field] != expected_references[field]:
            raise ValueError(f"core report {field} reference is invalid")
    if summary["figures"] != expected_references["figures"]:
        raise ValueError("core report figure references are invalid")

    for filename, expected_payload in expected_artifacts["json"].items():
        artifact_path = path.parent / filename
        try:
            observed_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid core report artifact {filename}: {exc}") from exc
        if observed_payload != expected_payload or sha256_file(
            artifact_path
        ) != _payload_sha256(expected_payload):
            raise ValueError(
                f"core report artifact differs from recomputed data: {filename}"
            )
    for filename, expected_content in expected_artifacts["text"].items():
        figure_path = path.parent / filename
        try:
            observed_content = figure_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"core report figure is unavailable: {filename}") from exc
        expected_sha256 = hashlib.sha256(expected_content.encode()).hexdigest()
        if (
            observed_content != expected_content
            or sha256_file(figure_path) != expected_sha256
        ):
            raise ValueError(
                f"core report figure differs from recomputed data: {filename}"
            )
    primary = expected_artifacts["json"]["primary-analysis.json"]
    failures = expected_artifacts["json"]["core-failures.json"]
    figure_hashes = {
        figure["id"]: figure["sha256"] for figure in expected_references["figures"]
    }
    return {
        **expected_matrix,
        "summary_sha256": sha256_file(path),
        "primary_analysis_sha256": expected_references["primary_analysis"]["sha256"],
        "curve_data_sha256": expected_references["curve_data"]["sha256"],
        "error_analysis_sha256": expected_references["error_analysis"]["sha256"],
        "telemetry_sha256": expected_references["telemetry"]["sha256"],
        "failures_sha256": expected_references["failures"]["sha256"],
        "figure_sha256": figure_hashes,
        "primary_figure_sha256": figure_hashes["primary_top1_corruption_curves"],
        "claim_supported": primary["claim_supported"],
        "unresolved_failures": failures["unresolved_failures"],
        "unresolved_failure_count": len(failures["unresolved_failures"]),
    }
