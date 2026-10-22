"""Faults rebind temporary fixtures to test semantics beyond file hashes."""

from __future__ import annotations

import json

import numpy as np
import pytest
import torch

from pose_embed.evaluation.metrics import evaluate_one_shot
from pose_embed.provenance import sha256_file
from pose_embed.training.runner import (
    _embedding_health,
    train_head,
    validate_v3_training_run,
)
from tests.unit.test_training_v3 import _inputs


def _archive(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def _record_scores(run, epoch, record):
    gallery = _archive(run / f"epochs/{epoch:03d}/gallery.npz")
    query_path = run / f"epochs/{epoch:03d}/queries.npz"
    query = _archive(query_path)
    record["scores"] = evaluate_one_shot(
        torch.from_numpy(gallery["embeddings"]),
        torch.from_numpy(gallery["labels"]),
        torch.from_numpy(query["embeddings"]),
        torch.from_numpy(query["labels"]),
        query_ids=tuple(query["sample_ids"]),
    ).as_dict()
    record["projections"][str(query_path)] = sha256_file(query_path)
    record["health"] = _embedding_health(torch.from_numpy(query["embeddings"]))


def _resign_fixture(run, epoch, record, manifest=None):
    record_name = f"epoch-{epoch:03d}.json"
    (run / record_name).write_text(json.dumps(record))
    metrics_path, manifest_path, outcome_path = (
        run / name for name in ("metrics.json", "run-manifest.json", "outcome.json")
    )
    metrics = json.loads(metrics_path.read_text())
    metrics["epoch_records"][record_name] = sha256_file(run / record_name)
    metrics_path.write_text(json.dumps(metrics))
    manifest = manifest or json.loads(manifest_path.read_text())
    manifest["epoch_records"] = metrics["epoch_records"]
    manifest["outputs"]["metrics"] = sha256_file(metrics_path)
    manifest["outputs"]["pilot_artifacts"] = {
        name: sha256_file(run / name) for name in manifest["outputs"]["pilot_artifacts"]
    }
    manifest_path.write_text(json.dumps(manifest))
    outcome = json.loads(outcome_path.read_text())
    outcome["metrics_sha256"] = sha256_file(metrics_path)
    outcome["run_manifest_sha256"] = sha256_file(manifest_path)
    outcome_path.write_text(json.dumps(outcome))


@pytest.mark.parametrize(
    "stage,epoch", [("engineering_pilot", 5), ("development_selection", 20)]
)
def test_rebound_scores_from_another_projection_cannot_rank_candidates(
    tmp_path, protocol_path, stage, epoch
):
    run = tmp_path / "run"
    train_head(**{**_inputs(tmp_path, protocol_path), "stage": stage}, output_dir=run)
    validate_v3_training_run(run, stage=stage)
    checkpoint_hash = sha256_file(run / "head.pt")
    record = json.loads((run / f"epoch-{epoch:03d}.json").read_text())
    query_path = run / f"epochs/{epoch:03d}/queries.npz"
    query = _archive(query_path)
    query["embeddings"] = np.flip(query["embeddings"], axis=1).copy()
    np.savez(query_path, **query)
    _record_scores(run, epoch, record)
    _resign_fixture(run, epoch, record)
    with pytest.raises(
        ValueError, match="projections differ from bound checkpoint/cache"
    ):
        validate_v3_training_run(run, stage=stage)
    assert sha256_file(run / "head.pt") == checkpoint_hash


def test_fixed_model_parity_bounds_allow_small_arithmetic_differences(
    tmp_path, protocol_path
):
    run = tmp_path / "run"
    train_head(
        **{**_inputs(tmp_path, protocol_path), "stage": "development_selection"},
        output_dir=run,
    )
    path = run / "epochs/020/queries.npz"
    query = _archive(path)
    query["embeddings"] += np.float32(1e-7)
    np.savez(path, **query)
    record = json.loads((run / "epoch-020.json").read_text())
    _record_scores(run, 20, record)
    _resign_fixture(run, 20, record)
    validate_v3_training_run(run, stage="development_selection")


def test_rebound_invalid_base_cache_is_revalidated(tmp_path, protocol_path):
    run = tmp_path / "run"
    inputs = _inputs(tmp_path, protocol_path)
    train_head(**{**inputs, "stage": "development_selection"}, output_dir=run)
    source = inputs["development_query_path"]
    arrays = _archive(source)
    arrays["features"][0, 0] = np.nan
    np.savez(source, **arrays)
    sidecar_path = source.with_suffix(".npz.manifest.json")
    sidecar = json.loads(sidecar_path.read_text())
    sidecar["artifact_sha256"] = sha256_file(source)
    sidecar_path.write_text(json.dumps(sidecar))
    record = json.loads((run / "epoch-020.json").read_text())
    manifest = json.loads((run / "run-manifest.json").read_text())
    for path in (source, sidecar_path):
        for bindings in (
            record["development_inputs"],
            manifest["development_inputs"],
            manifest["inputs"],
        ):
            bindings[str(path)] = sha256_file(path)
    _resign_fixture(run, 20, record, manifest)
    with pytest.raises(ValueError, match="only finite values"):
        validate_v3_training_run(run, stage="development_selection")


def test_snapshot_checkpoint_stage_must_match_its_scoring_record(
    tmp_path, protocol_path
):
    run = tmp_path / "run"
    train_head(**_inputs(tmp_path, protocol_path), output_dir=run)
    checkpoint_path = run / "epochs/005/head.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    checkpoint["stage"] = "development_selection"
    torch.save(checkpoint, checkpoint_path)
    record = json.loads((run / "epoch-005.json").read_text())
    record["checkpoint_sha256"] = sha256_file(checkpoint_path)
    _resign_fixture(run, 5, record)
    with pytest.raises(ValueError, match="wrong stage or epoch"):
        validate_v3_training_run(run, stage="engineering_pilot")
