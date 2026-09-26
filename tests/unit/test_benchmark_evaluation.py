from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.utils.data import TensorDataset

from pose_embed.benchmark import evaluation as evaluation
from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.retrieval import evaluate_retrieval
from pose_embed.data.manifest import ManifestRecord
from pose_embed.provenance import sha256_file


def _records():
    return [
        ManifestRecord(
            sample_id=f"S001C001P{performer:03}R001A{action:03}",
            split="novel_query_official",
        )
        for action in (1, 7)
        for performer in (1, 2)
    ]


def _result():
    rows = _records()
    vectors = np.array([[1.0, 0], [0.9, 0.1], [0, 1.0], [0.1, 0.9]])
    result = evaluate_retrieval(vectors, vectors, rows, rows, recall_k=(1, 2, 4, 8))
    return result, {"sample_ids": [r.sample_id for r in rows]}


@pytest.fixture
def final_fixture(tmp_path, monkeypatch):
    """Only authorization and licensed inputs are mocked; CPU inference is real."""
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    root = tmp_path / "benchmark-v2"
    locks = root / "locks"
    locks.mkdir(parents=True)
    for name in ("selection.json", "final-runs.json"):
        (locks / name).write_text("{}")
    config = load_benchmark()
    config = config.model_copy(
        update={
            "training": config.training.model_copy(update={"encoder_mode": "finetune"})
        }
    )
    monkeypatch.setattr(evaluation, "load_benchmark", lambda _: config)
    parity = tmp_path / "parity.json"
    parity.write_text("{}")
    bindings = {"verified_fixture_binding": "unit-test-only"}
    rows = _records()
    episode = {"sample_ids": [r.sample_id for r in rows]}
    opening = {
        "manifest_set_path": str(tmp_path / "manifest.json"),
        "novel_episode": episode,
    }
    events = []

    class TinyModel(torch.nn.Module):
        def __init__(self, encoder=None, *, embedding_dimension=512, **_):
            super().__init__()
            self.scale = torch.nn.Parameter(torch.ones(()))
            self.dimension = embedding_dimension

        def forward(self, poses):
            assert (locks / "test-opening.json").exists()
            events.append("forward")
            output = torch.zeros((len(poses), self.dimension))
            output[:, :2] = poses * self.scale
            return output

    run = root / "runs/contrastive-7"
    run.mkdir(parents=True)
    spec = load_methods()["contrastive"]
    identity = {
        "stage": "final",
        "track": "finetune",
        "scientific_use_allowed": True,
        "method": "contrastive",
        "seed": 7,
        "benchmark_sha256": benchmark_digest(config),
        "method_specification": spec.model_dump(mode="json"),
        "inputs": bindings,
        "parity_sha256": sha256_file(parity),
    }
    torch.save({"model": TinyModel().state_dict()}, run / "checkpoint.pt")
    (run / "run-manifest.json").write_text(json.dumps({"identity": identity}))
    reference = {
        "relative_path": str(run.relative_to(root)),
        "method": "contrastive",
        "seed": 7,
        "run_manifest_sha256": sha256_file(run / "run-manifest.json"),
        "checkpoint_sha256": sha256_file(run / "checkpoint.pt"),
    }
    final_runs = {"runs": [reference], "inputs": bindings}

    def validate_final(**_):
        events.append("validate-final")
        return final_runs

    def open_test(**_):
        events.append("open")
        (locks / "test-opening.json").write_text(json.dumps(opening))
        return opening

    inputs = SimpleNamespace(
        data_root=tmp_path,
        protocol=None,
        manifests={"official-novel.jsonl": rows},
        annotations=[{"frame_dir": row.sample_id} for row in rows],
    )
    monkeypatch.setattr(evaluation, "validate_final_runs", validate_final)
    monkeypatch.setattr(evaluation, "validate_opening", lambda **_: opening)
    monkeypatch.setattr(evaluation, "verify_run", lambda _: {"identity": identity})
    monkeypatch.setattr(evaluation, "code_digest", lambda: "code-fixture")
    monkeypatch.setattr(evaluation, "load_motionbert_inputs", lambda *_: inputs)
    monkeypatch.setattr(evaluation, "verify_motionbert_assets", lambda _: {})
    monkeypatch.setattr(evaluation, "build_motionbert_bindings", lambda *_: bindings)
    monkeypatch.setattr(evaluation, "validate_parity_report", lambda *_: None)
    monkeypatch.setattr(evaluation, "load_frozen_encoder", lambda *_: (None, None))
    monkeypatch.setattr(evaluation, "MotionRetrievalModel", TinyModel)
    monkeypatch.setattr(
        evaluation,
        "PoseDataset",
        lambda *_: TensorDataset(
            torch.tensor([[1.0, 0], [0.9, 0.1], [0, 1.0], [0.1, 0.9]]),
            torch.tensor([0, 0, 1, 1]),
        ),
    )
    monkeypatch.setattr(evaluation, "open_test", open_test)
    return SimpleNamespace(
        root=root,
        config=config,
        run=run,
        parity=parity,
        output=root / "evaluations/contrastive-7",
        opening=opening,
        final_runs=final_runs,
        events=events,
        identity=identity,
    )


