from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as functional

from pose_embed.cli import main
from pose_embed.data import ManifestRecord
from pose_embed.provenance import sha256_file


def _write_fixture(
    pose_path: Path,
    manifest_path: Path,
    *,
    sample_ids: list[str],
    split: str,
) -> None:
    actions = sorted({int(sample_id[-3:]) for sample_id in sample_ids})
    action_value = {
        action: -1.0 + 2.0 * index / max(1, len(actions) - 1)
        for index, action in enumerate(actions)
    }
    poses = np.stack(
        [
            np.full((1, 6, 17, 3), action_value[int(sample_id[-3:])], np.float32)
            for sample_id in sample_ids
        ]
    )
    labels = np.asarray([int(sample_id[-3:]) for sample_id in sample_ids])
    np.savez(pose_path, poses=poses, labels=labels, sample_ids=sample_ids)
    manifest_path.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id,
                split=split,
                is_anchor=split == "novel_anchor",
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )


def _extract(
    *,
    poses: Path,
    features: Path,
    protocol_path: Path,
    manifest: Path,
    role: str,
    split: str,
) -> None:
    assert (
        main(
            [
                "features",
                "extract",
                "--input",
                str(poses),
                "--output",
                str(features),
                "--protocol-config",
                str(protocol_path),
                "--manifest",
                str(manifest),
                "--role",
                role,
                "--split",
                split,
                "--embedding-dimension",
                "6",
            ]
        )
        == 0
    )


def _development_pair(
    tmp_path: Path,
    protocol_path: Path,
) -> tuple[Path, Path, Path, Path]:
    gallery_poses = tmp_path / "gallery-poses.npz"
    gallery = tmp_path / "gallery.npz"
    gallery_manifest = tmp_path / "gallery.jsonl"
    query_poses = tmp_path / "query-poses.npz"
    queries = tmp_path / "queries.npz"
    query_manifest = tmp_path / "queries.jsonl"
    _write_fixture(
        gallery_poses,
        gallery_manifest,
        sample_ids=["S001C001P001R001A002", "S001C001P001R001A008"],
        split="development_validation",
    )
    _write_fixture(
        query_poses,
        query_manifest,
        sample_ids=["S002C001P002R001A002", "S002C001P002R001A008"],
        split="development_validation",
    )
    _extract(
        poses=gallery_poses,
        features=gallery,
        protocol_path=protocol_path,
        manifest=gallery_manifest,
        role="gallery_clean",
        split="development_validation",
    )
    _extract(
        poses=query_poses,
        features=queries,
        protocol_path=protocol_path,
        manifest=query_manifest,
        role="query_clean",
        split="development_validation",
    )
    return gallery, queries, gallery_manifest, query_manifest


def _write_experiment(path: Path) -> None:
    path.write_text(
        """schema_version: 1
name: fixture-contrastive
objective: contrastive
seed: 7
input_dimension: 6
embedding_dimension: 4
epochs: 3
learning_rate: 0.01
weight_decay: 0.0
classes_per_batch: 2
samples_per_class: 2
temperature: 0.1
positive_margin: 0.9
negative_margin: 0.6
""",
        encoding="utf-8",
    )


def _checkpoint_backed_development_pair(
    tmp_path: Path,
    protocol_path: Path,
) -> tuple[Path, Path, Path, Path]:
    training_dir = tmp_path / "training"
    training_dir.mkdir()
    training_poses = training_dir / "poses.npz"
    training_manifest = training_dir / "manifest.jsonl"
    training_features = training_dir / "features.npz"
    config = training_dir / "experiment.yaml"
    run = training_dir / "run"
    training_ids = [
        *(f"S{index + 1:03d}C001P001R001A003" for index in range(4)),
        *(f"S{index + 5:03d}C001P002R001A004" for index in range(4)),
    ]
    _write_fixture(
        training_poses,
        training_manifest,
        sample_ids=training_ids,
        split="development_train",
    )
    _write_experiment(config)
    _extract(
        poses=training_poses,
        features=training_features,
        protocol_path=protocol_path,
        manifest=training_manifest,
        role="training",
        split="development_train",
    )
    assert (
        main(
            [
                "train",
                "--config",
                str(config),
                "--input",
                str(training_features),
                "--output-dir",
                str(run),
                "--protocol-config",
                str(protocol_path),
                "--manifest",
                str(training_manifest),
                "--allow-fixture",
            ]
        )
        == 0
    )

    raw_dir = tmp_path / "raw-evaluation"
    raw_dir.mkdir()
    raw_gallery, raw_queries, gallery_manifest, query_manifest = _development_pair(
        raw_dir, protocol_path
    )
    gallery = tmp_path / "gallery-embeddings.npz"
    queries = tmp_path / "query-embeddings.npz"
    for source, output, manifest in (
        (raw_gallery, gallery, gallery_manifest),
        (raw_queries, queries, query_manifest),
    ):
        assert (
            main(
                [
                    "features",
                    "apply-head",
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                    "--checkpoint",
                    str(run / "head.pt"),
                    "--run-manifest",
                    str(run / "run-manifest.json"),
                    "--protocol-config",
                    str(protocol_path),
                    "--manifest",
                    str(manifest),
                    "--allow-fixture",
                ]
            )
            == 0
        )
    return gallery, queries, gallery_manifest, query_manifest


