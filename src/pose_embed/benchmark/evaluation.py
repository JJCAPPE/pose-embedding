"""Sealed novel evaluation and complete paired reports for benchmark v2."""

from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from pose_embed.benchmark.analysis import analysis_plan_sha256, paired_intervals
from pose_embed.benchmark.config import benchmark_digest, load_benchmark, load_methods
from pose_embed.benchmark.descriptors import (
    encode_retrieval,
    make_score_rows,
    read_descriptors,
    save_descriptors,
)
from pose_embed.benchmark.locks import open_test, validate_final_runs, validate_opening
from pose_embed.benchmark.model import (
    MotionRetrievalModel,
    supports_embedding_inference,
)
from pose_embed.benchmark.retrieval import (
    CUSTOM_SCORERS,
    RETRIEVAL_POLICY,
    evaluate_retrieval,
    method_retrieval_policy,
)
from pose_embed.benchmark.runner import PoseDataset, encode
from pose_embed.benchmark.runtime import (
    REPOSITORY,
    artifact_path,
    artifact_root,
    code_digest,
    digest,
    now,
    read_json,
    verify_run,
)
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.models.motionbert import (
    configure_deterministic_inference,
    inference_environment,
    load_frozen_encoder,
    verify_motionbert_assets,
)
from pose_embed.motionbert_inputs import (
    build_motionbert_bindings,
    load_motionbert_inputs,
)
from pose_embed.motionbert_parity import validate_parity_report
from pose_embed.provenance import sha256_file, write_immutable_json


def _reference(directory: Path, final_runs: dict) -> dict:
    relative = str(directory.relative_to(artifact_root()))
    matches = [r for r in final_runs["runs"] if r["relative_path"] == relative]
    if len(matches) != 1:
        raise ValueError("run is absent or duplicated in the complete final lock")
    reference = matches[0]
    for filename, key in (
        ("run-manifest.json", "run_manifest_sha256"),
        ("checkpoint.pt", "checkpoint_sha256"),
    ):
        if sha256_file(directory / filename) != reference[key]:
            raise ValueError("final run differs from its locked reference")
    return reference


def _lock_hashes() -> dict[str, str]:
    return {
        "analysis_plan_sha256": analysis_plan_sha256(),
        **{
            key: sha256_file(artifact_root() / "locks" / filename)
            for key, filename in (
                ("selection_sha256", "selection.json"),
                ("final_run_set_sha256", "final-runs.json"),
                ("test_opening_sha256", "test-opening.json"),
            )
        },
    }


def _effective_final_config(config, identity):
    from pose_embed.benchmark.campaign import candidate_config

    # validate_final_runs has already checked the selected winner for this cell.
    return candidate_config(config, identity["candidate"])