def _evaluate(fixture):
    return evaluation.evaluate_final(
        fixture.run,
        "config.yaml",
        "manifest.json",
        fixture.parity,
        fixture.output,
        device="cpu",
    )


def test_final_authorization_precedes_any_source_loading(monkeypatch, tmp_path):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        evaluation,
        "load_motionbert_inputs",
        lambda *_: pytest.fail(
            "input loading must not precede full-roster authorization"
        ),
    )
    with pytest.raises(ValueError, match="fine-tuning|not implemented"):
        evaluation.evaluate_final(
            "unused", "configs/benchmark.v2.yaml", "unused", "unused", "unused"
        )


def test_fixture_forward_occurs_after_opening_and_result_is_immutable(final_fixture):
    f = final_fixture
    manifest = _evaluate(f)
    assert (
        f.events.index("validate-final")
        < f.events.index("open")
        < f.events.index("forward")
    )
    assert manifest["identity"]["embedding_dimension"] == 512
    key, metrics, rows = evaluation._read_evaluation(
        f.output, f.final_runs, f.opening, f.config
    )
    assert key == ("contrastive", 7)
    assert metrics["r_at_1"] == metrics["map"] == 1.0
    before = (f.output / "rank-metrics.json").read_bytes()
    with pytest.raises(FileExistsError, match="already exists"):
        _evaluate(f)
    assert (f.output / "rank-metrics.json").read_bytes() == before


def test_checkpoint_shape_mismatch_cannot_open_test(final_fixture):
    f = final_fixture
    torch.save({"model": {"unknown_parameter": torch.ones(1)}}, f.run / "checkpoint.pt")
    f.final_runs["runs"][0]["checkpoint_sha256"] = sha256_file(f.run / "checkpoint.pt")
    with pytest.raises(RuntimeError, match="state_dict"):
        _evaluate(f)
    assert "open" not in f.events and "forward" not in f.events


@pytest.mark.parametrize("corrupt_head", [False, True])
def test_proxy_evaluation_reconstructs_masked_head_before_opening(
    final_fixture, monkeypatch, corrupt_head
):
    from pose_embed.benchmark.model import MotionRetrievalModel

    f = final_fixture

    class Encoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(3, 4)

        def get_representation(self, poses):
            assert (f.root / "locks/test-opening.json").exists()
            return self.linear(poses)

    spec = load_methods()["proxy_nca_pp"]
    f.identity.update(
        method="proxy_nca_pp", method_specification=spec.model_dump(mode="json")
    )
    reference = f.final_runs["runs"][0]
    reference["method"] = "proxy_nca_pp"
    state = MotionRetrievalModel(
        Encoder(),
        method_id="proxy_nca_pp",
        representation_dimension=4,
        joints=2,
        embedding_dimension=512,
    ).state_dict()
    if corrupt_head:
        state["head.projection.weight"] = torch.ones(512, 8)
    torch.save({"model": state}, f.run / "checkpoint.pt")
    reference["checkpoint_sha256"] = sha256_file(f.run / "checkpoint.pt")
    (f.run / "run-manifest.json").write_text(json.dumps({"identity": f.identity}))
    reference["run_manifest_sha256"] = sha256_file(f.run / "run-manifest.json")
    monkeypatch.setattr(evaluation, "load_frozen_encoder", lambda *_: (Encoder(), {}))
    monkeypatch.setattr(
        evaluation,
        "MotionRetrievalModel",
        lambda encoder, **kwargs: MotionRetrievalModel(
            encoder, representation_dimension=4, joints=2, **kwargs
        ),
    )
    poses = torch.randn(4, 2, 3, 2, 3, generator=torch.Generator().manual_seed(17))
    poses[..., 2] = 1
    monkeypatch.setattr(
        evaluation,
        "PoseDataset",
        lambda *_: TensorDataset(poses, torch.tensor([0, 0, 1, 1])),
    )
    if corrupt_head:
        with pytest.raises(RuntimeError, match="size mismatch"):
            _evaluate(f)
        assert "open" not in f.events
    else:
        result = _evaluate(f)
        assert result["identity"]["run"]["method"] == "proxy_nca_pp"


