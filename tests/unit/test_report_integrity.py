from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import pose_embed.report as report_module
from pose_embed.artifacts import sample_order_digest
from pose_embed.config import load_protocol
from pose_embed.evaluation.result import EvaluationResult
from pose_embed.protocol import (
    evaluation_plan_digest,
    final_run_for,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    protocol_digest,
)
from pose_embed.provenance import RuntimeTelemetry, sha256_file
from pose_embed.report import (
    _metric_curve_svg,
    _validate_retrieval_metrics,
    build_report,
    validate_core_report_summary,
)
from tests.scientific_fixtures import write_lock_bundle


def _write_result(path: Path, *, seed: int = 7, include_metadata: bool = True) -> None:
    payload = {
        "schema_version": 4,
        "mode": "development",
        "protocol_sha256": "a" * 64,
        "evaluation_plan_sha256": None,
        "final_run_set_sha256": None,
        "protocol_lock_sha256": None,
        "test_opening_ledger_sha256": None,
        "run_manifest_sha256": None,
        "checkpoint_sha256": "d" * 64,
        "gallery_sidecar_sha256": "e" * 64,
        "query_sidecar_sha256": "f" * 64,
        "source_inventory_manifest_sha256": None,
        "anchor_manifest_sha256": None,
        "official_query_manifest_sha256": None,
        "primary_query_manifest_sha256": None,
        "gallery_sample_order_sha256": "b" * 64,
        "query_sample_order_sha256": "c" * 64,
        "gallery_artifact_sha256": "1" * 64,
        "query_artifact_sha256": "2" * 64,
        "metrics": {
            "top1": 0.5,
            "mrr": 0.75,
            "r_at_5": 1.0,
            "query_count": 2,
            "gallery_count": 2,
            "per_query": [
                {
                    "sample_id": "S001C001P001R001A002",
                    "label": 2,
                    "rank": 1,
                    "predicted_label": 2,
                    "top1_correct": True,
                },
                {
                    "sample_id": "S002C001P002R001A008",
                    "label": 8,
                    "rank": 2,
                    "predicted_label": 2,
                    "top1_correct": False,
                },
            ],
        },
        "telemetry": {
            "wall_time_seconds": 1.0,
            "peak_memory_bytes": 1_024,
            "peak_memory_source": "process_max_rss",
        },
        "provenance": {
            "schema_version": 1,
            "started_at": "2026-09-01T12:00:00Z",
            "ended_at": "2026-09-01T12:00:01Z",
            "command": "evaluate --mode development",
            "git_sha": "0" * 40,
            "git_dirty": False,
            "dependency_lock_sha256": "9" * 64,
            "configuration": {
                "mode": "development",
                "protocol_sha256": "a" * 64,
                "method": "contrastive",
                "seed": seed,
                "condition": "clean",
                "query_definition": "development",
            },
            "inputs": {
                "/cache/gallery.npz": "1" * 64,
                "/cache/query.npz": "2" * 64,
                "/cache/gallery.npz.manifest.json": "e" * 64,
                "/cache/query.npz.manifest.json": "f" * 64,
            },
            "environment": {"python": "3.11"},
        },
    }
    if include_metadata:
        payload.update(
            {
                "method": "contrastive",
                "seed": seed,
                "condition": "clean",
                "query_definition": "development",
            }
        )
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_report_requires_matrix_metadata_and_rejects_duplicate_cells(
    tmp_path: Path,
) -> None:
    incomplete = tmp_path / "incomplete.json"
    _write_result(incomplete, include_metadata=False)
    with pytest.raises(ValueError, match="invalid result schema"):
        build_report([incomplete], tmp_path / "incomplete-report")

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_result(first)
    _write_result(second)
    with pytest.raises(ValueError, match="duplicate result matrix cell"):
        build_report([first, second], tmp_path / "duplicate-report")


