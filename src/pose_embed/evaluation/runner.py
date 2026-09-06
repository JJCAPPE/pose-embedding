"""Role-authorized evaluation with a fail-closed final-test opening seal."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch

from pose_embed.artifacts import (
    FeatureSidecar,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.data import load_manifest, verify_manifests
from pose_embed.evaluation.metrics import evaluate_one_shot
from pose_embed.evaluation.result import EvaluationResult
from pose_embed.protocol import (
    evaluation_plan_digest,
    final_run_for,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    resolve_scientific_paths,
    validate_evaluation_manifests,
    validate_exploratory_run_artifacts,
    validate_final_run_artifacts,
    validate_locked_manifest,
    verify_protocol,
)
from pose_embed.provenance import (
    capture_provenance,
    capture_runtime_telemetry,
    require_path_within,
    sha256_file,
    write_immutable_json,
)
from pose_embed.test_access import open_final_test_once

EvaluationMode = Literal["development", "final", "exploratory"]
Method = Literal["contrastive", "supcon", "contextual", "multi_similarity_with_miner"]
QueryDefinition = Literal["development", "primary", "official"]


def _load_embeddings(path: Path) -> tuple[torch.Tensor, torch.Tensor, tuple[str, ...]]:
    with np.load(path, allow_pickle=False) as archive:
        key = "embeddings" if "embeddings" in archive.files else "features"
        required = {key, "labels", "sample_ids"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"embedding NPZ is missing keys: {sorted(missing)}")
        embeddings = torch.as_tensor(np.asarray(archive[key]), dtype=torch.float32)
        labels = torch.as_tensor(np.asarray(archive["labels"]), dtype=torch.long)
        sample_ids = tuple(np.asarray(archive["sample_ids"]).astype(str))
    return embeddings, labels, sample_ids


def _authorize_roles(
    gallery_sidecar: FeatureSidecar,
    query_sidecar: FeatureSidecar,
    *,
    mode: EvaluationMode,
    condition: str,
    query_definition: QueryDefinition,
) -> None:
    if gallery_sidecar.role != "gallery_clean" or gallery_sidecar.condition != "clean":
        raise ValueError("evaluation requires a clean gallery role")
    expected_query_role = "query_clean" if condition == "clean" else "query_corrupted"
    if query_sidecar.role != expected_query_role:
        raise ValueError(
            f"condition {condition!r} requires query role {expected_query_role!r}"
        )
    if query_sidecar.condition != condition:
        raise ValueError("declared condition does not match the query feature sidecar")
    if mode == "development":
        if query_definition != "development":
            raise ValueError(
                "development evaluation requires query_definition=development"
            )
        if condition != "clean":
            raise ValueError(
                "development retrieval is clean-only; corruptions are geometric "
                "checks until final-test opening"
            )
        if gallery_sidecar.split != "development_validation" or query_sidecar.split != (
            "development_validation"
        ):
            raise ValueError("development evaluation rejects every novel-test split")
        return
    if query_definition not in {"primary", "official"}:
        raise ValueError("final evaluation requires primary or official queries")
    expected_query_split = f"novel_query_{query_definition}"
    if gallery_sidecar.split != "novel_anchor":
        raise ValueError("final evaluation requires the novel_anchor gallery split")
    if query_sidecar.split != expected_query_split:
        raise ValueError(
            "final query definition does not match the novel-query feature split"
        )
    if not gallery_sidecar.scientific_use_allowed or not (
        query_sidecar.scientific_use_allowed
    ):
        raise ValueError("final evaluation rejects non-scientific fixture artifacts")


def _authorize_method_and_seed(
    gallery_sidecar: FeatureSidecar,
    query_sidecar: FeatureSidecar,
    *,
    method: Method,
    seed: int,
) -> None:
    if gallery_sidecar.head_checkpoint_sha256 != query_sidecar.head_checkpoint_sha256:
        raise ValueError("gallery and query embeddings use different checkpoints")
    if (
        gallery_sidecar.encoder_checkpoint_sha256
        != query_sidecar.encoder_checkpoint_sha256
    ):
        raise ValueError("gallery and query embeddings use different encoders")
    if gallery_sidecar.upstream_sha256 != query_sidecar.upstream_sha256:
        raise ValueError("gallery and query embeddings use different upstream code")
    expected = (method, seed)
    gallery_observed = (gallery_sidecar.method, gallery_sidecar.training_seed)
    query_observed = (query_sidecar.method, query_sidecar.training_seed)
    if gallery_observed != expected or query_observed != expected:
        raise ValueError(
            "declared method and seed do not match the retrieval feature sidecars"
        )


def _validate_identities(
    *,
    protocol: Any,
    gallery_manifest_path: str | Path,
    query_manifest_path: str | Path,
    mode: EvaluationMode,
) -> None:
    gallery_records = load_manifest(gallery_manifest_path)
    query_records = load_manifest(query_manifest_path)
    verify_manifests([*gallery_records, *query_records], protocol)
    gallery_ids = {record.sample_id for record in gallery_records}
    query_ids = {record.sample_id for record in query_records}
    if gallery_ids & query_ids:
        raise ValueError("gallery and query sample identities must be disjoint")
    if mode == "development":
        return
    novel_actions = set(protocol.dataset.novel_actions)
    anchor_counts = Counter(record.ntu.action for record in gallery_records)
    if set(anchor_counts) != novel_actions or set(anchor_counts.values()) != {1}:
        raise ValueError(
            "final gallery requires exactly one anchor for each novel action"
        )
    if {record.ntu.action for record in query_records} != novel_actions:
        raise ValueError("final query set must cover every novel action")


def evaluate_files(
    gallery_path: str | Path,
    query_path: str | Path,
    output_path: str | Path,
    *,
    mode: EvaluationMode,
    protocol_path: str | Path,
    gallery_manifest_path: str | Path,
    query_manifest_path: str | Path,
    method: Method,
    seed: int,
    condition: str,
    query_definition: QueryDefinition,
    allow_fixture: bool = False,
    stretch_run_manifest_path: str | Path | None = None,
    stretch_gate_evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate one development, locked core, or labeled exploratory cell."""
    started_at = datetime.now(UTC)
    protocol, digest = verify_protocol(protocol_path)
    evaluation_plan_sha256: str | None = None
    final_run_set_sha256: str | None = None
    protocol_lock_sha256: str | None = None
    test_opening_ledger_sha256: str | None = None
    run_manifest_sha256: str | None = None
    stretch_gate_evidence_sha256: str | None = None
    source_inventory_manifest_sha256: str | None = None
    anchor_manifest_sha256: str | None = None
    official_query_manifest_sha256: str | None = None
    primary_query_manifest_sha256: str | None = None
    scientific_inputs: list[Path] = []
    final_run = None
    scientific_paths = None
    evaluation_plan = None
    final_run_set = None
    manifest_paths: dict[str, Path] = {}

    if mode == "exploratory":
        if method != "multi_similarity_with_miner":
            raise ValueError("exploratory evaluation is reserved for Multi-Similarity")
        if stretch_run_manifest_path is None or stretch_gate_evidence_path is None:
            raise ValueError(
                "exploratory evaluation requires its run manifest and gate evidence"
            )
    if mode == "final" and method == "multi_similarity_with_miner":
        raise ValueError("core final evaluation excludes exploratory Multi-Similarity")

    if mode in {"final", "exploratory"}:
        if allow_fixture:
            raise ValueError("locked evaluations never permit fixture artifacts")
        scientific_paths = resolve_scientific_paths(protocol)
        require_path_within(
            output_path,
            scientific_paths.root,
            label="locked evaluation output",
        )
        protocol, digest = verify_protocol(
            protocol_path,
            lock_path=scientific_paths.protocol_lock,
            evaluation_plan_path=scientific_paths.evaluation_plan,
            final_run_set_path=scientific_paths.final_run_set,
            require_locked=True,
        )
        evaluation_plan = load_evaluation_plan(scientific_paths.evaluation_plan)
        final_run_set = load_final_run_set(scientific_paths.final_run_set)
        evaluation_plan_sha256 = evaluation_plan_digest(evaluation_plan)
        final_run_set_sha256 = final_run_set_digest(final_run_set)
        protocol_lock_sha256 = sha256_file(scientific_paths.protocol_lock)
        if mode == "final":
            if method not in evaluation_plan.methods:
                raise ValueError(
                    "method is absent from the locked core evaluation plan"
                )
            if (
                stretch_run_manifest_path is not None
                or stretch_gate_evidence_path is not None
            ):
                raise ValueError("core final evaluation cannot accept stretch inputs")
        else:
            if method != "multi_similarity_with_miner":
                raise ValueError(
                    "exploratory evaluation is reserved for Multi-Similarity"
                )
            if stretch_run_manifest_path is None or stretch_gate_evidence_path is None:
                raise ValueError(
                    "exploratory evaluation requires its run manifest and gate evidence"
                )
            if not scientific_paths.test_opening_ledger.is_file():
                raise ValueError(
                    "exploratory evaluation requires an existing core test opening"
                )
        if seed not in evaluation_plan.seeds:
            raise ValueError("seed is absent from the locked evaluation plan")
        if condition not in evaluation_plan.conditions:
            raise ValueError("condition is absent from the locked evaluation plan")
        if query_definition not in evaluation_plan.query_definitions:
            raise ValueError(
                "query definition is absent from the locked evaluation plan"
            )

        ledger = open_final_test_once(protocol, protocol_sha256=digest)
        manifest_validation = validate_evaluation_manifests(
            protocol,
            evaluation_plan,
            scientific_paths.root,
            check_source_files=False,
        )
        manifest_paths = manifest_validation.paths
        assert evaluation_plan.anchor_manifest is not None
        query_binding = (
            evaluation_plan.primary_query_manifest
            if query_definition == "primary"
            else evaluation_plan.official_query_manifest
        )
        assert query_binding is not None
        validate_locked_manifest(
            evaluation_plan.anchor_manifest,
            gallery_manifest_path,
            expected_split="novel_anchor",
        )
        validate_locked_manifest(
            query_binding,
            query_manifest_path,
            expected_split=f"novel_query_{query_definition}",
        )
        if mode == "final":
            final_run = final_run_for(final_run_set, method, seed)
            run_files = validate_final_run_artifacts(
                final_run_set,
                final_run,
                scientific_paths.root,
                protocol=protocol,
            )
            run_manifest_sha256 = final_run.run_manifest_sha256
            scientific_inputs.extend(run_files.values())
        test_opening_ledger_sha256 = sha256_file(scientific_paths.test_opening_ledger)
        if ledger.final_run_set_sha256 != final_run_set_sha256:
            raise ValueError("test-opening ledger differs from the active run set")
        assert evaluation_plan.source_inventory_manifest is not None
        assert evaluation_plan.official_query_manifest is not None
        assert evaluation_plan.primary_query_manifest is not None
        source_inventory_manifest_sha256 = (
            evaluation_plan.source_inventory_manifest.sha256
        )
        anchor_manifest_sha256 = evaluation_plan.anchor_manifest.sha256
        official_query_manifest_sha256 = evaluation_plan.official_query_manifest.sha256
        primary_query_manifest_sha256 = evaluation_plan.primary_query_manifest.sha256
        scientific_inputs.extend(
            [
                scientific_paths.protocol_lock,
                scientific_paths.evaluation_plan,
                scientific_paths.final_run_set,
                scientific_paths.test_opening_ledger,
                *manifest_paths.values(),
            ]
        )
    elif (
        stretch_run_manifest_path is not None or stretch_gate_evidence_path is not None
    ):
        raise ValueError("stretch inputs are only valid in exploratory mode")

    gallery = Path(gallery_path)
    query = Path(query_path)
    gallery_sidecar = validate_feature_artifact(
        gallery,
        protocol=protocol,
        manifest_path=gallery_manifest_path,
        allow_fixture=allow_fixture,
    )
    query_sidecar = validate_feature_artifact(
        query,
        protocol=protocol,
        manifest_path=query_manifest_path,
        allow_fixture=allow_fixture,
    )
    _authorize_roles(
        gallery_sidecar,
        query_sidecar,
        mode=mode,
        condition=condition,
        query_definition=query_definition,
    )
    _authorize_method_and_seed(
        gallery_sidecar,
        query_sidecar,
        method=method,
        seed=seed,
    )
    if final_run is not None and (
        gallery_sidecar.head_checkpoint_sha256 != final_run.checkpoint_sha256
        or query_sidecar.head_checkpoint_sha256 != final_run.checkpoint_sha256
    ):
        raise ValueError("retrieval sidecars differ from the locked checkpoint")
    if mode == "exploratory":
        assert stretch_run_manifest_path is not None
        assert stretch_gate_evidence_path is not None
        exploratory_files = validate_exploratory_run_artifacts(
            protocol,
            stretch_run_manifest_path,
            seed=seed,
            checkpoint_sha256=gallery_sidecar.head_checkpoint_sha256,
            evidence_path=stretch_gate_evidence_path,
        )
        if (
            query_sidecar.head_checkpoint_sha256
            != gallery_sidecar.head_checkpoint_sha256
        ):
            raise ValueError("exploratory features use different checkpoints")
        run_manifest_sha256 = sha256_file(exploratory_files["run_manifest"])
        stretch_gate_evidence_sha256 = sha256_file(
            exploratory_files["stretch_gate_evidence"]
        )
        scientific_inputs.extend(exploratory_files.values())

    _validate_identities(
        protocol=protocol,
        gallery_manifest_path=gallery_manifest_path,
        query_manifest_path=query_manifest_path,
        mode=mode,
    )

    gallery_embeddings, gallery_labels, _ = _load_embeddings(gallery)
    query_embeddings, query_labels, query_ids = _load_embeddings(query)
    evaluation = evaluate_one_shot(
        gallery_embeddings,
        gallery_labels,
        query_embeddings,
        query_labels,
        query_ids=query_ids,
    )
    matrix_key = {
        "method": method,
        "seed": seed,
        "condition": condition,
        "query_definition": query_definition,
    }
    provenance_inputs: list[str | Path] = [
        gallery,
        query,
        sidecar_path_for(gallery),
        sidecar_path_for(query),
        gallery_manifest_path,
        query_manifest_path,
        protocol_path,
    ]
    provenance_inputs.extend(scientific_inputs)
    ended_at = datetime.now(UTC)
    telemetry = capture_runtime_telemetry(
        started_at=started_at,
        ended_at=ended_at,
    )
    payload: dict[str, Any] = {
        "schema_version": 4,
        "mode": mode,
        "protocol_sha256": digest,
        "evaluation_plan_sha256": evaluation_plan_sha256,
        "final_run_set_sha256": final_run_set_sha256,
        "protocol_lock_sha256": protocol_lock_sha256,
        "test_opening_ledger_sha256": test_opening_ledger_sha256,
        "run_manifest_sha256": run_manifest_sha256,
        "checkpoint_sha256": gallery_sidecar.head_checkpoint_sha256,
        "gallery_sidecar_sha256": sha256_file(sidecar_path_for(gallery)),
        "query_sidecar_sha256": sha256_file(sidecar_path_for(query)),
        "source_inventory_manifest_sha256": source_inventory_manifest_sha256,
        "anchor_manifest_sha256": anchor_manifest_sha256,
        "official_query_manifest_sha256": official_query_manifest_sha256,
        "primary_query_manifest_sha256": primary_query_manifest_sha256,
        "stretch_gate_evidence_sha256": stretch_gate_evidence_sha256,
        **matrix_key,
        "gallery_artifact_sha256": gallery_sidecar.artifact_sha256,
        "query_artifact_sha256": query_sidecar.artifact_sha256,
        "gallery_sample_order_sha256": gallery_sidecar.sample_order_sha256,
        "query_sample_order_sha256": query_sidecar.sample_order_sha256,
        "metrics": evaluation.as_dict(),
        "telemetry": telemetry.model_dump(mode="json"),
        "provenance": capture_provenance(
            command=f"evaluate --mode {mode}",
            configuration={
                "mode": mode,
                "protocol_sha256": digest,
                **matrix_key,
            },
            inputs=provenance_inputs,
            started_at=started_at,
            ended_at=ended_at,
        ),
    }
    validated = EvaluationResult.model_validate(payload).model_dump(mode="json")
    write_immutable_json(output_path, validated)
    return validated
