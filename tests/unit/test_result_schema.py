from __future__ import annotations

import pytest

from pose_embed.evaluation.result import EvaluationResult


def _base_payload() -> dict:
    return {
        "schema_version": 4,
        "mode": "development",
        "protocol_sha256": "a" * 64,
        "evaluation_plan_sha256": None,
        "final_run_set_sha256": None,
        "protocol_lock_sha256": None,
        "test_opening_ledger_sha256": None,
        "run_manifest_sha256": None,
        "checkpoint_sha256": "b" * 64,
        "gallery_sidecar_sha256": "c" * 64,
        "query_sidecar_sha256": "d" * 64,
        "source_inventory_manifest_sha256": None,
        "anchor_manifest_sha256": None,
        "official_query_manifest_sha256": None,
        "primary_query_manifest_sha256": None,
        "method": "contrastive",
        "seed": 7,
        "condition": "clean",
        "query_definition": "development",
        "gallery_artifact_sha256": "e" * 64,
        "query_artifact_sha256": "f" * 64,
        "gallery_sample_order_sha256": "1" * 64,
        "query_sample_order_sha256": "2" * 64,
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
                "seed": 7,
                "condition": "clean",
                "query_definition": "development",
            },
            "inputs": {
                "/cache/gallery.npz": "e" * 64,
                "/cache/query.npz": "f" * 64,
                "/cache/gallery.npz.manifest.json": "c" * 64,
                "/cache/query.npz.manifest.json": "d" * 64,
            },
            "environment": {"python": "3.11"},
        },
    }


def test_result_schema_rejects_nonfinite_or_inconsistent_metrics() -> None:
    payload = _base_payload()
    payload["metrics"]["top1"] = float("nan")
    with pytest.raises(ValueError):
        EvaluationResult.model_validate(payload)

    payload = _base_payload()
    payload["provenance"] = {}
    with pytest.raises(ValueError, match="provenance"):
        EvaluationResult.model_validate(payload)

    payload = _base_payload()
    payload["metrics"]["query_count"] = 3
    with pytest.raises(ValueError, match="per-query"):
        EvaluationResult.model_validate(payload)

    payload = _base_payload()
    payload["telemetry"]["wall_time_seconds"] = 2.0
    with pytest.raises(ValueError, match="telemetry"):
        EvaluationResult.model_validate(payload)


def test_final_result_requires_complete_lock_and_artifact_provenance() -> None:
    payload = _base_payload()
    payload.update({"mode": "final", "query_definition": "primary"})
    payload["provenance"]["command"] = "evaluate --mode final"
    payload["provenance"]["configuration"].update(
        {"mode": "final", "query_definition": "primary"}
    )
    with pytest.raises(ValueError, match="final result requires"):
        EvaluationResult.model_validate(payload)

    for field, character in {
        "evaluation_plan_sha256": "3",
        "final_run_set_sha256": "4",
        "protocol_lock_sha256": "5",
        "test_opening_ledger_sha256": "6",
        "run_manifest_sha256": "7",
        "source_inventory_manifest_sha256": "8",
        "anchor_manifest_sha256": "9",
        "official_query_manifest_sha256": "a",
        "primary_query_manifest_sha256": "b",
    }.items():
        payload[field] = character * 64
        payload["provenance"]["inputs"][f"/locked/{field}"] = character * 64
    assert EvaluationResult.model_validate(payload).mode == "final"


def test_exploratory_results_are_labeled_and_excluded_from_core_mode() -> None:
    payload = _base_payload()
    payload.update(
        {
            "mode": "exploratory",
            "method": "multi_similarity_with_miner",
            "query_definition": "primary",
            "stretch_gate_evidence_sha256": "c" * 64,
        }
    )
    for field, character in {
        "evaluation_plan_sha256": "3",
        "final_run_set_sha256": "4",
        "protocol_lock_sha256": "5",
        "test_opening_ledger_sha256": "6",
        "run_manifest_sha256": "7",
        "source_inventory_manifest_sha256": "8",
        "anchor_manifest_sha256": "9",
        "official_query_manifest_sha256": "a",
        "primary_query_manifest_sha256": "b",
    }.items():
        payload[field] = character * 64
        payload["provenance"]["inputs"][f"/locked/{field}"] = character * 64
    payload["provenance"]["inputs"]["/locked/stretch-gates.json"] = "c" * 64
    payload["provenance"]["command"] = "evaluate --mode exploratory"
    payload["provenance"]["configuration"].update(
        {
            "mode": "exploratory",
            "method": "multi_similarity_with_miner",
            "query_definition": "primary",
        }
    )
    assert EvaluationResult.model_validate(payload).mode == "exploratory"

    payload["mode"] = "final"
    payload["provenance"]["command"] = "evaluate --mode final"
    payload["provenance"]["configuration"]["mode"] = "final"
    with pytest.raises(ValueError, match="core final"):
        EvaluationResult.model_validate(payload)
