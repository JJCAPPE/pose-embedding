from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from pose_embed.artifacts import load_feature_sidecar, validate_feature_artifact
from pose_embed.config import ExperimentConfig, load_protocol
from pose_embed.data import ManifestRecord
from pose_embed.evaluation.runner import evaluate_files
from pose_embed.features import apply_trained_head, extract_fixture_features
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file


def _make_features(
    tmp_path: Path,
    protocol_path: Path,
    *,
    name: str,
    sample_ids: list[str],
    split: str,
    role: str,
) -> tuple[Path, Path]:
    poses_path = tmp_path / f"{name}-poses.npz"
    feature_path = tmp_path / f"{name}-features.npz"
    manifest_path = tmp_path / f"{name}.jsonl"
    labels = np.asarray([int(sample_id[-3:]) for sample_id in sample_ids])
    poses = np.arange(len(sample_ids) * 1 * 6 * 17 * 3, dtype=np.float32).reshape(
        len(sample_ids), 1, 6, 17, 3
    )
    np.savez(poses_path, poses=poses, labels=labels, sample_ids=sample_ids)
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
    extract_fixture_features(
        poses_path,
        feature_path,
        protocol_path=protocol_path,
        manifest_path=manifest_path,
        role=role,
        split=split,
        embedding_dimension=6,
    )
    return feature_path, manifest_path


def _apply_test_head(
    tmp_path: Path,
    protocol_path: Path,
    features: Path,
    manifest: Path,
    *,
    name: str,
) -> Path:
    config = ExperimentConfig(
        schema_version=1,
        name="fixture-contrastive",
        objective="contrastive",
        seed=7,
        input_dimension=6,
        embedding_dimension=4,
        epochs=1,
        learning_rate=0.01,
        weight_decay=0.0,
        classes_per_batch=2,
        samples_per_class=2,
        temperature=0.1,
        positive_margin=0.9,
        negative_margin=0.6,
    )
    checkpoint = tmp_path / "head.pt"
    run_manifest = tmp_path / "run-manifest.json"
    if not checkpoint.exists():
        torch.save(
            {
                "config": config.model_dump(mode="json"),
                "state_dict": {
                    "projection.weight": torch.eye(4, 6),
                    "projection.bias": torch.zeros(4),
                },
            },
            checkpoint,
        )
        run_manifest.write_text(
            json.dumps(
                {
                    "configuration": {"experiment": config.model_dump(mode="json")},
                    "outputs": {"checkpoint": sha256_file(checkpoint)},
                    "protocol_sha256": protocol_digest(load_protocol(protocol_path)),
                    "scientific_use_allowed": False,
                }
            ),
            encoding="utf-8",
        )
    output = tmp_path / f"{name}-embeddings.npz"
    apply_trained_head(
        features,
        output,
        checkpoint_path=checkpoint,
        run_manifest_path=run_manifest,
        protocol_path=protocol_path,
        manifest_path=manifest,
        allow_fixture=True,
    )
    return output


