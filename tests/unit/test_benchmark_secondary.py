import copy
import json

import numpy as np
import pytest
import torch

from pose_embed.benchmark import secondary
from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.secondary_evaluation import (
    _one_shot_validated_metrics,
    expected_result_keys,
    one_shot_metrics,
)
from pose_embed.data.manifest import ManifestRecord


def records(stage="development", classes=80, samples=16):
    return [
        ManifestRecord(
            sample_id=f"S001C001P{person:03d}R001A{action:03d}", split=f"{stage}_train"
        )
        for action in range(1, classes + 1)
        for person in range(1, samples + 1)
    ]


def cell(family="clean", amount=0):
    return secondary.training_cells()[f"robustness-context_only-{family}-{amount:g}"]


def test_finite_matrix_and_no_double_counting_clean_controls():
    plan = secondary.load_secondary_plan(load_benchmark())
    assert plan["classification"] == "secondary_descriptive"
    assert len(secondary.training_cells()) == 46
    forecast = secondary.forecast()
    assert forecast["all_required_final_runs_before_opening"] == 432
    assert forecast["secondary_total_training_runs"] == 552
    assert len(expected_result_keys(load_benchmark())) == 660


def test_plan_rejects_modified_scientific_settings(tmp_path, monkeypatch):
    document = secondary.specification()
    document["robustness"]["label_noise"] = [0.3]
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(document))
    monkeypatch.setattr(secondary, "PLAN_PATH", path)
    with pytest.raises(ValueError, match="predeclared"):
        secondary.load_secondary_plan()


@pytest.mark.parametrize("family", ["label_noise", "pose_replacement"])
def test_training_interventions_are_paired_nested_and_never_use_other_partitions(
    family,
):
    source = records()
    before = torch.get_rng_state().clone()
    low = secondary.training_data_plan(
        source, stage="development", seed=7, cell=cell(family, 0.05)
    )
    high = secondary.training_data_plan(
        source, stage="development", seed=7, cell=cell(family, 0.2)
    )
    assert low == secondary.training_data_plan(
        source, stage="development", seed=7, cell=cell(family, 0.05)
    )
    assert torch.equal(torch.get_rng_state(), before)
    assert len(low["changed_indices"]) == int(len(source) * 0.05)
    assert set(low["changed_indices"]) <= set(high["changed_indices"])
    lookup = {r.sample_id: r for r in source}
    for index in low["changed_indices"]:
        if family == "label_noise":
            assert low["observed_actions"][index] != low["true_actions"][index]
            assert low["observed_actions"][index] == high["observed_actions"][index]
            assert low["source_sample_ids"][index] == source[index].sample_id
        else:
            replacement = lookup[low["source_sample_ids"][index]]
            assert replacement.ntu.action != source[index].ntu.action
            assert replacement.ntu.performance_id != source[index].ntu.performance_id
            assert low["observed_actions"] == low["true_actions"]
            assert low["source_sample_ids"][index] == high["source_sample_ids"][index]
    with pytest.raises(ValueError, match="current training partition"):
        secondary.training_data_plan(
            [r.model_copy(update={"split": "development_validation"}) for r in source],
            stage="development",
            seed=7,
            cell=cell(family, 0.05),
        )


@pytest.mark.parametrize("stage,classes", [("development", 80), ("final", 100)])
def test_low_data_keeps_nested_action_subsets_without_validation_changes(
    stage, classes
):
    source = records(stage, classes)
    subsets = []
    for fraction in (0.25, 0.5, 0.75):
        plan = secondary.training_data_plan(
            source, stage=stage, seed=17, cell=cell("retained_actions", fraction)
        )
        assert len(plan["retained_actions"]) == int(classes * fraction)
        assert plan["source_sample_ids"] == plan["sample_ids"]
        subsets.append(set(plan["retained_actions"]))
    assert subsets[0] < subsets[1] < subsets[2]


