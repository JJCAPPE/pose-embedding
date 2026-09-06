"""Fail-closed metadata contract for cached feature artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal

import numpy as np
import torch
import torch.nn.functional as functional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pose_embed.config import ExperimentConfig, ProtocolConfig
from pose_embed.data.manifest import Split, load_manifest
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file

FeatureRole = Literal["training", "gallery_clean", "query_clean", "query_corrupted"]
FeatureBackend = Literal["fixture", "motionbert"]
ArtifactMethod = Literal[
    "fixture_projection",
    "frozen_encoder_cache",
    "contrastive",
    "supcon",
    "contextual",
    "multi_similarity_with_miner",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sample_order_digest(sample_ids: tuple[str, ...] | list[str]) -> str:
    payload = json.dumps(list(sample_ids), separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def preprocessing_digest(protocol: ProtocolConfig) -> str:
    """Hash only protocol fields that determine encoder input tensors."""
    payload = {
        "dataset": protocol.dataset.model_dump(mode="json"),
        "input_pipeline": protocol.input_pipeline.model_dump(mode="json"),
        "corruptions": protocol.corruptions.model_dump(mode="json"),
    }
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


class FeatureSidecar(BaseModel):
    """Cryptographically bound description of one ordered feature matrix."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[3]
    artifact_type: Literal["feature_cache"]
    backend: FeatureBackend
    method: ArtifactMethod
    training_seed: int | None
    role: FeatureRole
    split: Split
    condition: str = Field(min_length=1)
    scientific_use_allowed: bool
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_order_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preprocessing_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    upstream_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    encoder_checkpoint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    head_checkpoint_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    base_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    base_sidecar_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    array_key: Literal["features", "embeddings"]
    shape: tuple[int, int]
    dtype: str
    sample_ids: tuple[str, ...]
    created_at: datetime
    provenance: dict[str, Any]

    @model_validator(mode="after")
    def semantics_are_consistent(self) -> FeatureSidecar:
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        if self.created_at > datetime.now(UTC):
            raise ValueError("created_at must not be in the future")
        if self.shape[0] != len(self.sample_ids) or min(self.shape) < 1:
            raise ValueError("shape must agree with the non-empty sample order")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("feature sample IDs must be unique")
        if self.backend == "fixture" and self.scientific_use_allowed:
            raise ValueError(
                "fixture artifacts can never be approved for scientific use"
            )
        if self.backend == "motionbert" and not self.scientific_use_allowed:
            raise ValueError("MotionBERT artifacts must be explicitly approved")
        base_method = (
            "fixture_projection"
            if self.backend == "fixture"
            else "frozen_encoder_cache"
        )
        base_methods = {"fixture_projection", "frozen_encoder_cache"}
        if self.method in base_methods and self.method != base_method:
            raise ValueError("pre-head feature method does not match its backend")
        if self.method == base_method and self.array_key != "features":
            raise ValueError("pre-head feature caches must use the features array")
        if self.method not in base_methods and self.array_key != "embeddings":
            raise ValueError(
                "trained retrieval embeddings must use the embeddings array"
            )
        lineage = (
            self.head_checkpoint_sha256,
            self.base_artifact_sha256,
            self.base_sidecar_sha256,
        )
        if self.method in base_methods and any(value is not None for value in lineage):
            raise ValueError("pre-head feature caches cannot claim trained lineage")
        if self.method not in base_methods and any(value is None for value in lineage):
            raise ValueError(
                "trained retrieval embeddings require head and base-cache lineage"
            )
        if self.method not in base_methods:
            inputs = self.provenance.get("inputs")
            if not isinstance(inputs, dict) or not {
                value for value in lineage if value is not None
            } <= set(inputs.values()):
                raise ValueError(
                    "trained retrieval lineage must be bound by provenance inputs"
                )
        training_splits = {"development_train", "final_train"}
        query_splits = {
            "development_validation",
            "novel_query_primary",
            "novel_query_official",
        }
        if self.role == "training" and self.split not in training_splits:
            raise ValueError("training features require an auxiliary training split")
        if self.role == "training":
            if self.training_seed is not None:
                raise ValueError(
                    "pre-head training features cannot have a training seed"
                )
            if self.method != base_method:
                raise ValueError("training features must be a pre-head feature cache")
        elif self.method == base_method:
            if self.training_seed is not None:
                raise ValueError("pre-head feature caches cannot have a training seed")
        elif self.training_seed is None:
            raise ValueError("retrieval embeddings require their training seed")
        if self.role == "gallery_clean" and self.split not in {
            "development_validation",
            "novel_anchor",
        }:
            raise ValueError("clean galleries require validation or novel-anchor split")
        if self.role.startswith("query_") and self.split not in query_splits:
            raise ValueError("query features require a validation or novel-query split")
        if (
            self.role in {"training", "gallery_clean", "query_clean"}
            and self.condition != "clean"
        ):
            raise ValueError(f"{self.role} requires the clean condition")
        if self.role == "query_corrupted" and self.condition == "clean":
            raise ValueError("query_corrupted requires a non-clean condition")
        return self


class StretchGateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["met"]
    evidence_path: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class StretchGateEvidence(BaseModel):
    """Auditable evidence that core work is complete before stretch training."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_run_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    test_opening_ledger_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_at: datetime
    gates: dict[str, StretchGateRecord]

    @model_validator(mode="after")
    def exact_gates_are_present(self) -> StretchGateEvidence:
        expected = {
            "nine_core_checkpoints_verified",
            "full_core_result_matrix_verified",
            "core_figures_reproducible",
            "no_unresolved_core_failures",
        }
        if set(self.gates) != expected:
            raise ValueError("stretch evidence must contain the exact four core gates")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("stretch evidence timestamp must include a timezone")
        if self.recorded_at > datetime.now(UTC):
            raise ValueError("stretch evidence timestamp must not be in the future")
        return self


def sidecar_path_for(artifact_path: str | Path) -> Path:
    artifact = Path(artifact_path)
    return artifact.with_suffix(f"{artifact.suffix}.manifest.json")


def load_feature_sidecar(artifact_path: str | Path) -> FeatureSidecar:
    path = sidecar_path_for(artifact_path)
    try:
        return FeatureSidecar.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"required feature sidecar does not exist: {path}") from exc


def _validate_archive(artifact: Path, sidecar: FeatureSidecar) -> np.ndarray:
    with np.load(artifact, allow_pickle=False) as archive:
        required = {sidecar.array_key, "labels", "sample_ids"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"feature artifact is missing keys: {sorted(missing)}")
        array = np.asarray(archive[sidecar.array_key])
        labels = np.asarray(archive["labels"])
        sample_ids = tuple(np.asarray(archive["sample_ids"]).astype(str))
        projection: np.ndarray | None = None
        if sidecar.backend == "fixture" and sidecar.method == "fixture_projection":
            if "fixture_projection" not in archive.files:
                raise ValueError(
                    "fixture artifact is missing its deterministic projection"
                )
            projection = np.asarray(archive["fixture_projection"])
            if (
                sha256_bytes(projection.tobytes(order="C"))
                != sidecar.encoder_checkpoint_sha256
            ):
                raise ValueError("fixture projection hash does not match the sidecar")
    if tuple(array.shape) != sidecar.shape or str(array.dtype) != sidecar.dtype:
        raise ValueError("feature shape or dtype does not match the sidecar")
    if not np.isfinite(array).all():
        raise ValueError("feature artifact must contain only finite values")
    if projection is not None and not np.isfinite(projection).all():
        raise ValueError("fixture projection must contain only finite values")
    if sample_ids != sidecar.sample_ids:
        raise ValueError("artifact sample order does not match the sidecar")
    if labels.shape != (len(sample_ids),):
        raise ValueError("artifact labels do not align with the sample order")
    expected_labels = np.asarray(
        [int(sample_id[-3:]) for sample_id in sample_ids], dtype=labels.dtype
    )
    if not np.array_equal(labels, expected_labels):
        raise ValueError("artifact labels do not match NTU action IDs")
    return array


def validate_feature_artifact(
    artifact_path: str | Path,
    *,
    protocol: ProtocolConfig,
    manifest_path: str | Path,
    allow_fixture: bool = False,
) -> FeatureSidecar:
    """Validate every hash and semantic boundary before consuming features."""
    artifact = Path(artifact_path)
    if not artifact.is_file():
        raise ValueError(f"feature artifact does not exist: {artifact}")
    sidecar = load_feature_sidecar(artifact)
    if sidecar.protocol_sha256 != protocol_digest(protocol):
        raise ValueError("feature protocol hash does not match the active protocol")
    if sidecar.preprocessing_sha256 != preprocessing_digest(protocol):
        raise ValueError(
            "feature preprocessing hash does not match the active protocol"
        )
    if sha256_file(artifact) != sidecar.artifact_sha256:
        raise ValueError("feature artifact hash does not match the sidecar")
    manifest = Path(manifest_path)
    if sha256_file(manifest) != sidecar.manifest_sha256:
        raise ValueError("feature manifest hash does not match the sidecar")
    records = load_manifest(manifest)
    if any(record.split != sidecar.split for record in records):
        raise ValueError("feature manifest must contain exactly one declared split")
    manifest_order = tuple(record.sample_id for record in records)
    if manifest_order != sidecar.sample_ids:
        raise ValueError("feature sample order does not match the supplied manifest")
    if sample_order_digest(sidecar.sample_ids) != sidecar.sample_order_sha256:
        raise ValueError("feature sample-order hash does not match the sidecar")
    if sidecar.backend == "fixture":
        fixture_source = Path(__file__).with_name("features.py")
        if sha256_file(fixture_source) != sidecar.upstream_sha256:
            raise ValueError("fixture implementation hash does not match the sidecar")
        if not allow_fixture:
            raise ValueError("feature cache is not approved for scientific use")
    else:
        raise ValueError(
            "real MotionBERT feature validation is blocked until its adapter, "
            "checkpoint, and upstream parity checks are implemented"
        )
    artifact_array = _validate_archive(artifact, sidecar)
    if sidecar.head_checkpoint_sha256 is not None:
        provenance_inputs = sidecar.provenance.get("inputs")
        assert isinstance(provenance_inputs, dict)

        def unique_input(expected_sha256: str, label: str) -> Path:
            matches = [
                Path(raw_path)
                for raw_path, observed_sha256 in provenance_inputs.items()
                if observed_sha256 == expected_sha256
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"trained feature provenance must identify one {label}"
                )
            candidate = matches[0]
            try:
                actual_sha256 = sha256_file(candidate)
            except OSError as exc:
                raise ValueError(
                    f"trained feature provenance input is unavailable: {candidate}"
                ) from exc
            if actual_sha256 != expected_sha256:
                raise ValueError(f"trained feature {label} hash mismatch")
            return candidate

        assert sidecar.base_artifact_sha256 is not None
        assert sidecar.base_sidecar_sha256 is not None
        base_artifact = unique_input(
            sidecar.base_artifact_sha256, "base feature artifact"
        )
        base_sidecar_path = unique_input(
            sidecar.base_sidecar_sha256, "base feature sidecar"
        )
        head_checkpoint = unique_input(
            sidecar.head_checkpoint_sha256, "head checkpoint"
        )
        if base_sidecar_path.resolve() != sidecar_path_for(base_artifact).resolve():
            raise ValueError("trained feature base artifact and sidecar do not pair")
        base_sidecar = validate_feature_artifact(
            base_artifact,
            protocol=protocol,
            manifest_path=manifest_path,
            allow_fixture=allow_fixture,
        )
        if (
            base_sidecar.method not in {"fixture_projection", "frozen_encoder_cache"}
            or base_sidecar.encoder_checkpoint_sha256
            != sidecar.encoder_checkpoint_sha256
            or base_sidecar.upstream_sha256 != sidecar.upstream_sha256
            or base_sidecar.preprocessing_sha256 != sidecar.preprocessing_sha256
            or base_sidecar.manifest_sha256 != sidecar.manifest_sha256
            or base_sidecar.sample_order_sha256 != sidecar.sample_order_sha256
            or base_sidecar.role != sidecar.role
            or base_sidecar.split != sidecar.split
            or base_sidecar.condition != sidecar.condition
        ):
            raise ValueError("trained feature differs from its base-cache lineage")
        base_array = _validate_archive(base_artifact, base_sidecar)
        try:
            checkpoint = torch.load(
                head_checkpoint,
                map_location="cpu",
                weights_only=True,
            )
            config = ExperimentConfig.model_validate(checkpoint.get("config"))
            state_dict = checkpoint.get("state_dict")
        except Exception as exc:
            raise ValueError("trained feature head checkpoint is invalid") from exc
        if (
            config.objective != sidecar.method
            or config.seed != sidecar.training_seed
            or config.input_dimension != base_array.shape[1]
            or config.embedding_dimension != artifact_array.shape[1]
            or not isinstance(state_dict, dict)
            or set(state_dict) != {"projection.weight", "projection.bias"}
        ):
            raise ValueError("trained feature head configuration is inconsistent")
        weight = state_dict.get("projection.weight")
        bias = state_dict.get("projection.bias")
        if (
            not isinstance(weight, torch.Tensor)
            or tuple(weight.shape)
            != (config.embedding_dimension, config.input_dimension)
            or not torch.isfinite(weight).all()
            or not isinstance(bias, torch.Tensor)
            or tuple(bias.shape) != (config.embedding_dimension,)
            or not torch.isfinite(bias).all()
        ):
            raise ValueError("trained feature head state is invalid")
        with torch.no_grad():
            expected_embeddings = functional.normalize(
                functional.linear(
                    torch.as_tensor(base_array, dtype=torch.float32),
                    weight.to(dtype=torch.float32),
                    bias.to(dtype=torch.float32),
                ),
                dim=-1,
            ).numpy()
        if not np.array_equal(artifact_array, expected_embeddings):
            raise ValueError(
                "trained embeddings differ from deterministic head application"
            )
    return sidecar


def validate_stretch_gate_evidence(
    evidence_path: str | Path,
    *,
    protocol: ProtocolConfig,
) -> StretchGateEvidence:
    """Verify every gated-stretch claim against a hashed local evidence file."""
    path = Path(evidence_path)
    try:
        evidence = StretchGateEvidence.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise ValueError(f"stretch gate evidence does not exist: {path}") from exc
    if evidence.protocol_sha256 != protocol_digest(protocol):
        raise ValueError("stretch gate evidence belongs to a different protocol")
    for gate, record in evidence.gates.items():
        relative = PurePosixPath(record.evidence_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"stretch gate {gate} uses an unsafe evidence path")
        artifact = path.parent.joinpath(*relative.parts)
        if not artifact.is_file():
            raise ValueError(f"stretch gate {gate} evidence file does not exist")
        if sha256_file(artifact) != record.evidence_sha256:
            raise ValueError(f"stretch gate {gate} evidence hash does not match")
    return evidence
