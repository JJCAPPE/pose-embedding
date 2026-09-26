import copy
import json
import random
import signal
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from pose_embed.benchmark import runner, runtime, segments

pytest_plugins = ["test_benchmark_runner"]


def configure(experiment, *, steps=8):
    path = experiment["config_path"]
    document = yaml.safe_load(path.read_text())
    document["training"].update(
        steps=steps, validation_every=2, encoder_mode="finetune"
    )
    path.write_text(yaml.safe_dump(document))


def checkpoint(path):
    return torch.load(path, map_location="cpu", weights_only=True)


@pytest.mark.parametrize(
    "experiment,method",
    [
        (None, method)
        for method in ("contrastive", "proxy_nca_pp", "multi_similarity_metrix", "s2sd")
    ]
    + [("diva", "diva")],
    indirect=["experiment"],
)
def test_segmented_continuation_is_exact_across_dropout_warmup_and_validation(
    experiment, tmp_path, method, monkeypatch
):
    configure(experiment)
    if method == "diva":
        methods = runner.load_methods()
        methods[method] = methods[method].model_copy(
            update={
                "embedding_dimension": 16,
                "parameters": methods[method].parameters
                | {
                    "feature_dimension": 8,
                    "physical_batch_size": 12,
                    "queue_batches": 2,
                    "decorrelation_hidden": 8,
                },
            }
        )
        monkeypatch.setattr(runner, "load_methods", lambda *args: methods)
        monkeypatch.setattr(runtime, "load_methods", lambda *args: methods)
    if method == "s2sd":
        methods = runner.load_methods()
        original = methods[method]
        methods[method] = original.model_copy(
            update={
                "embedding_dimension": 8,
                "parameters": original.parameters
                | {
                    "embedding_dimension": 8,
                    "feature_dimension": 8,
                    "target_dimensions": [8, 12, 16, 20],
                    "feature_delay": 4,
                },
            }
        )
        monkeypatch.setattr(runner, "load_methods", lambda: methods)
        monkeypatch.setattr(runtime, "load_methods", lambda: methods)
    uninterrupted = tmp_path / "benchmark-v2/full"
    split = tmp_path / "benchmark-v2/split"
    runner.run_experiment(**experiment, method=method, output_dir=uninterrupted)
    receipt = runner.run_experiment(
        **experiment, method=method, output_dir=split, segment_steps=3
    )
    assert receipt["status"] == "resumable" and not receipt["scientific_use_allowed"]
    assert receipt["completed_steps"] == 3
    assert (
        not (split / "outcome.json").exists()
        and not (split / "run-manifest.json").exists()
    )
    assert "--resume-from" in receipt["next_resume_command"]
    parent_file = receipt["segment_manifest"]
    first_hash = runtime.sha256_file(parent_file)
    random.seed(987)
    np.random.seed(456)
    torch.manual_seed(123)
    receipt = runner.run_experiment(
        **experiment,
        method=method,
        output_dir=split,
        segment_steps=2,
        resume_from=parent_file,
    )
    assert receipt["completed_steps"] == 5
    runner.run_experiment(
        **experiment,
        method=method,
        output_dir=split,
        resume_from=receipt["segment_manifest"],
    )
    assert runtime.sha256_file(parent_file) == first_hash
    runtime.verify_run(split)
    expected, actual = (
        checkpoint(uninterrupted / "checkpoint.pt"),
        checkpoint(split / "checkpoint.pt"),
    )
    assert segments._equal_state(expected, actual)
    if method == "s2sd":
        assert actual["criterion"]["completed_steps"].item() == actual["selected_step"]
    history = runtime.read_json(split / "history.json")
    expected_history = runtime.read_json(uninterrupted / "history.json")
    for first, second in zip(history["steps"], expected_history["steps"], strict=True):
        assert {
            key: value
            for key, value in first.items()
            if key not in {"seconds", "retrieval_timing"}
        } == {
            key: value
            for key, value in second.items()
            if key not in {"seconds", "retrieval_timing"}
        }
    assert history["selected_step"] == expected_history["selected_step"]
    assert runtime.read_json(split / "telemetry.json")["segment_artifact_bytes"] > 0
    chain = runtime.read_json(split / "segments.json")
    assert len(chain["chain"]) == 3