def evaluate_final(
    run_dir: str | Path,
    config_path: str | Path,
    manifest_set_path: str | Path,
    parity_evidence_path: str | Path,
    output_dir: str | Path,
    device: str = "cuda",
) -> dict[str, Any]:
    """Verify the entire final roster, open its ledger, then encode novel poses."""
    config = load_benchmark(config_path)
    final_runs = validate_final_runs(config_path=config_path)
    directory = artifact_path(run_dir)
    destination = artifact_path(output_dir)
    if destination.exists():
        raise FileExistsError("evaluation output already exists; use a new attempt")
    reference = _reference(directory, final_runs)
    manifest = verify_run(directory)
    identity = manifest["identity"]
    spec = load_methods()[reference["method"]]
    if (
        identity["stage"] != "final"
        or identity["track"] != "finetune"
        or identity["scientific_use_allowed"] is not True
        or identity["method"] != reference["method"]
        or identity["seed"] != reference["seed"]
        or identity["benchmark_sha256"]
        != benchmark_digest(_effective_final_config(config, identity))
        or identity["method_specification"] != spec.model_dump(mode="json")
    ):
        raise ValueError("evaluation requires the exact selected scientific final run")
    if not supports_embedding_inference(spec.method_id):
        raise ValueError("architecture-specific evaluation model is not implemented")

    configure_deterministic_inference()
    inputs = load_motionbert_inputs(
        REPOSITORY / config.input_protocol, manifest_set_path
    )
    assets = verify_motionbert_assets(inputs.data_root)
    bindings = build_motionbert_bindings(inputs, assets)
    if bindings != final_runs["inputs"] or bindings != identity["inputs"]:
        raise ValueError("physical input bindings differ from final training")
    validate_parity_report(parity_evidence_path, bindings)
    if sha256_file(parity_evidence_path) != identity["parity_sha256"]:
        raise ValueError("evaluation parity evidence differs from training")
    encoder, _ = load_frozen_encoder(inputs.data_root, device)
    model = MotionRetrievalModel(
        encoder,
        embedding_dimension=spec.embedding_dimension,
        train_encoder=True,
        method_id=spec.method_id,
        method_parameters=spec.parameters,
    ).to(device)
    checkpoint = torch.load(
        directory / "checkpoint.pt", map_location="cpu", weights_only=True
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()
    rows = inputs.manifests["official-novel.jsonl"]
    annotations = {a["frame_dir"]: a for a in inputs.annotations}
    dataset = PoseDataset(rows, annotations, inputs.protocol)

    # Full physical sources, parity and checkpoint shape are checked before opening.
    # No model forward occurs until open_test has validated all 26 x 6 final runs.
    opening = open_test(manifest_set_path=manifest_set_path, config_path=config_path)
    if [r.sample_id for r in rows] != opening["novel_episode"]["sample_ids"]:
        raise ValueError("novel rows differ from the opening ledger")
    evaluation_identity = {
        "schema_version": 2,
        "stage": "final_evaluation",
        "benchmark_sha256": benchmark_digest(config),
        "code_sha256": code_digest(),
        "run": reference,
        "embedding_dimension": spec.embedding_dimension,
        "input_bindings": bindings,
        "parity_sha256": sha256_file(parity_evidence_path),
        "episode_sha256": digest(opening["novel_episode"]),
        **_lock_hashes(),
    }
    destination.mkdir(parents=True, exist_ok=False)
    write_immutable_json(
        destination / "attempt.json",
        {"identity": evaluation_identity, "started_at": now()},
    )
    try:
        encoding_started = time.perf_counter()
        custom = spec.method_id in CUSTOM_SCORERS
        descriptors = (
            encode_retrieval(
                model, dataset, device, config.training.physical_batch_size
            )
            if custom
            else {
                "embeddings": encode(
                    model, dataset, device, config.training.physical_batch_size
                )
            }
        )
        encoding_seconds = time.perf_counter() - encoding_started
        scoring_started = time.perf_counter()
        embedded = descriptors["embeddings"]
        if embedded.shape != (len(rows), spec.embedding_dimension):
            raise ValueError("trained model output dimension differs from the registry")
        result = evaluate_retrieval(
            embedded,
            embedded,
            rows,
            rows,
            recall_k=config.metrics.recall_k,
            score_rows=make_score_rows(model, descriptors, descriptors),
            scoring_policy=method_retrieval_policy(spec.method_id, spec.parameters),
        )
        scoring_seconds = time.perf_counter() - scoring_started
        if custom:
            write_immutable_json(
                destination / "retrieval-timing.json",
                {
                    "encoding_seconds": encoding_seconds,
                    "scoring_seconds": scoring_seconds,
                    "environment": inference_environment(device),
                },
            )
            save_descriptors(
                destination, descriptors, spec.method_id, spec.embedding_dimension
            )
        write_immutable_json(destination / "rank-metrics.json", result)
        write_immutable_json(
            destination / "outcome.json", {"status": "succeeded", "completed_at": now()}
        )
        output = {
            "schema_version": 2,
            "identity": evaluation_identity,
            "outputs": {
                name: sha256_file(destination / name)
                for name in (
                    ("attempt.json", "rank-metrics.json", "outcome.json")
                    + (
                        (
                            "retrieval-descriptors.npz",
                            "descriptor-storage.json",
                            "retrieval-timing.json",
                        )
                        if custom
                        else ()
                    )
                )
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


def _validated_metrics(
    result: dict, episode: dict, cutoffs: tuple[int, ...], expected_policy=None
) -> dict:
    """Rederive every metric from valid ranks and the locked candidate identities."""
    sample_ids = episode["sample_ids"]
    if (
        result.get("schema_version") != 1
        or result.get("policy") != (expected_policy or RETRIEVAL_POLICY)
        or result.get("query_sample_ids") != sample_ids
        or result.get("gallery_sample_ids") != sample_ids
        or result.get("query_order_sha256") != digest(sample_ids)
        or result.get("gallery_order_sha256") != digest(sample_ids)
    ):
        raise ValueError(
            "result query/gallery identities or policy differ from the lock"
        )
    identities = [parse_ntu_sample_id(value) for value in sample_ids]
    counts = Counter(row.action for row in identities)
    performances: dict[tuple, list[str]] = defaultdict(list)
    for row in identities:
        performances[row.performance_id].append(row.sample_id)
    rows = result.get("per_query")
    if not isinstance(rows, list) or len(rows) != len(identities) or not rows:
        raise ValueError("result has incomplete per-query evidence")
    values = defaultdict(list)
    exclusions = []
    for identity, row in zip(identities, rows, strict=True):
        excluded = performances[identity.performance_id]
        relevant = counts[identity.action] - len(excluded)
        valid = len(identities) - len(excluded)
        ranks = row.get("relevant_ranks")
        if (
            row.get("sample_id") != identity.sample_id
            or row.get("label") != identity.action
            or row.get("excluded_gallery_ids") != excluded
            or row.get("relevant_count") != relevant
            or row.get("valid_gallery_count") != valid
            or relevant < 1
            or not isinstance(ranks, list)
            or len(ranks) != relevant
            or any(
                isinstance(r, bool) or not isinstance(r, int) or not 1 <= r <= valid
                for r in ranks
            )
            or sorted(set(ranks)) != ranks
        ):
            raise ValueError("per-query ranks, relevance or exclusions are invalid")
        precision = [i / rank for i, rank in enumerate(ranks, 1)]
        derived = {
            "average_precision": sum(precision) / relevant,
            "average_precision_at_r": sum(
                p for p, rank in zip(precision, ranks, strict=True) if rank <= relevant
            )
            / relevant,
            "reciprocal_rank": 1 / ranks[0],
        }
        if row.get("first_relevant_rank") != ranks[0] or row.get("recall_at_k") != {
            str(k): ranks[0] <= k for k in cutoffs
        }:
            raise ValueError(
                "per-query first rank or recall differs from relevant ranks"
            )
        for key, expected in derived.items():
            actual = row.get(key)
            if (
                isinstance(actual, bool)
                or not isinstance(actual, (int, float))
                or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
            ):
                raise ValueError("per-query metric differs from relevant ranks")
        for key, source in (
            ("map", "average_precision"),
            ("map_at_r", "average_precision_at_r"),
            ("mrr", "reciprocal_rank"),
        ):
            values[key].append(derived[source])
        for k in cutoffs:
            values[f"r_at_{k}"].append(float(ranks[0] <= k))
        exclusions.append({"sample_id": identity.sample_id, "excluded": excluded})
    metrics = {key: sum(items) / len(items) for key, items in values.items()}
    metrics.update(query_count=len(rows), gallery_count=len(rows))
    recorded = result.get("metrics", {})
    if (
        set(recorded) != set(metrics)
        or any(
            isinstance(recorded[key], bool)
            or not isinstance(recorded[key], (int, float))
            or not math.isclose(recorded[key], value, rel_tol=0, abs_tol=1e-12)
            for key, value in metrics.items()
        )
        or result.get("exclusion_sha256") != digest(exclusions)
    ):
        raise ValueError(
            "aggregate metrics or exclusion hash differ from query evidence"
        )
    return metrics


def _replay_structural_result(directory, run_dir, spec, episode, config, result):
    from pose_embed.config import load_protocol

    descriptors = read_descriptors(
        directory, spec.method_id, len(episode["sample_ids"]), spec.embedding_dimension
    )
    protocol = load_protocol(REPOSITORY / config.input_protocol)
    checkpoint = torch.load(
        run_dir / "checkpoint.pt", map_location="cpu", weights_only=True
    )
    replay_encoder = torch.nn.Identity()
    if spec.method_id == "proxy_anchor_avsl":
        widths = [
            checkpoint["model"][f"head.projections.{index}.weight"].shape[1]
            for index in (0, 1)
        ]
        if widths[0] != widths[1]:
            raise ValueError("AVSL intermediate feature widths differ")
        replay_encoder.dim_feat = widths[0]
    with torch.random.fork_rng():
        model = MotionRetrievalModel(
            replay_encoder,
            method_id=spec.method_id,
            embedding_dimension=spec.embedding_dimension,
            representation_dimension=protocol.encoder.representation_dimension,
            method_parameters=spec.parameters,
        )
    model.head.load_state_dict(
        {
            name.removeprefix("head."): value
            for name, value in checkpoint["model"].items()
            if name.startswith("head.")
        },
        strict=True,
    )
    model.eval()
    rows = [{"sample_id": value} for value in episode["sample_ids"]]
    replay = evaluate_retrieval(
        descriptors["embeddings"],
        descriptors["embeddings"],
        rows,
        rows,
        recall_k=config.metrics.recall_k,
        score_rows=make_score_rows(model, descriptors, descriptors),
        scoring_policy=method_retrieval_policy(spec.method_id, spec.parameters),
    )
    if result != replay:
        raise ValueError(
            "saved structural retrieval ranks differ from descriptor/checkpoint replay"
        )


def _read_evaluation(
    directory: Path, final_runs: dict, opening: dict, config
) -> tuple[tuple[str, int], dict, list[dict]]:
    manifest = read_json(directory / "evaluation-manifest.json")
    identity = manifest.get("identity", {})
    custom = identity.get("run", {}).get("method") in CUSTOM_SCORERS
    output_names = {"attempt.json", "rank-metrics.json", "outcome.json"}
    if custom:
        output_names.update(
            {
                "retrieval-descriptors.npz",
                "descriptor-storage.json",
                "retrieval-timing.json",
            }
        )
    if (
        manifest.get("schema_version") != 2
        or set(manifest.get("outputs", {})) != output_names
    ):
        raise ValueError("evaluation manifest has incomplete output evidence")
    for name, expected in manifest["outputs"].items():
        if sha256_file(directory / name) != expected:
            raise ValueError("evaluation output was changed")
    if (
        read_json(directory / "attempt.json").get("identity") != identity
        or read_json(directory / "outcome.json").get("status") != "succeeded"
    ):
        raise ValueError("evaluation attempt did not succeed with this identity")
    reference = identity.get("run", {})
    if reference not in final_runs["runs"]:
        raise ValueError("evaluation run is absent from the complete lock")
    run_dir = artifact_path(artifact_root() / reference["relative_path"])
    _reference(run_dir, final_runs)
    run = verify_run(run_dir)["identity"]
    spec = load_methods()[reference["method"]]
    expected_identity = {
        "schema_version": 2,
        "stage": "final_evaluation",
        "benchmark_sha256": benchmark_digest(config),
        "code_sha256": code_digest(),
        "run": reference,
        "embedding_dimension": spec.embedding_dimension,
        "input_bindings": final_runs["inputs"],
        "parity_sha256": run["parity_sha256"],
        "episode_sha256": digest(opening["novel_episode"]),
        **_lock_hashes(),
    }
    if identity != expected_identity:
        raise ValueError("evaluation provenance differs from the complete test lock")
    result = read_json(directory / "rank-metrics.json")
    if custom:
        _replay_structural_result(
            directory, run_dir, spec, opening["novel_episode"], config, result
        )
    return (
        (reference["method"], reference["seed"]),
        _validated_metrics(
            result,
            opening["novel_episode"],
            config.metrics.recall_k,
            method_retrieval_policy(spec.method_id, spec.parameters),
        ),
        result["per_query"],
    )


def _summarize_matrix(
    matrix: dict, per_query: dict, episode: dict, config, methods
) -> dict:
    expected = {
        (method, seed)
        for method in config.final_methods
        for seed in config.training.seeds
    }
    if set(matrix) != expected or set(per_query) != expected:
        raise ValueError("report requires all 26 methods and six paired seeds")
    seeds = list(config.training.seeds)
    first = next(iter(matrix.values()))
    metrics = sorted(set(first) - {"query_count", "gallery_count"})
    if any(set(row) != set(first) for row in matrix.values()):
        raise ValueError("reported methods have different metric sets")
    scores = {}
    for key, rows in per_query.items():
        if [row["sample_id"] for row in rows] != episode["sample_ids"]:
            raise ValueError("paired analysis query identities differ")
        hits = [float(row["recall_at_k"]["1"]) for row in rows]
        if not hits or not math.isclose(
            sum(hits) / len(hits), matrix[key]["r_at_1"], abs_tol=1e-12
        ):
            raise ValueError("primary aggregate differs from its paired query hits")
        scores[key] = hits
    inference = paired_intervals(scores, episode["sample_ids"], config)
    groups = []
    for dimension in sorted(
        {methods[method].embedding_dimension for method in config.final_methods}
    ):
        roster = [
            m
            for m in config.final_methods
            if methods[m].embedding_dimension == dimension
        ]
        table = []
        for method in roster:
            vectors = {
                key: np.array(
                    [matrix[(method, seed)][key] for seed in seeds], dtype=float
                )
                for key in metrics
            }
            if any(
                not np.isfinite(vector).all()
                or (vector < 0).any()
                or (vector > 1).any()
                for vector in vectors.values()
            ):
                raise ValueError("report metrics must be finite proportions")
            table.append(
                {
                    "method": method,
                    "metrics": {
                        key: {
                            "mean": float(vector.mean()),
                            "sample_std": float(vector.std(ddof=1)),
                            "per_seed": vector.tolist(),
                        }
                        for key, vector in vectors.items()
                    },
                }
            )
        groups.append(
            {
                "embedding_dimension": dimension,
                "methods": table,
                "paired_primary_comparisons": [
                    row
                    for row in inference["comparisons"]
                    if row["embedding_dimension"] == dimension
                ],
            }
        )
    return {
        "schema_version": 2,
        "stage": "final_report",
        "complete": True,
        "required_runs": len(expected),
        "seeds": seeds,
        "query_count": first["query_count"],
        "gallery_count": first["gallery_count"],
        "groups": groups,
        "uncertainty": {
            key: value for key, value in inference.items() if key != "comparisons"
        },
        "interpretation": (
            "All declared results and directions are retained. A positive comparison "
            "requires its simultaneous interval to exclude zero; raw intervals and "
            "secondary metrics do not authorize a superiority claim."
        ),
    }


def report_final(
    result_dirs: list[str | Path], config_path: str | Path, output_dir: str | Path
) -> dict:
    """Verify a complete final matrix and publish a summary without sample IDs."""
    config = load_benchmark(config_path)
    final_runs = validate_final_runs(config_path=config_path)
    ledger = read_json(artifact_root() / "locks/test-opening.json")
    opening = validate_opening(
        manifest_set_path=ledger["manifest_set_path"], config_path=config_path
    )
    matrix, per_query, evidence = {}, {}, []
    for value in result_dirs:
        directory = artifact_path(value)
        key, metrics, rows = _read_evaluation(directory, final_runs, opening, config)
        if key in matrix:
            raise ValueError("duplicate evaluation for a method/seed")
        matrix[key] = metrics
        per_query[key] = rows
        evidence.append(sha256_file(directory / "evaluation-manifest.json"))
    summary = _summarize_matrix(
        matrix, per_query, opening["novel_episode"], config, load_methods()
    )
    summary.update(
        benchmark_sha256=benchmark_digest(config),
        code_sha256=code_digest(),
        evaluation_manifest_sha256=sorted(evidence),
        **_lock_hashes(),
    )
    destination = artifact_path(output_dir)
    destination.mkdir(parents=True, exist_ok=False)
    write_immutable_json(destination / "summary.json", summary)
    return summary