def test_dataset_replacement_changes_input_only_and_keeps_source_dictionary_private():
    from types import SimpleNamespace

    source = records()
    plan = secondary.training_data_plan(
        source, stage="development", seed=7, cell=cell("pose_replacement", 0.1)
    )
    annotations = {r.sample_id: {"source": r.sample_id} for r in source}
    original = copy.deepcopy(annotations)
    dataset = SimpleNamespace(annotations=annotations, labels=[], label_mapping={})
    secondary.bind_dataset(dataset, plan)
    assert annotations == original
    for index in plan["changed_indices"]:
        assert (
            dataset.annotations[plan["sample_ids"][index]]["source"]
            == plan["source_sample_ids"][index]
        )
    assert dataset.labels == plan["labels"]


def test_one_shot_cosine_and_custom_scoring_keep_official_views_and_map_equals_mrr():
    anchors = [
        ManifestRecord(
            sample_id=f"S001C001P001R001A{action:03d}",
            split="novel_anchor",
            is_anchor=True,
        )
        for action in (1, 2)
    ]
    queries = [
        ManifestRecord(
            sample_id=f"S001C002P001R001A{action:03d}", split="novel_query_official"
        )
        for action in (1, 2)
    ]
    query = {"embeddings": np.array([[1.0, 0.0], [1.0, 0.0]])}
    gallery = {"embeddings": np.eye(2)}
    cosine = one_shot_metrics(query, gallery, queries, anchors)
    assert cosine["top1"] == 0.5 and cosine["map"] == cosine["mrr"] == 0.75
    observed = []

    def scorer(q, g, excluded):
        observed.append(excluded)
        return np.ones((len(q), len(g)))

    custom = one_shot_metrics(query, gallery, queries, anchors, scorer)
    assert observed == [[[], []]]
    assert [row["rank"] for row in custom["per_query"]] == [1, 2]
    identity = {
        "query_sample_ids": [r.sample_id for r in queries],
        "gallery_sample_ids": [r.sample_id for r in anchors],
    }
    assert _one_shot_validated_metrics(custom, identity)["map"] == 0.75
    custom["map"] = 0.9
    with pytest.raises(ValueError, match="per-query ranks"):
        _one_shot_validated_metrics(custom, identity)


def test_incomplete_secondary_matrix_rejected_and_opening_cannot_bypass_it(
    tmp_path, monkeypatch
):
    from pose_embed.benchmark import locks

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    plan = {
        "cells": secondary.training_cells(),
        "seeds": [7, 17, 29, 43, 59, 71],
        "created_at": "2026-09-24T00:00:00+00:00",
    }
    monkeypatch.setattr(secondary, "validate_secondary_plan", lambda **kwargs: plan)
    with pytest.raises(ValueError, match="all 46 cells"):
        secondary._runs_content([], config_path="ignored", stage="final")
    monkeypatch.setattr(locks, "validate_final_runs", lambda **kwargs: {})
    monkeypatch.setattr(
        locks,
        "load_episode",
        lambda *args: pytest.fail(
            "novel metadata must follow secondary training authorization"
        ),
    )
    with pytest.raises(FileNotFoundError):
        locks.open_test(manifest_set_path="unused", config_path="unused")


def test_secondary_lock_refuses_any_work_after_test_opening(tmp_path, monkeypatch):
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    root = tmp_path / "benchmark-v2/locks"
    root.mkdir(parents=True)
    (root / "test-opening.json").write_text("{}")
    with pytest.raises(ValueError, match="after test opening"):
        secondary.lock_secondary_plan(config_path="unused")