def test_rng_roundtrip_preserves_python_numpy_torch_and_gaussian_cache():
    random.seed(13)
    np.random.seed(21)
    torch.manual_seed(34)
    random.gauss(0, 1)
    np.random.normal()
    saved = segments.capture_rng()
    expected = (
        random.random(),
        random.gauss(0, 1),
        np.random.random(),
        np.random.normal(),
        torch.rand(4),
    )
    segments.restore_rng(saved)
    actual = (
        random.random(),
        random.gauss(0, 1),
        np.random.random(),
        np.random.normal(),
        torch.rand(4),
    )
    assert expected[:4] == actual[:4]
    assert torch.equal(expected[4], actual[4])
    bad = copy.deepcopy(saved)
    bad["runtime"]["torch"] = "different"
    with pytest.raises(ValueError, match="runtime"):
        segments.restore_rng(bad)


def test_safe_signal_waits_for_complete_update_and_restores_handler(
    experiment, tmp_path, monkeypatch
):
    configure(experiment, steps=4)
    original = runner.optimizer_step
    prior = signal.getsignal(signal.SIGTERM)
    calls = []

    def request_after_step(*args, **kwargs):
        value = original(*args, **kwargs)
        calls.append(1)
        signal.raise_signal(signal.SIGTERM)
        return value

    monkeypatch.setattr(runner, "optimizer_step", request_after_step)
    path = tmp_path / "benchmark-v2/signal"
    receipt = runner.run_experiment(
        **experiment, method="contrastive", output_dir=path, segment_steps=3
    )
    assert calls == [1] and receipt["completed_steps"] == 1
    assert signal.getsignal(signal.SIGTERM) == prior
    manifest = runtime.read_json(receipt["segment_manifest"])
    assert manifest["reason"] == "signal:SIGTERM"
    saved = checkpoint(path / "segments/000001/checkpoint.pt")
    assert saved["step"] == 1 and saved["training_state"]["step"] == 1


@pytest.mark.parametrize("what", ["checkpoint", "history", "parent", "batch"])
def test_tampered_parent_chain_rejected_before_loading_model(
    experiment, tmp_path, monkeypatch, what
):
    configure(experiment, steps=6)
    root = tmp_path / "benchmark-v2/tamper"
    first = runner.run_experiment(
        **experiment, method="contrastive", output_dir=root, segment_steps=2
    )
    second = runner.run_experiment(
        **experiment,
        method="contrastive",
        output_dir=root,
        segment_steps=2,
        resume_from=first["segment_manifest"],
    )
    if what == "checkpoint":
        (root / "segments/000001/checkpoint.pt").write_bytes(b"changed")
    elif what == "history":
        (root / "segments/000001/history.json").write_text("{}")
    elif what == "parent":
        manifest = runtime.read_json(first["segment_manifest"])
        manifest["reason"] = "changed"
        Path(first["segment_manifest"]).write_text(json.dumps(manifest))
    else:
        (root / "batch-plan.json").write_text("{}")
    monkeypatch.setattr(
        runner,
        "load_frozen_encoder",
        lambda *_: pytest.fail("must reject before model load"),
    )
    with pytest.raises(ValueError, match="changed"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            output_dir=root,
            resume_from=second["segment_manifest"],
        )


def test_completed_verifier_rejects_missing_ancestor_and_stale_resume(
    experiment, tmp_path
):
    configure(experiment, steps=4)
    root = tmp_path / "benchmark-v2/chain"
    first = runner.run_experiment(
        **experiment, method="contrastive", output_dir=root, segment_steps=1
    )
    second = runner.run_experiment(
        **experiment,
        method="contrastive",
        output_dir=root,
        segment_steps=1,
        resume_from=first["segment_manifest"],
    )
    with pytest.raises(ValueError, match="latest"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            output_dir=root,
            resume_from=first["segment_manifest"],
        )
    runner.run_experiment(
        **experiment,
        method="contrastive",
        output_dir=root,
        resume_from=second["segment_manifest"],
    )
    runtime.verify_run(root)
    (root / "segments/000001/checkpoint.pt").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        runtime.verify_run(root)


