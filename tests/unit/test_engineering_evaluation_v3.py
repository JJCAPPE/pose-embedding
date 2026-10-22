from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as functional

from pose_embed.artifacts import load_feature_sidecar
from pose_embed.corruptions.pose import apply_corruption_v3
from pose_embed.evaluation.result import EvaluationResult
from pose_embed.evaluation.runner import evaluate_files
from pose_embed.geometry_v3 import LEVELS
from pose_embed.report import build_report
from tests.unit.test_evaluation_integrity import _apply_test_head, _make_features


@pytest.mark.parametrize(
    ("family", "severity"),
    [(family, severity) for family, levels in LEVELS.items() for severity in levels],
)
def test_v3_engineering_fixture_runs_extraction_projection_retrieval_and_report(
    repository_root: Path, tmp_path: Path, family: str, severity: float
):
    protocol_path = repository_root / "configs/protocol.v3.yaml"
    gallery, gallery_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="gallery",
        sample_ids=["S001C001P001R001A002", "S001C001P001R001A008"],
        split="development_validation",
        role="gallery_clean",
    )
    queries, query_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="queries",
        sample_ids=["S002C001P002R001A002", "S002C001P002R001A008"],
        split="development_validation",
        role="query_corrupted",
        corruption_family=family,
        corruption_severity=severity,
    )
    with np.load(tmp_path / "queries-poses.npz", allow_pickle=False) as source:
        corrupted = torch.stack(
            [
                apply_corruption_v3(
                    torch.from_numpy(pose),
                    family=family,
                    severity=severity,
                    sample_id=sample_id,
                )
                for pose, sample_id in zip(
                    source["poses"], source["sample_ids"], strict=True
                )
            ]
        )
    with np.load(queries, allow_pickle=False) as features:
        expected = functional.normalize(
            corrupted.mean(dim=(1, 2)).flatten(start_dim=1)
            @ torch.from_numpy(features["fixture_projection"]),
            dim=1,
        )
        np.testing.assert_array_equal(features["features"], expected.numpy())
    projected_gallery = _apply_test_head(
        tmp_path, protocol_path, gallery, gallery_manifest, name="gallery"
    )
    projected_queries = _apply_test_head(
        tmp_path, protocol_path, queries, query_manifest, name="queries"
    )
    sidecar = load_feature_sidecar(projected_queries)
    assert sidecar.backend == "fixture"
    assert sidecar.scientific_use_allowed is False
    condition = f"{family}:{severity:g}"
    assert sidecar.condition == condition
    arguments = {
        "protocol_path": protocol_path,
        "gallery_manifest_path": gallery_manifest,
        "query_manifest_path": query_manifest,
        "method": "contrastive",
        "seed": 7,
        "condition": condition,
        "query_definition": "development",
        "allow_fixture": True,
    }
    result_path = tmp_path / "engineering.json"
    result = EvaluationResult.model_validate(
        evaluate_files(
            projected_gallery,
            projected_queries,
            result_path,
            mode="engineering",
            **arguments,
        )
    )
    assert result.mode == "engineering"
    assert result.metrics.query_count == 2
    assert result.provenance.configuration["mode"] == "engineering"
    assert result.final_run_set_sha256 is None
    assert result.test_opening_ledger_sha256 is None
    report = build_report([result_path], tmp_path / "report")
    assert report["analysis_scope"] == "development"
    assert report["matrix"]["complete"] is False
    assert report["primary_analysis"] is None

    with pytest.raises(ValueError, match="clean-only"):
        evaluate_files(
            projected_gallery,
            projected_queries,
            tmp_path / "selection.json",
            mode="development",
            **arguments,
        )
    with pytest.raises(ValueError, match="never permit fixture"):
        evaluate_files(
            projected_gallery,
            projected_queries,
            tmp_path / "final.json",
            mode="final",
            **arguments,
        )
    assert not (tmp_path / "selection.json").exists()
    assert not (tmp_path / "final.json").exists()