def test_matrix_scope_validates_main_selection_once_and_rechecks_changed_evidence(
    tmp_path, monkeypatch
):
    from pose_embed.benchmark import locks
    from pose_embed.benchmark.config import REPOSITORY_ROOT, load_methods
    from pose_embed.provenance import sha256_file

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    lock = tmp_path / "benchmark-v2/locks"
    lock.mkdir(parents=True)
    selection_path = lock / "selection.json"
    selection_path.write_text("{}")
    config_path = REPOSITORY_ROOT / "configs/benchmark.finetune.v2.yaml"
    config = load_benchmark(config_path)
    method = load_methods()["contrastive"]
    cell_id = "robustness-contrastive-clean-0"
    plan = {
        "main_configuration_path": str(config_path),
        "secondary_plan_sha256": secondary.secondary_plan_sha256(),
        "created_at": "2026-09-24T01:00:00+00:00",
        "seeds": [7],
        "cells": {
            cell_id: {
                "configuration": config.model_dump(mode="json"),
                "method_specification": method.model_dump(mode="json"),
                "selected_steps": 2,
            }
        },
    }
    (lock / "secondary-plan.json").write_text(json.dumps(plan))
    calls = []

    def validate_selection(**kwargs):
        calls.append(kwargs)
        return {"created_at": "2026-09-24T00:00:00+00:00"}

    monkeypatch.setattr(locks, "validate_selection", validate_selection)
    monkeypatch.setattr(
        secondary,
        "_lock_content",
        lambda *args: {
            key: value for key, value in plan.items() if key != "created_at"
        },
    )
    identity = {
        "configuration": config.model_dump(mode="json"),
        "method_specification": method.model_dump(mode="json"),
        "method": "contrastive",
        "seed": 7,
        "stage": "development",
        "track": "finetune",
        "steps": 2,
        "scientific_use_allowed": True,
        "selection_sha256": sha256_file(selection_path),
        "secondary": {
            "classification": "secondary_descriptive",
            "cell_id": cell_id,
            "secondary_plan_sha256": plan["secondary_plan_sha256"],
            "secondary_lock_sha256": sha256_file(lock / "secondary-plan.json"),
            "main_configuration_path": str(config_path),
            "data_plan_sha256": "0" * 64,
        },
    }
    with secondary.secondary_validation_scope():
        secondary.validate_secondary_plan(config_path=config_path)
        # verify_run has three real binding routes per run: identity, source rows,
        # and the regenerated intervention plan. Exercise their actual resolver.
        for _ in range(276 * 3):
            secondary.validate_run_binding(identity)
        assert len(calls) == 1
        selection_path.write_text('{"modified":true}')
        with pytest.raises(ValueError, match="changed during validation"):
            secondary.validate_run_binding(identity)
        selection_path.write_text("{}")
    # A new command must revalidate the full parent evidence; no process cache.
    with secondary.secondary_validation_scope():
        secondary.validate_run_binding(identity)
    assert len(calls) == 2


def test_complete_secondary_lock_revalidates_every_reference_and_pair(
    tmp_path, monkeypatch
):
    from pose_embed.benchmark import runtime
    from pose_embed.provenance import sha256_file

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    root = tmp_path / "benchmark-v2"
    lock = root / "locks"
    lock.mkdir(parents=True)
    for name in ("selection.json", "secondary-plan.json"):
        (lock / name).write_text("{}")
    plan = {
        "cells": secondary.training_cells(),
        "seeds": [7, 17, 29, 43, 59, 71],
        "created_at": "2026-09-24T00:00:00+00:00",
        "inputs": {"fixture": "metadata"},
    }
    monkeypatch.setattr(secondary, "validate_secondary_plan", lambda **kwargs: plan)
    monkeypatch.setattr(
        runtime,
        "verify_run",
        lambda path: runtime.read_json(path / "run-manifest.json"),
    )
    paths = []
    for key, cell in plan["cells"].items():
        for seed in plan["seeds"]:
            directory = root / "runs" / key / str(seed)
            directory.mkdir(parents=True)
            identity = {
                "method": cell["method"],
                "stage": "development",
                "seed": seed,
                "inputs": plan["inputs"],
                "secondary": {
                    "cell_id": key,
                    "data_plan_sha256": runtime.digest(
                        [cell["intervention"], cell["amount"], seed]
                    ),
                },
            }
            (directory / "attempt.json").write_text(
                json.dumps({"started_at": "2026-09-24T01:00:00+00:00"})
            )
            (directory / "initialization.json").write_text(
                json.dumps({"encoder": str(seed), "head": str(seed)})
            )
            (directory / "batch-plan.json").write_text(
                json.dumps({"sample_ids": ["fixture"], "steps": [[0]]})
            )
            (directory / "checkpoint.pt").write_bytes(b"fixture-only-checkpoint")
            (directory / "run-manifest.json").write_text(
                json.dumps(
                    {"identity": identity, "completed_at": "2026-09-24T02:00:00+00:00"}
                )
            )
            paths.append(directory)
    result = secondary.lock_secondary_runs(
        paths, config_path="fixture", stage="development"
    )
    assert len(result["runs"]) == 276
    assert (
        secondary.validate_secondary_runs(config_path="fixture", stage="development")
        == result
    )
    assert (
        sha256_file(paths[0] / "checkpoint.pt")
        == result["runs"][0]["checkpoint_sha256"]
    )
    (paths[0] / "checkpoint.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checkpoint|changed|differ"):
        secondary.validate_secondary_runs(config_path="fixture", stage="development")


