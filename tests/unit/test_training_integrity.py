from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from pose_embed.config import load_protocol
from pose_embed.data import ManifestRecord
from pose_embed.features import extract_fixture_features
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file
from pose_embed.training import train_head


def _write_experiment(path: Path) -> None:
    path.write_text(
        """schema_version: 1
name: integrity-fixture
objective: contrastive
seed: 7
input_dimension: 6
embedding_dimension: 4
epochs: 2
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


def _write_training_features(
    tmp_path: Path,
    protocol_path: Path,
) -> tuple[Path, Path]:
    sample_ids = [f"S{index + 1:03d}C001P001R001A003" for index in range(4)] + [
        f"S{index + 1:03d}C001P002R001A004" for index in range(4)
    ]
    poses = tmp_path / "poses.npz"
    manifest = tmp_path / "train.jsonl"
    features = tmp_path / "features.npz"
    np.savez(
        poses,
        poses=np.ones((8, 1, 6, 17, 3), dtype=np.float32),
        labels=np.asarray([3] * 4 + [4] * 4),
        sample_ids=np.asarray(sample_ids),
    )
    manifest.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id, split="development_train"
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )
    extract_fixture_features(
        poses,
        features,
        protocol_path=protocol_path,
        manifest_path=manifest,
        role="training",
        split="development_train",
        embedding_dimension=6,
    )
    return features, manifest


def test_training_requires_trusted_sidecar_and_records_paired_controls(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    features, manifest = _write_training_features(tmp_path, protocol_path)
    config = tmp_path / "experiment.yaml"
    _write_experiment(config)

    with pytest.raises(ValueError, match="scientific use"):
        train_head(
            config,
            features,
            tmp_path / "blocked-run",
            protocol_path=protocol_path,
            manifest_path=manifest,
        )

    summary = train_head(
        config,
        features,
        tmp_path / "fixture-run",
        protocol_path=protocol_path,
        manifest_path=manifest,
        allow_fixture=True,
    )
    run_dir = tmp_path / "fixture-run"
    batch_plan = json.loads((run_dir / "batch-plan.json").read_text(encoding="utf-8"))
    run_manifest = json.loads(
        (run_dir / "run-manifest.json").read_text(encoding="utf-8")
    )
    attempt = json.loads((run_dir / "attempt.json").read_text(encoding="utf-8"))
    outcome = json.loads((run_dir / "outcome.json").read_text(encoding="utf-8"))

    assert len(summary["initialization_sha256"]) == 64
    assert len(summary["batch_plan_sha256"]) == 64
    assert len(summary["epoch_batch_plan_sha256"]) == 2
    assert len(batch_plan["epochs"]) == 2
    assert run_manifest["outputs"]["batch_plan"] == summary["batch_plan_sha256"]
    assert run_manifest["scientific_use_allowed"] is False
    assert summary["telemetry"] == run_manifest["telemetry"]
    assert summary["telemetry"]["wall_time_seconds"] > 0
    assert summary["telemetry"]["peak_memory_bytes"] >= 0
    assert attempt["attempt_id"] == outcome["attempt_id"]
    assert attempt["status"] == "started"
    assert outcome["status"] == "success"
    assert outcome["run_manifest_sha256"]


def test_training_rejects_novel_query_role(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    sample_ids = [
        "S001C001P001R001A001",
        "S002C001P002R001A001",
        "S001C001P003R001A007",
        "S002C001P004R001A007",
    ]
    poses = tmp_path / "novel.npz"
    manifest = tmp_path / "novel.jsonl"
    features = tmp_path / "novel-features.npz"
    config = tmp_path / "experiment.yaml"
    _write_experiment(config)
    np.savez(
        poses,
        poses=np.ones((4, 1, 6, 17, 3), dtype=np.float32),
        labels=np.asarray([1, 1, 7, 7]),
        sample_ids=np.asarray(sample_ids),
    )
    manifest.write_text(
        "\n".join(
            ManifestRecord(
                sample_id=sample_id, split="novel_query_primary"
            ).model_dump_json()
            for sample_id in sample_ids
        )
        + "\n",
        encoding="utf-8",
    )
    extract_fixture_features(
        poses,
        features,
        protocol_path=protocol_path,
        manifest_path=manifest,
        role="query_clean",
        split="novel_query_primary",
        embedding_dimension=6,
    )

    with pytest.raises(ValueError, match="training role"):
        train_head(
            config,
            features,
            tmp_path / "run",
            protocol_path=protocol_path,
            manifest_path=manifest,
            allow_fixture=True,
        )


def test_multi_similarity_training_requires_completed_core_gate_evidence(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    features, manifest = _write_training_features(tmp_path, protocol_path)
    config = tmp_path / "multi-similarity.yaml"
    config.write_text(
        """schema_version: 1
name: debug-stretch
objective: multi_similarity_with_miner
seed: 7
input_dimension: 6
embedding_dimension: 4
epochs: 1
learning_rate: 0.01
weight_decay: 0.0
classes_per_batch: 2
samples_per_class: 2
temperature: 0.07
positive_margin: 0.9
negative_margin: 0.6
multi_similarity:
  library: pytorch-metric-learning
  library_version: 2.9.0
  loss_alpha: 2.0
  loss_beta: 50.0
  loss_base: 0.5
  miner_epsilon: 0.1
  distance: cosine_similarity
  normalize_embeddings: true
  distance_p: 2
  distance_power: 1
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="four stretch-gate"):
        train_head(
            config,
            features,
            tmp_path / "run",
            protocol_path=protocol_path,
            manifest_path=manifest,
            allow_fixture=True,
        )

    gate_names = (
        "nine_core_checkpoints_verified",
        "full_core_result_matrix_verified",
        "core_figures_reproducible",
        "no_unresolved_core_failures",
    )
    gates = {}
    for gate_name in gate_names:
        evidence_file = tmp_path / f"{gate_name}.json"
        evidence_file.write_text("{}\n", encoding="utf-8")
        gates[gate_name] = {
            "status": "met",
            "evidence_path": evidence_file.name,
            "evidence_sha256": sha256_file(evidence_file),
        }
    protocol = load_protocol(protocol_path)
    gate_evidence = tmp_path / "stretch-gates.json"
    gate_evidence.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_sha256": protocol_digest(protocol),
                "evaluation_plan_sha256": "a" * 64,
                "final_run_set_sha256": "b" * 64,
                "test_opening_ledger_sha256": "c" * 64,
                "recorded_at": datetime.now(UTC).isoformat(),
                "gates": gates,
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "locks/test-opening.v1.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))

    summary = train_head(
        config,
        features,
        tmp_path / "stretch-run",
        protocol_path=protocol_path,
        manifest_path=manifest,
        allow_fixture=True,
        stretch_gate_evidence_path=gate_evidence,
    )
    assert summary["objective"] == "multi_similarity_with_miner"