def test_wrong_physical_bindings_cannot_open_test(final_fixture, monkeypatch):
    monkeypatch.setattr(
        evaluation, "build_motionbert_bindings", lambda *_: {"changed": True}
    )
    with pytest.raises(ValueError, match="physical input bindings"):
        _evaluate(final_fixture)
    assert "open" not in final_fixture.events


def test_failed_novel_forward_records_failure_without_success_manifest(
    final_fixture, monkeypatch
):
    def fail(*_):
        assert "open" in final_fixture.events
        raise ValueError("non-finite model output")

    monkeypatch.setattr(evaluation, "encode", fail)
    with pytest.raises(ValueError, match="non-finite"):
        _evaluate(final_fixture)
    outcome = json.loads((final_fixture.output / "outcome.json").read_text())
    assert outcome["status"] == "failed"
    assert not (final_fixture.output / "evaluation-manifest.json").exists()


def test_rehashed_forged_aggregate_is_rejected_against_per_query_ranks(final_fixture):
    f = final_fixture
    _evaluate(f)
    result_path = f.output / "rank-metrics.json"
    result = json.loads(result_path.read_text())
    result["metrics"]["map"] = 0.1
    result_path.write_text(json.dumps(result))
    manifest_path = f.output / "evaluation-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["outputs"]["rank-metrics.json"] = sha256_file(result_path)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="aggregate metrics"):
        evaluation._read_evaluation(f.output, f.final_runs, f.opening, f.config)


@pytest.mark.parametrize("change", ["rank", "exclusion", "identity", "count", "nan"])
def test_result_revalidates_ranks_and_candidate_eligibility(change):
    result, episode = _result()
    if change == "rank":
        result["per_query"][0]["relevant_ranks"] = [999]
    elif change == "exclusion":
        result["per_query"][0]["excluded_gallery_ids"] = []
    elif change == "identity":
        result["query_sample_ids"] = list(reversed(result["query_sample_ids"]))
    elif change == "count":
        result["per_query"][0]["relevant_count"] = 2
    else:
        result["per_query"][0]["average_precision"] = float("nan")
    with pytest.raises(ValueError):
        evaluation._validated_metrics(result, episode, (1, 2, 4, 8))


def _matrix(config):
    sample_ids = [
        f"S001C{camera:03}P{performer:03}R001A{action:03}"
        for action in range(1, 120, 6)
        for performer in (1, 2)
        for camera in (1, 2)
    ]
    matrix, per_query = {}, {}
    for method in config.final_methods:
        for index, seed in enumerate(config.training.seeds):
            hit = method in {"contextual", "proxy_anchor_avsl"}
            matrix[(method, seed)] = {
                "r_at_1": float(hit),
                "map": 0.2 + 0.03 * index,
                "query_count": len(sample_ids),
                "gallery_count": len(sample_ids),
            }
            per_query[(method, seed)] = [
                {"sample_id": sample_id, "recall_at_k": {"1": hit}}
                for sample_id in sample_ids
            ]
    return matrix, per_query, {"sample_ids": sample_ids}