def test_complete_secondary_report_requires_660_cells_and_reports_paired_seed_values(
    tmp_path, monkeypatch
):
    import pose_embed.motionbert_inputs as input_module
    from pose_embed.benchmark import secondary_evaluation as evaluation
    from pose_embed.benchmark.config import load_methods
    from pose_embed.benchmark.retrieval import (
        evaluate_retrieval,
    )
    from pose_embed.benchmark.runtime import read_json
    from pose_embed.provenance import sha256_file

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    root = tmp_path / "benchmark-v2"
    locks = root / "locks"
    locks.mkdir(parents=True)
    for name in (
        "selection.json",
        "final-runs.json",
        "secondary-plan.json",
        "secondary-final.json",
        "test-opening.json",
    ):
        (locks / name).write_text("{}")
    config = load_benchmark()
    methods = load_methods()
    all_rows = [
        ManifestRecord(
            sample_id=f"S001C001P{person:03d}R001A{action:03d}",
            split="novel_query_official",
        )
        for action in (1, 2)
        for person in (1, 2)
    ]
    anchors = [
        all_rows[i].model_copy(update={"split": "novel_anchor", "is_anchor": True})
        for i in (0, 2)
    ]
    queries = [all_rows[i] for i in (1, 3)]
    episode = {"sample_ids": [r.sample_id for r in all_rows]}
    manifests = {
        "novel-anchor.jsonl": anchors,
        "novel-query-official.jsonl": queries,
        "novel-query-primary.jsonl": queries,
    }
    monkeypatch.setattr(
        input_module, "verify_manifest_bundle", lambda *args: ({}, manifests)
    )
    monkeypatch.setattr(
        evaluation, "validate_opening", lambda **kwargs: {"novel_episode": episode}
    )
    monkeypatch.setattr(evaluation, "code_digest", lambda: "fixture-code")
    bindings = {"fixture": "synthetic-only"}
    main = {"runs": [], "inputs": bindings}
    extra = {"runs": [], "inputs": bindings}
    monkeypatch.setattr(evaluation, "validate_final_runs", lambda **kwargs: main)
    monkeypatch.setattr(evaluation, "validate_secondary_runs", lambda **kwargs: extra)
    monkeypatch.setattr(
        evaluation, "verify_run", lambda path: read_json(path / "run-manifest.json")
    )
    paths = []
    training = {}
    multi = evaluate_retrieval(
        np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.1, 0.9]]),
        np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.1, 0.9]]),
        all_rows,
        all_rows,
        recall_k=config.metrics.recall_k,
    )
    shot = one_shot_metrics(
        {"embeddings": np.eye(2)}, {"embeddings": np.eye(2)}, queries, anchors
    )
    for number, key in enumerate(sorted(expected_result_keys(config))):
        task, name, seed, query, condition = key
        cell_id = name if task == "training_study" else None
        multi_positive = evaluation._uses_multi_positive(task, query)
        method = secondary.training_cells()[name]["method"] if cell_id else name
        train_key = (cell_id or method, seed)
        if train_key not in training:
            train = root / "runs" / str(len(training))
            train.mkdir(parents=True)
            run = {
                "method": method,
                "seed": seed,
                "parity_sha256": "fixture-parity",
                "method_specification": methods[method].model_dump(mode="json"),
            }
            if cell_id:
                run["secondary"] = {"cell_id": cell_id}
            (train / "run-manifest.json").write_text(json.dumps({"identity": run}))
            (train / "checkpoint.pt").write_bytes(b"fixture-only")
            ref = {
                "relative_path": str(train.relative_to(root)),
                "method": method,
                "seed": seed,
                "run_manifest_sha256": sha256_file(train / "run-manifest.json"),
                "checkpoint_sha256": sha256_file(train / "checkpoint.pt"),
            }
            (extra if cell_id else main)["runs"].append(ref)
            training[train_key] = ref
        identity = {
            "classification": "secondary_descriptive",
            "task": task,
            "cell_id": cell_id,
            "method": method,
            "seed": seed,
            "run": training[train_key],
            "query_definition": query,
            "condition": condition,
            "code_sha256": "fixture-code",
            "input_bindings": bindings,
            "parity_sha256": "fixture-parity",
            "query_sample_ids": episode["sample_ids"]
            if multi_positive
            else [r.sample_id for r in queries],
            "gallery_sample_ids": episode["sample_ids"]
            if multi_positive
            else [r.sample_id for r in anchors],
            "scoring_policy": evaluation._secondary_policy(
                method, methods[method].parameters, task, query
            ),
            **evaluation._hashes(),
        }
        destination = root / "results" / str(number)
        destination.mkdir(parents=True)
        (destination / "attempt.json").write_text(json.dumps({"identity": identity}))
        (destination / "outcome.json").write_text(json.dumps({"status": "succeeded"}))
        (destination / "rank-metrics.json").write_text(
            json.dumps(multi if multi_positive else shot)
        )
        (destination / "evaluation-manifest.json").write_text(
            json.dumps(
                {
                    "identity": identity,
                    "outputs": {
                        filename: sha256_file(destination / filename)
                        for filename in (
                            "attempt.json",
                            "outcome.json",
                            "rank-metrics.json",
                        )
                    },
                }
            )
        )
        paths.append(destination)
    result = evaluation.report_secondary(
        paths,
        config_path="configs/benchmark.v2.yaml",
        manifest_set_path="fixture",
        output_dir=root / "report",
    )
    assert result["unique_evaluation_count"] == 660
    assert len(result["rows"]) == 110
    assert result["confirmatory_claims_allowed"] is False
    assert all(len(row["seeds"]) == 6 for row in result["rows"])
    assert all(
        value["sample_standard_deviation"] == 0
        for row in result["rows"]
        for value in row["summary"].values()
    )
    with pytest.raises(ValueError, match="every predeclared"):
        evaluation.report_secondary(
            paths[:-1],
            config_path="configs/benchmark.v2.yaml",
            manifest_set_path="fixture",
            output_dir=root / "incomplete",
        )