def test_training_stops_after_test_opening(
    protocol_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    features, manifest = _write_training_features(tmp_path, protocol_path)
    config = tmp_path / "experiment.yaml"
    ledger = tmp_path / "locks/test-opening.v1.json"
    _write_experiment(config)
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))

    with pytest.raises(ValueError, match="forbidden after"):
        train_head(
            config,
            features,
            tmp_path / "run",
            protocol_path=protocol_path,
            manifest_path=manifest,
            allow_fixture=True,
        )


def test_training_failure_preserves_attempt_and_outcome(
    protocol_path: Path,
    tmp_path: Path,
) -> None:
    features, manifest = _write_training_features(tmp_path, protocol_path)
    config = tmp_path / "experiment.yaml"
    run_dir = tmp_path / "failed-run"
    _write_experiment(config)

    with pytest.raises((RuntimeError, AssertionError)):
        train_head(
            config,
            features,
            run_dir,
            protocol_path=protocol_path,
            manifest_path=manifest,
            allow_fixture=True,
            device="cuda:999999",
        )

    attempt = json.loads((run_dir / "attempt.json").read_text(encoding="utf-8"))
    outcome = json.loads((run_dir / "outcome.json").read_text(encoding="utf-8"))
    assert attempt["status"] == "started"
    assert outcome["status"] == "failed"
    assert outcome["attempt_id"] == attempt["attempt_id"]
    assert outcome["error_type"]