def test_complete_report_preserves_paired_effects_and_dimension_groups():
    config = load_benchmark()
    summary = evaluation._summarize_matrix(*_matrix(config), config, load_methods())
    assert summary["required_runs"] == 156
    assert [
        (g["embedding_dimension"], len(g["methods"])) for g in summary["groups"]
    ] == [(512, 24), (1536, 2)]
    for group, expected in zip(summary["groups"], (1.0, -1.0), strict=True):
        comparison = group["paired_primary_comparisons"][0]
        assert comparison["mean_difference"] == expected
        assert comparison["raw_ci95"] == [expected, expected]
        assert comparison["simultaneous_ci95"] == [expected, expected]
        assert comparison["supports_positive_difference"] is (expected > 0)
    assert summary["uncertainty"]["multiplicity"]["family_size"] == 24
    assert "sample_id" not in json.dumps(summary)
    first = summary["groups"][0]["methods"][0]["metrics"]["map"]
    assert first["sample_std"] == pytest.approx(
        np.std([0.2 + 0.03 * i for i in range(6)], ddof=1)
    )


def test_report_rejects_missing_method_seed_and_nonfinite_metric():
    config = load_benchmark()
    matrix, rows, episode = _matrix(config)
    matrix.pop(("contextual", config.training.seeds[-1]))
    with pytest.raises(ValueError, match="all 26 methods"):
        evaluation._summarize_matrix(matrix, rows, episode, config, load_methods())
    matrix, rows, episode = _matrix(config)
    matrix[("contextual", config.training.seeds[0])]["map"] = float("nan")
    with pytest.raises(ValueError, match="finite proportions"):
        evaluation._summarize_matrix(matrix, rows, episode, config, load_methods())


def test_report_entrypoint_requires_complete_unique_matrix_and_writes_public_summary(
    final_fixture, monkeypatch
):
    f = final_fixture
    _evaluate(f)
    matrix, rows, episode = _matrix(f.config)
    f.opening["novel_episode"] = episode
    directories = []
    keyed = {}
    for (method, seed), metrics in matrix.items():
        directory = f.root / "report-fixtures" / f"{method}-{seed}"
        directory.mkdir(parents=True)
        (directory / "evaluation-manifest.json").write_text("{}")
        directories.append(directory)
        keyed[directory] = ((method, seed), metrics, rows[(method, seed)])
    monkeypatch.setattr(
        evaluation, "_read_evaluation", lambda directory, *_: keyed[directory]
    )
    with pytest.raises(ValueError, match="all 26 methods"):
        evaluation.report_final(directories[:-1], "config.yaml", f.root / "incomplete")
    assert not (f.root / "incomplete").exists()
    with pytest.raises(ValueError, match="duplicate"):
        evaluation.report_final(
            directories + directories[:1], "config.yaml", f.root / "duplicate"
        )
    summary = evaluation.report_final(directories, "config.yaml", f.root / "report")
    assert json.loads((f.root / "report/summary.json").read_text()) == summary
    assert not any(row.sample_id in json.dumps(summary) for row in _records())
    with pytest.raises(FileExistsError):
        evaluation.report_final(directories, "config.yaml", f.root / "report")


def test_matched_large_dimension_is_loaded_from_its_exact_registry_entry(final_fixture):
    f = final_fixture
    spec = load_methods()["contextual_1536"]
    f.identity.update(
        method="contextual_1536", method_specification=spec.model_dump(mode="json")
    )
    reference = f.final_runs["runs"][0]
    reference["method"] = "contextual_1536"
    (f.run / "run-manifest.json").write_text(json.dumps({"identity": f.identity}))
    reference["run_manifest_sha256"] = sha256_file(f.run / "run-manifest.json")
    manifest = _evaluate(f)
    assert manifest["identity"]["embedding_dimension"] == 1536
    key, metrics, _ = evaluation._read_evaluation(
        f.output, f.final_runs, f.opening, f.config
    )
    assert key == ("contextual_1536", 7)
    assert metrics["r_at_1"] == 1.0


def test_modified_evaluation_output_is_rejected_by_recorded_hash(final_fixture):
    f = final_fixture
    _evaluate(f)
    (f.output / "rank-metrics.json").write_text("{}")
    with pytest.raises(ValueError, match="output was changed"):
        evaluation._read_evaluation(f.output, f.final_runs, f.opening, f.config)