def test_secondary_recipe_inherits_verified_main_winner_and_fixed_steps(
    tmp_path, monkeypatch
):
    import yaml

    from pose_embed.benchmark.campaign import candidate_config
    from pose_embed.benchmark.runtime import digest

    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    config = load_benchmark()
    config = config.model_copy(
        update={
            "training": config.training.model_copy(update={"encoder_mode": "finetune"})
        }
    )
    path = tmp_path / "main.yaml"
    path.write_text(yaml.safe_dump(config.model_dump()))
    lock = tmp_path / "benchmark-v2/locks"
    lock.mkdir(parents=True)
    (lock / "selection.json").write_text("{}")
    selected = {"inputs": {"fixture": "selected"}, "methods": {}}
    for method in (
        "contextual",
        "contrastive",
        "multi_similarity",
        "multi_similarity_miner",
    ):
        candidate = "half" if method == "contextual" else "double"
        chosen = candidate_config(config, candidate)
        selected["methods"][method] = {
            "candidate": candidate,
            "configuration_sha256": digest(chosen.model_dump(mode="json")),
            "selected_steps": 3,
        }
    resolved = secondary._lock_content(path, selected)
    pure = resolved["cells"]["robustness-context_only-clean-0"]
    assert pure["configuration"]["training"]["learning_rate_scale"] == 0.5
    assert pure["configuration"]["training"]["steps"] == 3
    assert pure["configuration"]["training"]["samples_per_class"] == 8
    assert pure["method_specification"]["parameters"]["lam"] == 1
    assert pure["method_specification"]["parameters"]["gamma"] == 0
    contrast = resolved["cells"]["robustness-contrastive-clean-0"]
    assert contrast["configuration"]["training"]["learning_rate_scale"] == 2
    assert resolved["forecast"]["optimizer_updates_per_stage"] == 276 * 3
    assert resolved["forecast"]["physical_training_items_per_stage"] == 276 * 3 * 32
    selected["methods"]["contextual"]["configuration_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="configuration hash"):
        secondary._lock_content(path, selected)
