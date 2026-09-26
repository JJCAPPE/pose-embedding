"""Secondary-only one-shot, query corruption and training-study evaluation."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import torch

from pose_embed.benchmark.config import load_benchmark
from pose_embed.benchmark.descriptors import (
    encode_retrieval,
    make_score_rows,
    validate_descriptors,
)
from pose_embed.benchmark.evaluation import _reference
from pose_embed.benchmark.locks import open_test, validate_final_runs, validate_opening
from pose_embed.benchmark.model import MotionRetrievalModel
from pose_embed.benchmark.retrieval import evaluate_retrieval, method_retrieval_policy
from pose_embed.benchmark.runner import PoseDataset
from pose_embed.benchmark.runtime import (
    REPOSITORY,
    artifact_path,
    artifact_root,
    code_digest,
    now,
    read_json,
    verify_run,
)
from pose_embed.benchmark.secondary import (
    CONDITIONS,
    load_secondary_plan,
    secondary_plan_sha256,
    secondary_validation_scope,
    validate_secondary_runs,
)
from pose_embed.corruptions.pose import apply_corruption
from pose_embed.evaluation.metrics import evaluate_one_shot
from pose_embed.models.motionbert import (
    configure_deterministic_inference,
    load_frozen_encoder,
    verify_motionbert_assets,
)
from pose_embed.motionbert_inputs import (
    build_motionbert_bindings,
    load_motionbert_inputs,
)
from pose_embed.motionbert_parity import validate_parity_report
from pose_embed.provenance import sha256_file, write_immutable_json


class CorruptedQueries(PoseDataset):
    def __init__(self, records, annotations, protocol, condition):
        super().__init__(records, annotations, protocol)
        self.family, severity = condition.split(":")
        self.severity = float(severity)

    def __getitem__(self, index):
        poses, label = super().__getitem__(index)
        return apply_corruption(
            poses,
            family=self.family,
            severity=self.severity,
            sample_id=self.records[index].sample_id,
        ), label


def one_shot_metrics(query, gallery, queries, anchors, score_rows=None):
    labels = torch.tensor([row.ntu.action for row in queries])
    gallery_labels = torch.tensor([row.ntu.action for row in anchors])
    query_ids = [row.sample_id for row in queries]
    if score_rows is None:
        result = evaluate_one_shot(
            torch.as_tensor(gallery["embeddings"]),
            gallery_labels,
            torch.as_tensor(query["embeddings"]),
            labels,
            query_ids=query_ids,
        ).as_dict()
    else:
        if len(set(gallery_labels.tolist())) != len(anchors) or not set(
            labels.tolist()
        ) <= set(gallery_labels.tolist()):
            raise ValueError("one-shot requires exactly one anchor per query action")
        per_query = []
        for start in range(0, len(queries), 128):
            stop = min(len(queries), start + 128)
            # Official one-shot retains synchronized anchor-performance views.
            scores = torch.as_tensor(
                score_rows(
                    list(range(start, stop)),
                    list(range(len(anchors))),
                    [[] for _ in range(start, stop)],
                )
            )
            if (
                scores.shape != (stop - start, len(anchors))
                or not scores.is_floating_point()
                or not torch.isfinite(scores).all()
            ):
                raise ValueError("structural one-shot scorer returned invalid scores")
            ranks = gallery_labels[
                torch.argsort(scores, dim=1, descending=True, stable=True)
            ]
            for local, index in enumerate(range(start, stop)):
                rank = int((ranks[local] == labels[index]).nonzero()[0, 0]) + 1
                per_query.append(
                    {
                        "sample_id": query_ids[index],
                        "label": int(labels[index]),
                        "rank": rank,
                        "predicted_label": int(ranks[local, 0]),
                        "top1_correct": rank == 1,
                    }
                )
        result = {
            "query_count": len(queries),
            "gallery_count": len(anchors),
            "per_query": per_query,
        }
        result.update(
            top1=float(np.mean([row["rank"] == 1 for row in per_query])),
            mrr=float(np.mean([1 / row["rank"] for row in per_query])),
            r_at_5=float(np.mean([row["rank"] <= 5 for row in per_query])),
        )
    result["map"] = result["mrr"]
    result["query_sample_ids"] = query_ids
    result["gallery_sample_ids"] = [row.sample_id for row in anchors]
    return result


def _uses_multi_positive(task, query_definition):
    return task == "training_study" or (
        task == "query_corruption" and query_definition == "primary"
    )


def _secondary_policy(method, parameters, task, query_definition):
    policy = method_retrieval_policy(method, parameters)
    if not _uses_multi_positive(task, query_definition):
        policy.update(
            relevance="one_clean_anchor_with_same_action",
            exclusion="none_official_query_set",
            recall="single_relevant_anchor_in_first_k",
            average_precision="single_relevant_anchor_reciprocal_rank",
            average_precision_at_r="not_reported",
        )
    return policy


def _hashes():
    return {
        "secondary_plan_sha256": secondary_plan_sha256(),
        **{
            key: sha256_file(artifact_root() / "locks" / name)
            for key, name in (
                ("selection_sha256", "selection.json"),
                ("main_final_sha256", "final-runs.json"),
                ("secondary_lock_sha256", "secondary-plan.json"),
                ("secondary_final_sha256", "secondary-final.json"),
                ("opening_sha256", "test-opening.json"),
            )
        },
    }


@secondary_validation_scope()
def evaluate_secondary(
    *,
    run_dir,
    config_path,
    manifest_set_path,
    parity_evidence_path,
    output_dir,
    task,
    query_definition="official",
    condition="clean",
    device="cuda",
):
    config = load_benchmark(config_path)
    plan = load_secondary_plan(config)
    main_final = validate_final_runs(config_path=config_path)
    secondary_final = validate_secondary_runs(config_path=config_path)
    directory, destination = artifact_path(run_dir), artifact_path(output_dir)
    if destination.exists():
        raise FileExistsError("secondary evaluation already exists; use a new attempt")
    manifest = verify_run(directory)
    identity = manifest["identity"]
    secondary = identity.get("secondary")
    if task not in {"one_shot", "query_corruption", "training_study"}:
        raise ValueError("unknown declared secondary evaluation task")
    if task == "training_study":
        if secondary is None or condition != "clean" or query_definition != "official":
            raise ValueError(
                "training-study evaluation requires its clean multi-positive task"
            )
        reference = _reference(directory, secondary_final)
        cell = secondary["cell_id"]
    else:
        if secondary is not None:
            raise ValueError("one-shot/corruption uses selected clean main checkpoints")
        reference = _reference(directory, main_final)
        cell = None
        if task == "one_shot" and (
            condition != "clean" or query_definition != "official"
        ):
            raise ValueError("official one-shot is the clean official query task")
        if task == "query_corruption" and (
            identity["method"] not in plan["query_corruption"]["methods"]
            or query_definition not in plan["query_corruption"]["query_definitions"]
            or condition not in CONDITIONS
        ):
            raise ValueError(
                "corruption method/query/condition lies outside the locked matrix"
            )
    if (
        identity["stage"] != "final"
        or identity["track"] != "finetune"
        or not identity["scientific_use_allowed"]
    ):
        raise ValueError(
            "secondary novel evaluation requires locked scientific final training"
        )
    configure_deterministic_inference()
    inputs = load_motionbert_inputs(
        REPOSITORY / config.input_protocol, manifest_set_path
    )
    assets = verify_motionbert_assets(inputs.data_root)
    bindings = build_motionbert_bindings(inputs, assets)
    if bindings != main_final["inputs"] or bindings != identity["inputs"]:
        raise ValueError("secondary physical inputs differ from final training")
    validate_parity_report(parity_evidence_path, bindings)
    if sha256_file(parity_evidence_path) != identity["parity_sha256"]:
        raise ValueError("secondary parity evidence differs from training")
    spec = identity["method_specification"]
    encoder, _ = load_frozen_encoder(inputs.data_root, device)
    model = MotionRetrievalModel(
        encoder,
        embedding_dimension=spec["embedding_dimension"],
        train_encoder=True,
        method_id=identity["method"],
        method_parameters=spec["parameters"],
    ).to(device)
    checkpoint = torch.load(
        directory / "checkpoint.pt", map_location="cpu", weights_only=True
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()
    annotations = {row["frame_dir"]: row for row in inputs.annotations}
    multi_positive = _uses_multi_positive(task, query_definition)
    if multi_positive:
        queries = anchors = inputs.manifests["official-novel.jsonl"]
    else:
        anchors = inputs.manifests["novel-anchor.jsonl"]
        queries = inputs.manifests[f"novel-query-{query_definition}.jsonl"]
    opening = open_test(manifest_set_path=manifest_set_path, config_path=config_path)
    if not set(row.sample_id for row in [*queries, *anchors]) <= set(
        opening["novel_episode"]["sample_ids"]
    ):
        raise ValueError("secondary episode lies outside the sealed novel pool")
    evidence = {
        "schema_version": 1,
        "classification": "secondary_descriptive",
        "task": task,
        "cell_id": cell,
        "method": identity["method"],
        "seed": identity["seed"],
        "run": reference,
        "condition": condition,
        "query_definition": "multi_positive"
        if task == "training_study"
        else query_definition,
        "query_sample_ids": [row.sample_id for row in queries],
        "gallery_sample_ids": [row.sample_id for row in anchors],
        "input_bindings": bindings,
        "parity_sha256": sha256_file(parity_evidence_path),
        "code_sha256": code_digest(),
        "scoring_policy": _secondary_policy(
            identity["method"], spec["parameters"], task, query_definition
        ),
        **_hashes(),
    }
    destination.mkdir(parents=True, exist_ok=False)
    write_immutable_json(
        destination / "attempt.json", {"identity": evidence, "started_at": now()}
    )
    try:
        clean = PoseDataset(anchors, annotations, inputs.protocol)
        gallery = encode_retrieval(
            model, clean, device, config.training.physical_batch_size
        )
        if multi_positive and condition == "clean":
            query = gallery
        else:
            dataset = (
                PoseDataset(queries, annotations, inputs.protocol)
                if condition == "clean"
                else CorruptedQueries(queries, annotations, inputs.protocol, condition)
            )
            query = encode_retrieval(
                model, dataset, device, config.training.physical_batch_size
            )
        for values, records in ((query, queries), (gallery, anchors)):
            validate_descriptors(
                values, identity["method"], len(records), spec["embedding_dimension"]
            )
        scorer = make_score_rows(model, query, gallery)
        result = (
            evaluate_retrieval(
                query["embeddings"],
                gallery["embeddings"],
                queries,
                anchors,
                recall_k=config.metrics.recall_k,
                score_rows=scorer,
                scoring_policy=evidence["scoring_policy"],
            )
            if multi_positive
            else one_shot_metrics(query, gallery, queries, anchors, scorer)
        )
        write_immutable_json(destination / "rank-metrics.json", result)
        write_immutable_json(
            destination / "outcome.json", {"status": "succeeded", "completed_at": now()}
        )
        output = {
            "schema_version": 1,
            "identity": evidence,
            "outputs": {
                name: sha256_file(destination / name)
                for name in ("attempt.json", "rank-metrics.json", "outcome.json")
            },
            "completed_at": now(),
        }
        write_immutable_json(destination / "evaluation-manifest.json", output)
        return output
    except BaseException as exc:
        if not (destination / "outcome.json").exists():
            write_immutable_json(
                destination / "outcome.json",
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "completed_at": now(),
                },
            )
        raise


def _result_key(identity):
    task = identity["task"]
    if (
        task == "query_corruption"
        and identity["condition"] == "clean"
        and identity["query_definition"] == "official"
    ):
        task = "one_shot"
    return (
        task,
        identity["cell_id"] or identity["method"],
        identity["seed"],
        identity["query_definition"],
        identity["condition"],
    )


def expected_result_keys(config):
    from pose_embed.benchmark.secondary import training_cells

    keys = {
        ("one_shot", method, seed, "official", "clean")
        for method in config.final_methods
        for seed in config.training.seeds
    }
    keys.update(
        _result_key(
            {
                "task": "query_corruption",
                "method": method,
                "cell_id": None,
                "seed": seed,
                "query_definition": query,
                "condition": condition,
            }
        )
        for method in ("contrastive", "contextual")
        for seed in config.training.seeds
        for query in ("official", "primary")
        for condition in CONDITIONS
    )
    keys.update(
        ("training_study", cell, seed, "multi_positive", "clean")
        for cell in training_cells()
        for seed in config.training.seeds
    )
    return keys


def _one_shot_validated_metrics(result, identity):
    from pose_embed.data.ntu import parse_ntu_sample_id

    queries, anchors = identity["query_sample_ids"], identity["gallery_sample_ids"]
    rows = result.get("per_query", [])
    classes = [parse_ntu_sample_id(value).action for value in anchors]
    if (
        len(set(classes)) != len(classes)
        or result.get("query_sample_ids") != queries
        or result.get("gallery_sample_ids") != anchors
        or len(rows) != len(queries)
        or result.get("query_count") != len(queries)
        or result.get("gallery_count") != len(anchors)
    ):
        raise ValueError("one-shot evidence differs from its declared identities")
    ranks = []
    for row, sample_id in zip(rows, queries, strict=True):
        label, rank = parse_ntu_sample_id(sample_id).action, row.get("rank")
        if (
            row.get("sample_id") != sample_id
            or row.get("label") != label
            or type(rank) is not int
            or rank not in range(1, len(anchors) + 1)
            or row.get("predicted_label") not in classes
            or row.get("top1_correct") is not (rank == 1)
            or (row["predicted_label"] == label) != (rank == 1)
        ):
            raise ValueError("one-shot per-query ranks or predictions are invalid")
        ranks.append(rank)
    metrics = {
        "top1": float(np.mean(np.array(ranks) == 1)),
        "mrr": float(np.mean(1 / np.array(ranks))),
        "r_at_5": float(np.mean(np.array(ranks) <= 5)),
    }
    metrics["map"] = metrics["mrr"]
    if any(
        not math.isclose(result.get(key, math.nan), value, rel_tol=1e-12, abs_tol=1e-12)
        for key, value in metrics.items()
    ):
        raise ValueError("one-shot metrics differ from their per-query ranks")
    return metrics


@secondary_validation_scope()
def report_secondary(result_dirs, *, config_path, manifest_set_path, output_dir):
    from pose_embed.benchmark.evaluation import _validated_metrics

    config = load_benchmark(config_path)
    opening = validate_opening(
        config_path=config_path, manifest_set_path=manifest_set_path
    )
    main_final = validate_final_runs(config_path=config_path)
    secondary_final = validate_secondary_runs(config_path=config_path)
    from pose_embed.config import load_protocol
    from pose_embed.motionbert_inputs import verify_manifest_bundle

    _, manifests = verify_manifest_bundle(
        load_protocol(REPOSITORY / config.input_protocol), manifest_set_path
    )
    expected, observed = expected_result_keys(config), {}
    destination = artifact_path(output_dir)
    if destination.exists():
        raise FileExistsError("secondary report already exists")
    for path in result_dirs:
        directory = artifact_path(path)
        manifest = read_json(directory / "evaluation-manifest.json")
        identity = manifest["identity"]
        if (
            identity.get("classification") != "secondary_descriptive"
            or identity.get("code_sha256") != code_digest()
            or any(identity.get(key) != value for key, value in _hashes().items())
        ):
            raise ValueError("secondary result differs from its sealed study")
        key = _result_key(identity)
        if key not in expected or key in observed:
            raise ValueError("secondary report has an unexpected or duplicate cell")
        required = {"attempt.json", "rank-metrics.json", "outcome.json"}
        if set(manifest.get("outputs", {})) != required or any(
            sha256_file(directory / name) != value
            for name, value in manifest["outputs"].items()
        ):
            raise ValueError("secondary evaluation files changed")
        if (
            read_json(directory / "attempt.json").get("identity") != identity
            or read_json(directory / "outcome.json").get("status") != "succeeded"
        ):
            raise ValueError(
                "secondary evaluation did not complete with its declared identity"
            )
        training_dir = artifact_root() / identity["run"]["relative_path"]
        final_set = (
            secondary_final if identity["task"] == "training_study" else main_final
        )
        reference = _reference(training_dir, final_set)
        run = verify_run(training_dir)["identity"]
        if (
            reference != identity["run"]
            or run["method"] != identity["method"]
            or run["seed"] != identity["seed"]
            or run.get("secondary", {}).get("cell_id") != identity["cell_id"]
            or identity["input_bindings"] != final_set["inputs"]
            or identity["parity_sha256"] != run["parity_sha256"]
        ):
            raise ValueError("secondary result/checkpoint membership differs")
        multi_positive = _uses_multi_positive(
            identity["task"], identity["query_definition"]
        )
        if multi_positive:
            expected_queries = expected_gallery = opening["novel_episode"]["sample_ids"]
        else:
            expected_queries = [
                row.sample_id
                for row in manifests[
                    f"novel-query-{identity['query_definition']}.jsonl"
                ]
            ]
            expected_gallery = [
                row.sample_id for row in manifests["novel-anchor.jsonl"]
            ]
        if (
            identity["query_sample_ids"] != expected_queries
            or identity["gallery_sample_ids"] != expected_gallery
            or identity["scoring_policy"]
            != _secondary_policy(
                run["method"],
                run["method_specification"]["parameters"],
                identity["task"],
                identity["query_definition"],
            )
        ):
            raise ValueError(
                "secondary episode/scorer differs from the verified input manifests"
            )
        result = read_json(directory / "rank-metrics.json")
        metrics = (
            _validated_metrics(
                result, opening["novel_episode"], config.metrics.recall_k
            )
            if multi_positive
            else _one_shot_validated_metrics(result, identity)
        )
        observed[key] = (metrics, sha256_file(directory / "evaluation-manifest.json"))
    if set(observed) != expected:
        raise ValueError(
            "secondary report requires every predeclared method, "
            "condition and six-seed cell"
        )
    groups = defaultdict(list)
    for key, (metrics, evidence_hash) in sorted(observed.items()):
        task, cell, seed, query, condition = key
        groups[(task, cell, query, condition)].append(
            {"seed": seed, "metrics": metrics, "evidence_sha256": evidence_hash}
        )
    rows = []
    for (task, cell, query, condition), values in sorted(groups.items()):
        summary = {
            name: {
                "mean": float(np.mean([v["metrics"][name] for v in values])),
                "sample_standard_deviation": float(
                    np.std([v["metrics"][name] for v in values], ddof=1)
                ),
            }
            for name in values[0]["metrics"]
        }
        rows.append(
            {
                "task": task,
                "cell_or_method": cell,
                "embedding_dimension": 1536
                if cell in {"proxy_anchor_avsl", "contextual_1536"}
                else 512,
                "query_definition": query,
                "condition": condition,
                "seeds": values,
                "summary": summary,
            }
        )
    output = {
        "schema_version": 1,
        "classification": "secondary_descriptive",
        "confirmatory_claims_allowed": False,
        "unique_evaluation_count": len(observed),
        "coverage": {
            "official_one_shot": 156,
            "query_corruption_including_12_shared_clean_controls": 240,
            "training_studies": 276,
        },
        "rows": rows,
        **_hashes(),
    }
    destination.mkdir(parents=True, exist_ok=False)
    write_immutable_json(destination / "secondary-report.json", output)
    return output