def test_report_recomputes_ranks_from_bound_feature_artifacts(tmp_path: Path) -> None:
    gallery = tmp_path / "gallery.npz"
    queries = tmp_path / "queries.npz"
    np.savez(
        gallery,
        embeddings=np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        labels=np.asarray([2, 8], dtype=np.int64),
        sample_ids=np.asarray(["S001C001P001R001A002", "S001C001P001R001A008"]),
    )
    np.savez(
        queries,
        embeddings=np.asarray([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32),
        labels=np.asarray([2, 8], dtype=np.int64),
        sample_ids=np.asarray(["S001C001P001R001A002", "S002C001P002R001A008"]),
    )
    result_path = tmp_path / "result.json"
    _write_result(result_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["gallery_artifact_sha256"] = sha256_file(gallery)
    payload["query_artifact_sha256"] = sha256_file(queries)
    payload["provenance"]["inputs"] = {
        str(gallery): sha256_file(gallery),
        str(queries): sha256_file(queries),
        "/cache/gallery.npz.manifest.json": "e" * 64,
        "/cache/query.npz.manifest.json": "f" * 64,
    }
    valid = EvaluationResult.model_validate(payload)
    _validate_retrieval_metrics(valid, gallery, queries)

    payload["metrics"]["per_query"] = [
        {
            "sample_id": "S001C001P001R001A002",
            "label": 2,
            "rank": 2,
            "predicted_label": 8,
            "top1_correct": False,
        },
        {
            "sample_id": "S002C001P002R001A008",
            "label": 8,
            "rank": 1,
            "predicted_label": 8,
            "top1_correct": True,
        },
    ]
    forged = EvaluationResult.model_validate(payload)
    with pytest.raises(ValueError, match="deterministic feature retrieval"):
        _validate_retrieval_metrics(forged, gallery, queries)


def test_metric_curve_is_deterministic_source_bound_and_shows_seed_range() -> None:
    seeds = (7, 17, 29)
    families = ("coordinate_jitter", "joint_mask", "frame_mask")
    payload = {
        "seeds": list(seeds),
        "curves": [
            {
                "query_definition": "primary",
                "metric": "top1",
                "corruption_family": family,
                "series": [
                    {
                        "method": method,
                        "points": [
                            {
                                "condition": "clean"
                                if index == 0
                                else f"{family}:{index}",
                                "severity": "clean" if index == 0 else str(index),
                                "seed_values": [
                                    {"seed": seed, "value": 1.0 - index * 0.1}
                                    for seed in seeds
                                ],
                                "mean": 1.0 - index * 0.1,
                                "minimum": 1.0 - index * 0.1,
                                "maximum": 1.0 - index * 0.1,
                            }
                            for index in range(4)
                        ],
                    }
                    for method in ("contrastive", "supcon", "contextual")
                ],
            }
            for family in families
        ],
    }
    arguments = {
        "query_definition": "primary",
        "metric": "top1",
        "curves_sha256": "a" * 64,
        "result_set_sha256": "b" * 64,
    }

    first = _metric_curve_svg(payload, **arguments)
    second = _metric_curve_svg(payload, **arguments)

    assert first == second
    assert f"curves_sha256={'a' * 64}" in first
    assert f"result_set_sha256={'b' * 64}" in first
    assert "whiskers span all three seed values" in first
    assert "seed 7=" in first
    assert "Contrastive" in first
    assert "SupCon" in first
    assert "Contextual" in first


def test_core_report_recertification_requires_full_provenance_validator(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = "a" * 64
    result_hash = "b" * 64
    result_paths = [
        (tmp_path / "results" / f"result-{index:03d}.json").resolve()
        for index in range(180)
    ]
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "schema_version": 5,
                "analysis_scope": "core_confirmatory",
                "protocol_sha256": digest,
                "matrix": {
                    "observed_rows": 180,
                    "expected_rows": 180,
                    "complete": True,
                },
                "primary_analysis": {},
                "curve_data": {},
                "error_analysis": {},
                "telemetry": {},
                "failures": {},
                "figures": [],
                "results": [
                    {"file": str(path), "sha256": result_hash} for path in result_paths
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    protocol = load_protocol(protocol_path)
    monkeypatch.setattr(
        report_module,
        "verify_protocol",
        lambda *args, **kwargs: (protocol, digest),
    )
    monkeypatch.setattr(
        report_module,
        "load_evaluation_plan",
        lambda path: SimpleNamespace(expected_rows=180),
    )
    monkeypatch.setattr(report_module, "sha256_file", lambda path: result_hash)
    monkeypatch.setattr(
        report_module,
        "_load_result",
        lambda path: SimpleNamespace(),
    )
    observed: dict[str, int] = {}

    def require_full_validator(results: list, **kwargs: object) -> tuple[int, set]:
        observed["result_count"] = len(results)
        raise RuntimeError("full-validator-called")

    monkeypatch.setattr(
        report_module,
        "_validate_final_provenance",
        require_full_validator,
    )

    with pytest.raises(RuntimeError, match="full-validator-called"):
        validate_core_report_summary(summary_path, protocol_path)
    assert observed == {"result_count": 180}


def test_exact_final_report_writes_analysis_and_source_bound_curve(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeds = (7, 17, 29)
    conditions = (
        "clean",
        "coordinate_jitter:0.01",
        "coordinate_jitter:0.025",
        "coordinate_jitter:0.05",
        "joint_mask:3",
        "joint_mask:6",
        "joint_mask:8",
        "frame_mask:10",
        "frame_mask:25",
        "frame_mask:40",
    )
    query_definitions = ("primary", "official")
    actions = tuple(range(1, 116, 6))
    sample_ids = tuple(f"S002C001P002R001A{action:03d}" for action in actions)
    expected_keys = {
        (method, seed, condition, query_definition)
        for method in ("contrastive", "supcon", "contextual")
        for seed in seeds
        for condition in conditions
        for query_definition in query_definitions
    }
    result_by_path: dict[Path, SimpleNamespace] = {}
    for index, (method, seed, condition, query_definition) in enumerate(
        sorted(expected_keys)
    ):
        correctness = (
            (True,) * len(sample_ids)
            if condition == "clean" or method == "contextual"
            else (False,) * len(sample_ids)
            if method == "contrastive"
            else tuple(index % 2 == 0 for index in range(len(sample_ids)))
        )
        per_query = tuple(
            SimpleNamespace(
                sample_id=sample_id,
                label=int(sample_id[-3:]),
                rank=1 if value else 2,
                predicted_label=(
                    int(sample_id[-3:])
                    if value
                    else actions[(row_index + 1) % len(actions)]
                ),
                top1_correct=value,
            )
            for row_index, (sample_id, value) in enumerate(
                zip(sample_ids, correctness, strict=True)
            )
        )
        reciprocal_ranks = [1.0 / row.rank for row in per_query]
        result = SimpleNamespace(
            mode="final",
            protocol_sha256="a" * 64,
            evaluation_plan_sha256="b" * 64,
            final_run_set_sha256="c" * 64,
            gallery_sample_order_sha256="d" * 64,
            query_sample_order_sha256=(
                "e" * 64 if query_definition == "primary" else "f" * 64
            ),
            method=method,
            seed=seed,
            condition=condition,
            query_definition=query_definition,
            metrics=SimpleNamespace(
                top1=sum(correctness) / len(correctness),
                mrr=sum(reciprocal_ranks) / len(reciprocal_ranks),
                r_at_5=1.0,
                query_count=len(sample_ids),
                per_query=per_query,
            ),
            telemetry=RuntimeTelemetry(
                wall_time_seconds=1.0,
                peak_memory_bytes=1_024,
                peak_memory_source="process_max_rss",
            ),
        )
        result_path = (tmp_path / "results" / f"result-{index:03d}.json").resolve()
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text("{}\n", encoding="utf-8")
        result_by_path[result_path] = result

    plan = SimpleNamespace(
        methods=("contrastive", "supcon", "contextual"),
        seeds=seeds,
        conditions=conditions,
        query_definitions=query_definitions,
        metrics=("top1", "mrr", "r_at_5"),
        expected_rows=180,
    )
    telemetry = {
        "wall_time_seconds": 2.0,
        "peak_memory_bytes": 2_048,
        "peak_memory_source": "process_max_rss",
    }
    runs = []
    for method in plan.methods:
        for seed in seeds:
            manifest_path = tmp_path / "runs" / f"{method}-{seed}" / "run-manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps({"telemetry": telemetry}),
                encoding="utf-8",
            )
            runs.append(
                SimpleNamespace(
                    method=method,
                    seed=seed,
                    run_manifest_relative_path=manifest_path.relative_to(
                        tmp_path
                    ).as_posix(),
                    run_manifest_sha256=sha256_file(manifest_path),
                )
            )
    run_set = SimpleNamespace(runs=tuple(runs))
    failure_payload = {
        "schema_version": 1,
        "protocol_sha256": "a" * 64,
        "final_run_set_sha256": "c" * 64,
        "test_opening_ledger_sha256": "9" * 64,
        "attempt_count": 9,
        "failed_attempt_count": 0,
        "attempts": [],
        "unresolved_failures": [],
    }
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        report_module,
        "_load_result",
        lambda path: result_by_path[path.resolve()],
    )
    monkeypatch.setattr(report_module, "load_evaluation_plan", lambda path: plan)
    monkeypatch.setattr(report_module, "load_final_run_set", lambda path: run_set)
    monkeypatch.setattr(
        report_module,
        "derive_core_failure_status",
        lambda protocol: failure_payload,
    )
    monkeypatch.setattr(
        report_module,
        "_validate_final_provenance",
        lambda results, **kwargs: (180, expected_keys),
    )

    destination = tmp_path / "report"
    summary = build_report(
        result_by_path,
        destination,
        protocol_path=protocol_path,
    )

    analysis_path = destination / "primary-analysis.json"
    figure_path = destination / "primary-top1-corruption-curves.svg"
    assert summary["schema_version"] == 5
    assert summary["matrix"] == {
        "observed_rows": 180,
        "expected_rows": 180,
        "complete": True,
    }
    assert summary["primary_analysis"]["estimate"] == -1.0
    assert summary["primary_analysis"]["sha256"] == sha256_file(analysis_path)
    assert summary["curve_data"]["curve_count"] == 18
    assert summary["error_analysis"]["per_class_row_count"] == 3_600
    assert summary["telemetry"]["evaluation_operation_count"] == 180
    assert summary["telemetry"]["training_operation_count"] == 9
    assert summary["failures"]["unresolved_failure_count"] == 0
    assert len(summary["figures"]) == 6
    assert summary["figures"][0]["sha256"] == sha256_file(figure_path)
    assert (
        summary["figures"][0]["source_curves_sha256"] == summary["curve_data"]["sha256"]
    )
    assert "curves_sha256=" in figure_path.read_text(encoding="utf-8")


def test_report_marks_complete_only_for_exact_authorized_180_rows(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = load_protocol(protocol_path)
    digest = protocol_digest(protocol)
    lock_path, plan_path, run_set_path = write_lock_bundle(tmp_path, digest)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    plan = load_evaluation_plan(plan_path)
    run_set = load_final_run_set(run_set_path)
    assert plan.anchor_manifest is not None
    assert plan.source_inventory_manifest is not None
    assert plan.official_query_manifest is not None
    assert plan.primary_query_manifest is not None
    common = {
        "schema_version": 4,
        "mode": "final",
        "protocol_sha256": digest,
        "evaluation_plan_sha256": evaluation_plan_digest(plan),
        "final_run_set_sha256": final_run_set_digest(run_set),
        "protocol_lock_sha256": sha256_file(lock_path),
        "test_opening_ledger_sha256": "6" * 64,
        "gallery_sidecar_sha256": "e" * 64,
        "query_sidecar_sha256": "f" * 64,
        "source_inventory_manifest_sha256": (plan.source_inventory_manifest.sha256),
        "anchor_manifest_sha256": plan.anchor_manifest.sha256,
        "official_query_manifest_sha256": (plan.official_query_manifest.sha256),
        "primary_query_manifest_sha256": plan.primary_query_manifest.sha256,
        "gallery_artifact_sha256": "1" * 64,
        "query_artifact_sha256": "2" * 64,
        "gallery_sample_order_sha256": sample_order_digest(
            plan.anchor_manifest.sample_ids
        ),
        "telemetry": {
            "wall_time_seconds": 1.0,
            "peak_memory_bytes": 1_024,
            "peak_memory_source": "process_max_rss",
        },
        "provenance": {},
    }
    result_paths = []
    for method in plan.methods:
        for seed in plan.seeds:
            run = final_run_for(run_set, method, seed)
            for condition in plan.conditions:
                for query_definition in plan.query_definitions:
                    binding = (
                        plan.primary_query_manifest
                        if query_definition == "primary"
                        else plan.official_query_manifest
                    )
                    per_query = [
                        {
                            "sample_id": sample_id,
                            "label": int(sample_id[-3:]),
                            "rank": 1,
                            "predicted_label": int(sample_id[-3:]),
                            "top1_correct": True,
                        }
                        for sample_id in binding.sample_ids
                    ]
                    payload = {
                        **common,
                        "run_manifest_sha256": run.run_manifest_sha256,
                        "checkpoint_sha256": run.checkpoint_sha256,
                        "method": method,
                        "seed": seed,
                        "condition": condition,
                        "query_definition": query_definition,
                        "query_sample_order_sha256": sample_order_digest(
                            binding.sample_ids
                        ),
                        "metrics": {
                            "top1": 1.0,
                            "mrr": 1.0,
                            "r_at_5": 1.0,
                            "query_count": binding.sample_count,
                            "gallery_count": plan.anchor_manifest.sample_count,
                            "per_query": per_query,
                        },
                    }
                    path = (
                        tmp_path
                        / "results"
                        / (
                            f"{method}-{seed}-{condition.replace(':', '_')}-"
                            f"{query_definition}.json"
                        )
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    result_paths.append(path)

    with pytest.raises(ValueError, match="invalid result schema|provenance"):
        build_report(
            result_paths,
            tmp_path / "report",
            protocol_path=protocol_path,
        )
