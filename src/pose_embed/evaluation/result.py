"""Strict schema for immutable retrieval results."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pose_embed.provenance import RuntimeTelemetry

Hash = str


class EvaluationProvenance(BaseModel):
    """Typed, audit-ready provenance captured by the evaluator itself."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    started_at: datetime
    ended_at: datetime
    command: str = Field(min_length=1)
    git_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    git_dirty: bool | None
    dependency_lock_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    configuration: dict[str, Any]
    inputs: dict[str, Hash] = Field(min_length=4)
    environment: dict[str, Any] = Field(min_length=1)

    @model_validator(mode="after")
    def timestamps_and_hashes_are_valid(self) -> EvaluationProvenance:
        for timestamp in (self.started_at, self.ended_at):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("evaluation provenance timestamps require a timezone")
        if self.started_at > self.ended_at or self.ended_at > datetime.now(UTC):
            raise ValueError("evaluation provenance timestamps are invalid")
        if any(
            len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
            for value in self.inputs.values()
        ):
            raise ValueError(
                "evaluation provenance input hashes must be lowercase SHA-256"
            )
        return self


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_id: str = Field(min_length=1)
    label: int
    rank: int = Field(gt=0)
    predicted_label: int
    top1_correct: bool

    @model_validator(mode="after")
    def correctness_matches_rank(self) -> QueryResult:
        if self.top1_correct != (self.rank == 1):
            raise ValueError("per-query top1 flag must equal rank == 1")
        return self


class ResultMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    top1: float = Field(ge=0, le=1)
    mrr: float = Field(ge=0, le=1)
    r_at_5: float = Field(ge=0, le=1)
    query_count: int = Field(gt=0)
    gallery_count: int = Field(gt=0)
    per_query: tuple[QueryResult, ...]

    @model_validator(mode="after")
    def aggregates_match_per_query_rows(self) -> ResultMetrics:
        if self.query_count != len(self.per_query):
            raise ValueError("query_count must equal the per-query result count")
        if len({row.sample_id for row in self.per_query}) != self.query_count:
            raise ValueError("per-query sample IDs must be unique")
        if any(row.rank > self.gallery_count for row in self.per_query):
            raise ValueError("per-query rank exceeds gallery count")
        expected = {
            "top1": sum(row.rank == 1 for row in self.per_query) / self.query_count,
            "mrr": sum(1.0 / row.rank for row in self.per_query) / self.query_count,
            "r_at_5": sum(row.rank <= 5 for row in self.per_query) / self.query_count,
        }
        for name, value in expected.items():
            if not math.isclose(getattr(self, name), value, rel_tol=0, abs_tol=1e-12):
                raise ValueError(f"{name} does not match the per-query ranks")
        return self


class EvaluationResult(BaseModel):
    """One unique development or protocol-authorized final matrix cell."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[4]
    mode: Literal["development", "final", "exploratory"]
    protocol_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_plan_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    final_run_set_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    protocol_lock_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    test_opening_ledger_sha256: Hash | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    run_manifest_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    checkpoint_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    gallery_sidecar_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    query_sidecar_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    source_inventory_manifest_sha256: Hash | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    anchor_manifest_sha256: Hash | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    official_query_manifest_sha256: Hash | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    primary_query_manifest_sha256: Hash | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    stretch_gate_evidence_sha256: Hash | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    method: Literal[
        "contrastive", "supcon", "contextual", "multi_similarity_with_miner"
    ]
    seed: int
    condition: str = Field(min_length=1)
    query_definition: Literal["development", "primary", "official"]
    gallery_artifact_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    query_artifact_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    gallery_sample_order_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    query_sample_order_sha256: Hash = Field(pattern=r"^[0-9a-f]{64}$")
    metrics: ResultMetrics
    telemetry: RuntimeTelemetry
    provenance: EvaluationProvenance

    @model_validator(mode="after")
    def authorization_fields_match_mode(self) -> EvaluationResult:
        elapsed = (
            self.provenance.ended_at - self.provenance.started_at
        ).total_seconds()
        if not math.isclose(
            self.telemetry.wall_time_seconds,
            elapsed,
            rel_tol=0,
            abs_tol=1e-6,
        ):
            raise ValueError("evaluation telemetry differs from provenance timestamps")
        final_fields = (
            self.evaluation_plan_sha256,
            self.final_run_set_sha256,
            self.protocol_lock_sha256,
            self.test_opening_ledger_sha256,
            self.run_manifest_sha256,
            self.source_inventory_manifest_sha256,
            self.anchor_manifest_sha256,
            self.official_query_manifest_sha256,
            self.primary_query_manifest_sha256,
        )
        expected_configuration = {
            "mode": self.mode,
            "protocol_sha256": self.protocol_sha256,
            "method": self.method,
            "seed": self.seed,
            "condition": self.condition,
            "query_definition": self.query_definition,
        }
        if self.provenance.command != f"evaluate --mode {self.mode}":
            raise ValueError("evaluation provenance command does not match result mode")
        if self.provenance.configuration != expected_configuration:
            raise ValueError(
                "evaluation provenance configuration does not match result"
            )
        required_input_hashes = {
            self.gallery_artifact_sha256,
            self.query_artifact_sha256,
            self.gallery_sidecar_sha256,
            self.query_sidecar_sha256,
        }
        if not required_input_hashes <= set(self.provenance.inputs.values()):
            raise ValueError("evaluation provenance does not bind feature artifacts")
        if self.mode == "development":
            if self.query_definition != "development":
                raise ValueError("development result requires development queries")
            if any(value is not None for value in final_fields):
                raise ValueError(
                    "development result cannot claim final-lock provenance"
                )
            if self.stretch_gate_evidence_sha256 is not None:
                raise ValueError(
                    "development result cannot claim stretch authorization"
                )
            return self
        if self.query_definition not in {"primary", "official"}:
            raise ValueError("locked result requires primary or official queries")
        if any(value is None for value in final_fields):
            raise ValueError("final result requires complete lock and run provenance")
        if self.mode == "final":
            if self.method == "multi_similarity_with_miner":
                raise ValueError(
                    "core final mode excludes exploratory Multi-Similarity rows"
                )
            if self.stretch_gate_evidence_sha256 is not None:
                raise ValueError("core final result cannot claim stretch authorization")
        else:
            if self.method != "multi_similarity_with_miner":
                raise ValueError(
                    "exploratory mode is reserved for Multi-Similarity stretch rows"
                )
            if self.stretch_gate_evidence_sha256 is None:
                raise ValueError(
                    "exploratory result requires stretch-gate authorization"
                )
        assert self.protocol_lock_sha256 is not None
        assert self.test_opening_ledger_sha256 is not None
        assert self.run_manifest_sha256 is not None
        assert self.source_inventory_manifest_sha256 is not None
        assert self.anchor_manifest_sha256 is not None
        assert self.official_query_manifest_sha256 is not None
        assert self.primary_query_manifest_sha256 is not None
        required_final_hashes = {
            self.protocol_lock_sha256,
            self.test_opening_ledger_sha256,
            self.run_manifest_sha256,
            self.source_inventory_manifest_sha256,
            self.anchor_manifest_sha256,
            self.official_query_manifest_sha256,
            self.primary_query_manifest_sha256,
        }
        if self.stretch_gate_evidence_sha256 is not None:
            required_final_hashes.add(self.stretch_gate_evidence_sha256)
        if not required_final_hashes <= set(self.provenance.inputs.values()):
            raise ValueError("final provenance does not bind locked scientific inputs")
        return self