def test_fixture_extract_and_train_are_auditable(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    poses = tmp_path / "poses.npz"
    manifest_path = tmp_path / "train.jsonl"
    features = tmp_path / "features.npz"
    config = tmp_path / "experiment.yaml"
    run = tmp_path / "run"
    sample_ids = [f"S{index + 1:03d}C001P001R001A003" for index in range(4)] + [
        f"S{index + 5:03d}C001P002R001A004" for index in range(4)
    ]
    _write_fixture(
        poses,
        manifest_path,
        sample_ids=sample_ids,
        split="development_train",
    )
    _write_experiment(config)
    _extract(
        poses=poses,
        features=features,
        protocol_path=protocol_path,
        manifest=manifest_path,
        role="training",
        split="development_train",
    )

    assert (
        main(
            [
                "train",
                "--config",
                str(config),
                "--input",
                str(features),
                "--output-dir",
                str(run),
                "--protocol-config",
                str(protocol_path),
                "--manifest",
                str(manifest_path),
                "--allow-fixture",
            ]
        )
        == 0
    )
    metrics = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    run_manifest = json.loads((run / "run-manifest.json").read_text(encoding="utf-8"))
    assert len(metrics["epoch_losses"]) == 3
    assert metrics["input_metadata"]["scientific_use_allowed"] is False
    assert run_manifest["inputs"][str(features)]
    assert metrics["telemetry"] == run_manifest["telemetry"]
    assert metrics["telemetry"]["wall_time_seconds"] > 0
    assert (run / "head.pt").is_file()
    assert (run / "batch-plan.json").is_file()


def test_cpu_pipeline_applies_trained_checkpoint_before_retrieval_and_report(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    train_poses = tmp_path / "train-poses.npz"
    train_manifest = tmp_path / "train.jsonl"
    train_features = tmp_path / "train-features.npz"
    config = tmp_path / "experiment.yaml"
    run = tmp_path / "run"
    training_ids = [
        *(f"S{index + 1:03d}C001P001R001A003" for index in range(4)),
        *(f"S{index + 5:03d}C001P002R001A004" for index in range(4)),
    ]
    _write_fixture(
        train_poses,
        train_manifest,
        sample_ids=training_ids,
        split="development_train",
    )
    _write_experiment(config)
    _extract(
        poses=train_poses,
        features=train_features,
        protocol_path=protocol_path,
        manifest=train_manifest,
        role="training",
        split="development_train",
    )
    assert (
        main(
            [
                "train",
                "--config",
                str(config),
                "--input",
                str(train_features),
                "--output-dir",
                str(run),
                "--protocol-config",
                str(protocol_path),
                "--manifest",
                str(train_manifest),
                "--allow-fixture",
            ]
        )
        == 0
    )

    evaluation_dir = tmp_path / "evaluation"
    evaluation_dir.mkdir()
    raw_gallery, raw_queries, gallery_manifest, query_manifest = _development_pair(
        evaluation_dir, protocol_path
    )
    gallery = tmp_path / "gallery-embeddings.npz"
    queries = tmp_path / "query-embeddings.npz"
    for source, output, manifest in (
        (raw_gallery, gallery, gallery_manifest),
        (raw_queries, queries, query_manifest),
    ):
        assert (
            main(
                [
                    "features",
                    "apply-head",
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                    "--checkpoint",
                    str(run / "head.pt"),
                    "--run-manifest",
                    str(run / "run-manifest.json"),
                    "--protocol-config",
                    str(protocol_path),
                    "--manifest",
                    str(manifest),
                    "--allow-fixture",
                ]
            )
            == 0
        )

    with np.load(raw_gallery, allow_pickle=False) as raw_archive:
        raw = torch.as_tensor(raw_archive["features"], dtype=torch.float32)
    checkpoint = torch.load(run / "head.pt", map_location="cpu", weights_only=True)
    expected = functional.normalize(
        functional.linear(
            raw,
            checkpoint["state_dict"]["projection.weight"],
            checkpoint["state_dict"]["projection.bias"],
        ),
        dim=-1,
    ).numpy()
    with np.load(gallery, allow_pickle=False) as projected_archive:
        projected = projected_archive["embeddings"]
    np.testing.assert_allclose(projected, expected, rtol=1e-6, atol=1e-6)

    result = tmp_path / "checkpoint-backed-result.json"
    assert (
        main(
            [
                "evaluate",
                "--gallery",
                str(gallery),
                "--queries",
                str(queries),
                "--gallery-manifest",
                str(gallery_manifest),
                "--query-manifest",
                str(query_manifest),
                "--method",
                "contrastive",
                "--seed",
                "7",
                "--condition",
                "clean",
                "--query-definition",
                "development",
                "--allow-fixture",
                "--output",
                str(result),
                "--mode",
                "development",
                "--protocol-config",
                str(protocol_path),
            ]
        )
        == 0
    )
    result_payload = json.loads(result.read_text(encoding="utf-8"))
    assert result_payload["checkpoint_sha256"] == sha256_file(run / "head.pt")
    assert result_payload["method"] == "contrastive"
    assert result_payload["seed"] == 7
    assert result_payload["telemetry"]["wall_time_seconds"] > 0
    assert (
        result_payload["provenance"]["started_at"]
        != (result_payload["provenance"]["ended_at"])
    )

    report = tmp_path / "checkpoint-backed-report"
    assert (
        main(
            [
                "report",
                "build",
                "--results",
                str(result),
                "--output-dir",
                str(report),
            ]
        )
        == 0
    )
    summary = json.loads((report / "summary.json").read_text(encoding="utf-8"))
    assert summary["analysis_scope"] == "development"
    assert summary["matrix"]["observed_rows"] == 1


def test_evaluate_requires_lock_only_for_final_mode(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    gallery, queries, gallery_manifest, query_manifest = (
        _checkpoint_backed_development_pair(tmp_path, protocol_path)
    )
    development = tmp_path / "development.json"
    blocked_final = tmp_path / "final.json"
    common = [
        "--gallery",
        str(gallery),
        "--queries",
        str(queries),
        "--protocol-config",
        str(protocol_path),
        "--gallery-manifest",
        str(gallery_manifest),
        "--query-manifest",
        str(query_manifest),
        "--method",
        "contrastive",
        "--seed",
        "7",
        "--condition",
        "clean",
        "--query-definition",
        "development",
        "--allow-fixture",
    ]
    assert (
        main(
            ["evaluate", *common, "--output", str(development), "--mode", "development"]
        )
        == 0
    )
    assert (
        main(["evaluate", *common, "--output", str(blocked_final), "--mode", "final"])
        == 2
    )
    assert development.is_file()
    assert not blocked_final.exists()


def test_report_build_indexes_every_result(protocol_path: Path, tmp_path: Path) -> None:
    gallery, queries, gallery_manifest, query_manifest = (
        _checkpoint_backed_development_pair(tmp_path, protocol_path)
    )
    result = tmp_path / "result.json"
    report = tmp_path / "report"
    assert (
        main(
            [
                "evaluate",
                "--gallery",
                str(gallery),
                "--queries",
                str(queries),
                "--gallery-manifest",
                str(gallery_manifest),
                "--query-manifest",
                str(query_manifest),
                "--method",
                "contrastive",
                "--seed",
                "7",
                "--condition",
                "clean",
                "--query-definition",
                "development",
                "--allow-fixture",
                "--output",
                str(result),
                "--mode",
                "development",
                "--protocol-config",
                str(protocol_path),
            ]
        )
        == 0
    )
    assert (
        main(["report", "build", "--results", str(result), "--output-dir", str(report)])
        == 0
    )
    summary = json.loads((report / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["results"]) == 1
    assert summary["matrix"]["observed_rows"] == 1


def test_final_evaluation_does_not_accept_caller_selected_lock_paths(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gallery_poses = tmp_path / "novel-gallery-poses.npz"
    gallery = tmp_path / "novel-gallery.npz"
    gallery_manifest = tmp_path / "novel-gallery.jsonl"
    query_poses = tmp_path / "novel-query-poses.npz"
    queries = tmp_path / "novel-query.npz"
    query_manifest = tmp_path / "novel-query.jsonl"
    _write_fixture(
        gallery_poses,
        gallery_manifest,
        sample_ids=["S001C001P001R001A001"],
        split="novel_anchor",
    )
    _write_fixture(
        query_poses,
        query_manifest,
        sample_ids=["S002C001P002R001A001"],
        split="novel_query_primary",
    )
    _extract(
        poses=gallery_poses,
        features=gallery,
        protocol_path=protocol_path,
        manifest=gallery_manifest,
        role="gallery_clean",
        split="novel_anchor",
    )
    _extract(
        poses=query_poses,
        features=queries,
        protocol_path=protocol_path,
        manifest=query_manifest,
        role="query_clean",
        split="novel_query_primary",
    )
    output = tmp_path / "final.json"
    monkeypatch.delenv("POSE_EMBED_ARTIFACT_ROOT", raising=False)

    assert (
        main(
            [
                "evaluate",
                "--gallery",
                str(gallery),
                "--queries",
                str(queries),
                "--gallery-manifest",
                str(gallery_manifest),
                "--query-manifest",
                str(query_manifest),
                "--method",
                "contrastive",
                "--seed",
                "7",
                "--condition",
                "clean",
                "--query-definition",
                "primary",
                "--allow-fixture",
                "--output",
                str(output),
                "--mode",
                "final",
                "--protocol-config",
                str(protocol_path),
            ]
        )
        == 2
    )
    assert not output.exists()