def test_failed_segment_is_preserved_and_retry_appends(
    experiment, tmp_path, monkeypatch
):
    configure(experiment, steps=4)
    root = tmp_path / "benchmark-v2/retry"
    first = runner.run_experiment(
        **experiment, method="contrastive", output_dir=root, segment_steps=2
    )
    original = runner.optimizer_step

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic transient failure")

    monkeypatch.setattr(runner, "optimizer_step", fail)
    with pytest.raises(RuntimeError, match="transient"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            output_dir=root,
            resume_from=first["segment_manifest"],
        )
    failure = root / "segments/000002/outcome.json"
    assert runtime.read_json(failure)["status"] == "failed"
    assert runtime.read_json(failure)["elapsed_seconds"] >= 0
    failure_hash = runtime.sha256_file(failure)
    monkeypatch.setattr(runner, "optimizer_step", original)
    runner.run_experiment(
        **experiment,
        method="contrastive",
        output_dir=root,
        resume_from=first["segment_manifest"],
    )
    assert runtime.sha256_file(failure) == failure_hash
    assert (root / "segments/000003/segment-manifest.json").exists()
    runtime.verify_run(root)


def test_profiles_and_different_identity_cannot_resume(
    experiment, tmp_path, monkeypatch
):
    root = tmp_path / "benchmark-v2/identity"
    with pytest.raises(ValueError, match="profiles"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            output_dir=root,
            profile_steps=1,
            segment_steps=1,
        )
    first = runner.run_experiment(
        **experiment, method="contrastive", output_dir=root, segment_steps=1
    )
    monkeypatch.setattr(runner, "code_digest", lambda: "0" * 64)
    with pytest.raises(ValueError, match="identical"):
        runner.run_experiment(
            **experiment,
            method="contrastive",
            output_dir=root,
            resume_from=first["segment_manifest"],
        )


def test_wall_time_limit_seals_after_one_complete_update(experiment, tmp_path):
    configure(experiment, steps=4)
    root = tmp_path / "benchmark-v2/soft-time"
    receipt = runner.run_experiment(
        **experiment,
        method="contrastive",
        output_dir=root,
        max_segment_seconds=1e-9,
    )
    assert receipt["status"] == "resumable" and receipt["completed_steps"] == 1
    assert "--max-segment-seconds 1e-09" in receipt["next_resume_command"]


def test_numeric_environment_must_match_but_node_identity_can_change():
    prior = {"hostname": "node1", "device_index": 0, "gpu": "A100", "torch": "2.9"}
    segments.verify_environment(prior, prior | {"hostname": "node2", "device_index": 1})
    with pytest.raises(ValueError, match="numeric environment"):
        segments.verify_environment(prior, prior | {"gpu": "H100"})


def test_secondary_chain_binds_data_plan_and_selects_fixed_final_step(tmp_path):
    root = tmp_path / "secondary"
    root.mkdir()
    identity = {
        "stage": "development",
        "steps": 4,
        "secondary": {"cell_id": "synthetic-cell"},
        "configuration": {"training": {"validation_every": 2}},
        "training_recipe": {
            "warmup_steps": 0,
            "profile_phase": None,
            "minimum_selected_step": 1,
        },
    }
    batches = [[0, 1]] * 4
    runtime.write_immutable_json(root / "attempt.json", {"identity": identity})
    runtime.write_immutable_json(root / "batch-plan.json", {"steps": batches})
    runtime.write_immutable_json(root / "secondary-data-plan.json", {"labels": [0, 1]})
    rows = []
    parent = None
    for end in (2, 4):
        rows.extend(
            {"step": step, "loss": 1.0, "phase": "main"}
            | ({"validation": {"r_at_1": 1 / end}} if step == end else {})
            for step in range(end - 1, end + 1)
        )
        leaf = segments.begin_segment(root, identity, parent)
        segments.seal_segment(
            root,
            leaf,
            identity,
            parent,
            {"step": end},
            {"model": {}} if end == 4 else None,
            None,
            4,
            0.25,
            rows,
            batches,
            1.0,
            {},
            0,
            0,
            "test",
        )
        parent = segments.verify_chain(root, leaf, identity, completed=end == 4)
    assert parent["manifest"]["best"]["selected_step"] == 4
    assert "secondary-data-plan.json" in parent["manifest"]["shared"]
    (root / "secondary-data-plan.json").write_text("{}")
    with pytest.raises(ValueError, match="shared evidence"):
        segments.verify_chain(root, parent["path"], identity)