def test_development_evaluation_requires_roles_and_emits_matrix_metadata(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    gallery, gallery_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="gallery",
        sample_ids=[
            "S001C001P001R001A002",
            "S001C001P001R001A008",
        ],
        split="development_validation",
        role="gallery_clean",
    )
    queries, query_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="queries",
        sample_ids=[
            "S002C001P002R001A002",
            "S002C001P002R001A008",
        ],
        split="development_validation",
        role="query_clean",
    )

    projected_gallery = _apply_test_head(
        tmp_path, protocol_path, gallery, gallery_manifest, name="gallery"
    )
    projected_queries = _apply_test_head(
        tmp_path, protocol_path, queries, query_manifest, name="queries"
    )
    gallery_sidecar = load_feature_sidecar(projected_gallery)
    query_sidecar = load_feature_sidecar(projected_queries)
    assert (
        gallery_sidecar.head_checkpoint_sha256 == query_sidecar.head_checkpoint_sha256
    )
    assert (
        gallery_sidecar.encoder_checkpoint_sha256
        == query_sidecar.encoder_checkpoint_sha256
    )
    assert gallery_sidecar.base_artifact_sha256 == sha256_file(gallery)
    assert query_sidecar.base_artifact_sha256 == sha256_file(queries)
    payload = evaluate_files(
        projected_gallery,
        projected_queries,
        tmp_path / "result.json",
        mode="development",
        protocol_path=protocol_path,
        gallery_manifest_path=gallery_manifest,
        query_manifest_path=query_manifest,
        method="contrastive",
        seed=7,
        condition="clean",
        query_definition="development",
        allow_fixture=True,
    )
    assert (
        payload["method"],
        payload["seed"],
        payload["condition"],
        payload["query_definition"],
    ) == ("contrastive", 7, "clean", "development")

    with gallery.open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="base feature artifact hash mismatch"):
        evaluate_files(
            projected_gallery,
            projected_queries,
            tmp_path / "tampered-lineage-result.json",
            mode="development",
            protocol_path=protocol_path,
            gallery_manifest_path=gallery_manifest,
            query_manifest_path=query_manifest,
            method="contrastive",
            seed=7,
            condition="clean",
            query_definition="development",
            allow_fixture=True,
        )


def test_trained_embedding_validation_recomputes_the_locked_head(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    base, manifest = _make_features(
        tmp_path,
        protocol_path,
        name="recompute",
        sample_ids=[
            "S001C001P001R001A002",
            "S001C001P001R001A008",
        ],
        split="development_validation",
        role="gallery_clean",
    )
    projected = _apply_test_head(
        tmp_path,
        protocol_path,
        base,
        manifest,
        name="recompute",
    )
    with np.load(projected, allow_pickle=False) as archive:
        payload = {key: np.asarray(archive[key]) for key in archive.files}
    payload["embeddings"] = np.flip(payload["embeddings"], axis=0).copy()
    np.savez_compressed(projected, **payload)
    sidecar_path = projected.with_suffix(f"{projected.suffix}.manifest.json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    sidecar["artifact_sha256"] = sha256_file(projected)
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

    with pytest.raises(ValueError, match="deterministic head application"):
        validate_feature_artifact(
            projected,
            protocol=load_protocol(protocol_path),
            manifest_path=manifest,
            allow_fixture=True,
        )


def test_development_evaluation_rejects_novel_roles(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    gallery, gallery_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="novel-gallery",
        sample_ids=["S001C001P001R001A001"],
        split="novel_anchor",
        role="gallery_clean",
    )
    queries, query_manifest = _make_features(
        tmp_path,
        protocol_path,
        name="novel-query",
        sample_ids=["S002C001P002R001A001"],
        split="novel_query_primary",
        role="query_clean",
    )

    with pytest.raises(ValueError, match="rejects every novel-test split"):
        evaluate_files(
            gallery,
            queries,
            tmp_path / "result.json",
            mode="development",
            protocol_path=protocol_path,
            gallery_manifest_path=gallery_manifest,
            query_manifest_path=query_manifest,
            method="contrastive",
            seed=7,
            condition="clean",
            query_definition="development",
            allow_fixture=True,
        )


def test_exploratory_evaluation_requires_labeled_multi_similarity_inputs(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.npz"
    with pytest.raises(
        ValueError, match="exploratory evaluation requires its run manifest"
    ):
        evaluate_files(
            missing,
            missing,
            tmp_path / "result.json",
            mode="exploratory",
            protocol_path=protocol_path,
            gallery_manifest_path=missing,
            query_manifest_path=missing,
            method="multi_similarity_with_miner",
            seed=7,
            condition="clean",
            query_definition="primary",
        )

    with pytest.raises(ValueError, match="reserved for Multi-Similarity"):
        evaluate_files(
            missing,
            missing,
            tmp_path / "result.json",
            mode="exploratory",
            protocol_path=protocol_path,
            gallery_manifest_path=missing,
            query_manifest_path=missing,
            method="contrastive",
            seed=7,
            condition="clean",
            query_definition="primary",
            stretch_run_manifest_path=missing,
            stretch_gate_evidence_path=missing,
        )
