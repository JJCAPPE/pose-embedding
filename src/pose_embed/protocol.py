"""Protocol hashing and lock verification."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pose_embed.config import (
    ExperimentConfig,
    ProtocolConfig,
    canonical_json,
    experiment_hyperparameters_digest,
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)


class ProtocolLock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_id: str
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_inventory_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    official_query_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    primary_query_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_run_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    locked_at: datetime
    advisor_approved_by: str = Field(min_length=1)
    advisor_approved_at: datetime

    @field_validator("locked_at", "advisor_approved_at")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("lock timestamps must include an RFC 3339 timezone")
        return value


class LockedManifest(BaseModel):
    """Exact bytes and ordered identity set for one final-evaluation manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_count: int = Field(gt=0)
    sample_ids: tuple[str, ...]

    @model_validator(mode="after")
    def path_and_identities_are_exact(self) -> LockedManifest:
        path = PurePosixPath(self.relative_path)
        if (
            path.is_absolute()
            or self.relative_path != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("locked manifest path must be normalized and relative")
        if self.sample_count != len(self.sample_ids):
            raise ValueError("locked manifest count must equal its ordered sample IDs")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("locked manifest sample IDs must be unique")
        from pose_embed.data.ntu import parse_ntu_sample_id

        if any(
            parse_ntu_sample_id(value).sample_id != value for value in self.sample_ids
        ):
            raise ValueError("locked manifest sample IDs must be canonical NTU IDs")
        return self


class EvaluationPlan(BaseModel):
    """The complete, versioned matrix authorized for the one-time test opening."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    status: Literal["template", "locked"]
    plan_id: Literal["final-evaluation-v1"]
    methods: tuple[Literal["contrastive", "supcon", "contextual"], ...]
    seeds: tuple[int, ...]
    conditions: tuple[str, ...]
    query_definitions: tuple[Literal["primary", "official"], ...]
    metrics: tuple[Literal["top1", "mrr", "r_at_5"], ...]
    expected_rows: int = Field(gt=0)
    gallery_role: Literal["gallery_clean"]
    gallery_split: Literal["novel_anchor"]
    query_roles: tuple[Literal["query_clean", "query_corrupted"], ...]
    query_splits: tuple[Literal["novel_query_primary", "novel_query_official"], ...]
    source_inventory_manifest: LockedManifest | None
    anchor_manifest: LockedManifest | None
    official_query_manifest: LockedManifest | None
    primary_query_manifest: LockedManifest | None

    @model_validator(mode="after")
    def matrix_is_exact(self) -> EvaluationPlan:
        expected_conditions = (
            "clean",
            "coordinate_jitter:0.01",
            "coordinate_jitter:0.025",
            "coordinate_jitter:0.05",
            "joint_mask:3",
            "joint_mask:6",
            "joint_mask:8",
            "frame_mask:10",
            "frame_mask:25",
            "frame_mask:40",
        )
        if self.methods != ("contrastive", "supcon", "contextual"):
            raise ValueError("evaluation methods differ from the three core methods")
        if len(self.seeds) != 3 or len(set(self.seeds)) != 3:
            raise ValueError("evaluation plan requires three distinct paired seeds")
        if self.conditions != expected_conditions:
            raise ValueError("evaluation conditions differ from the locked ten cells")
        if self.query_definitions != ("primary", "official"):
            raise ValueError("both primary and official query definitions are required")
        if self.metrics != ("top1", "mrr", "r_at_5"):
            raise ValueError("evaluation metrics differ from protocol v1")
        matrix_size = (
            len(self.methods)
            * len(self.seeds)
            * len(self.conditions)
            * len(self.query_definitions)
        )
        if self.expected_rows != matrix_size:
            raise ValueError("expected_rows does not equal the declared result matrix")
        if self.query_roles != ("query_clean", "query_corrupted"):
            raise ValueError("evaluation query roles are incomplete")
        if self.query_splits != (
            "novel_query_primary",
            "novel_query_official",
        ):
            raise ValueError("evaluation query splits are incomplete")
        manifests = (
            self.source_inventory_manifest,
            self.anchor_manifest,
            self.official_query_manifest,
            self.primary_query_manifest,
        )
        if self.status == "template":
            if any(manifest is not None for manifest in manifests):
                raise ValueError("template evaluation plans cannot bind real manifests")
            return self
        if any(manifest is None for manifest in manifests):
            raise ValueError("locked evaluation plans require all four exact manifests")
        source, anchors, official, primary = manifests
        assert source is not None
        assert anchors is not None
        assert official is not None
        assert primary is not None
        if anchors.sample_count != 20:
            raise ValueError("locked anchor manifest requires exactly 20 samples")
        anchor_ids = set(anchors.sample_ids)
        official_ids = set(official.sample_ids)
        primary_ids = set(primary.sample_ids)
        if anchor_ids & official_ids:
            raise ValueError("official queries must exclude exact anchor samples")
        if not primary_ids <= official_ids:
            raise ValueError("primary queries must be a subset of official queries")
        if not anchor_ids | official_ids <= set(source.sample_ids):
            raise ValueError(
                "source inventory must contain anchors and official queries"
            )
        from pose_embed.data.ntu import parse_ntu_sample_id

        anchor_performances = {
            parse_ntu_sample_id(sample_id).performance_id for sample_id in anchor_ids
        }
        expected_primary = {
            sample_id
            for sample_id in official_ids
            if parse_ntu_sample_id(sample_id).performance_id not in anchor_performances
        }
        if primary_ids != expected_primary:
            raise ValueError(
                "primary queries must exactly exclude synchronized anchor performances"
            )
        return self


class SelectedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal["contrastive", "supcon", "contextual"]
    config_id: str = Field(min_length=1)
    hyperparameters_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FinalRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal[
        "contrastive", "supcon", "contextual", "multi_similarity_with_miner"
    ]
    seed: int
    config_relative_path: str = Field(min_length=1)
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_manifest_relative_path: str = Field(min_length=1)
    run_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint_relative_path: str = Field(min_length=1)
    checkpoint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_plan_relative_path: str = Field(min_length=1)
    batch_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    metrics_relative_path: str = Field(min_length=1)
    metrics_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attempt_relative_path: str = Field(min_length=1)
    attempt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    outcome_relative_path: str = Field(min_length=1)
    outcome_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    initialization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator(
        "config_relative_path",
        "run_manifest_relative_path",
        "checkpoint_relative_path",
        "batch_plan_relative_path",
        "metrics_relative_path",
        "attempt_relative_path",
        "outcome_relative_path",
    )
    @classmethod
    def run_path_is_relative(cls, value: str) -> str:
        _validate_relative_path(value, label="final run artifact")
        return value


class CodeHashes(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    training: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation: str = Field(pattern=r"^[0-9a-f]{64}$")
    sampler: str = Field(pattern=r"^[0-9a-f]{64}$")
    corruptions: str = Field(pattern=r"^[0-9a-f]{64}$")
    analysis: str = Field(pattern=r"^[0-9a-f]{64}$")


class FinalRunSet(BaseModel):
    """The immutable, result-blind core run set authorized for final evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    run_set_id: Literal["final-core-run-set-v1"]
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection_locked_at: datetime
    locked_at: datetime
    selected_configs: tuple[SelectedConfig, ...]
    runs: tuple[FinalRun, ...]
    code_sha256: CodeHashes

    @model_validator(mode="after")
    def run_matrix_is_complete_and_paired(self) -> FinalRunSet:
        for timestamp in (self.selection_locked_at, self.locked_at):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("run-set timestamps must include a timezone")
        if self.selection_locked_at > self.locked_at:
            raise ValueError("run-set selection must be locked before finalization")
        expected_methods = ("contrastive", "supcon", "contextual")
        selected_methods = tuple(item.method for item in self.selected_configs)
        if selected_methods != expected_methods:
            raise ValueError(
                "run set requires one ordered selected core config per method"
            )
        seeds = {run.seed for run in self.runs}
        if len(self.runs) != 9 or len(seeds) != 3:
            raise ValueError("final run set requires exactly nine runs and three seeds")
        expected_cells = {
            (method, seed) for method in expected_methods for seed in seeds
        }
        observed_cells = {(run.method, run.seed) for run in self.runs}
        if observed_cells != expected_cells or len(observed_cells) != len(self.runs):
            raise ValueError(
                "final run set must contain each method/seed cell exactly once"
            )
        if len({item.config_id for item in self.selected_configs}) != 3:
            raise ValueError("selected core config IDs must be unique")
        for seed in seeds:
            paired = [run for run in self.runs if run.seed == seed]
            if len({run.batch_plan_sha256 for run in paired}) != 1:
                raise ValueError("paired methods must share the same batch-plan hash")
            if len({run.initialization_sha256 for run in paired}) != 1:
                raise ValueError(
                    "paired methods must share the same initialization hash"
                )
        return self


@dataclass(frozen=True)
class ScientificPaths:
    root: Path
    protocol_lock: Path
    evaluation_plan: Path
    final_run_set: Path
    test_opening_ledger: Path
    stretch_gate_evidence: Path


@dataclass(frozen=True)
class EvaluationManifestValidation:
    """Bound manifests plus one deterministic snapshot of every source file."""

    paths: dict[str, Path]
    source_file_count: int
    source_files_sha256: str
    source_files_verified: bool


def _validate_relative_path(value: str, *, label: str) -> None:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{label} path must be normalized and relative")


def resolve_scientific_paths(protocol: ProtocolConfig) -> ScientificPaths:
    """Resolve every scientific lock from one non-overridable artifact root."""
    variable = protocol.test_access.artifact_root_environment
    raw_root = os.environ.get(variable)
    if not raw_root:
        raise ValueError(f"{variable} is required for scientific operations")
    root = Path(raw_root)
    if not root.is_absolute():
        raise ValueError(f"{variable} must be an absolute path")
    root = root.resolve()

    def below_root(relative: str) -> Path:
        _validate_relative_path(relative, label="scientific artifact")
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root):
            raise ValueError("scientific artifact path escapes the artifact root")
        return candidate

    access = protocol.test_access
    return ScientificPaths(
        root=root,
        protocol_lock=below_root(access.protocol_lock_relative_path),
        evaluation_plan=below_root(access.evaluation_plan_relative_path),
        final_run_set=below_root(access.final_run_set_relative_path),
        test_opening_ledger=below_root(access.opening_ledger_relative_path),
        stretch_gate_evidence=below_root(access.stretch_gate_evidence_relative_path),
    )


def _locked_path(root: Path, relative_path: str) -> Path:
    _validate_relative_path(relative_path, label="locked artifact")
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("locked artifact path escapes the artifact root")
    return candidate


def validate_locked_manifest(
    binding: LockedManifest,
    path: str | Path,
    *,
    expected_split: str | None = None,
) -> tuple[str, ...]:
    """Require exact manifest bytes, row count, order, and optional split."""
    from pose_embed.data import load_manifest
    from pose_embed.provenance import sha256_file

    manifest_path = Path(path)
    if sha256_file(manifest_path) != binding.sha256:
        raise ValueError(f"manifest hash differs from locked plan: {manifest_path}")
    records = load_manifest(manifest_path)
    sample_ids = tuple(record.sample_id for record in records)
    if len(records) != binding.sample_count or sample_ids != binding.sample_ids:
        raise ValueError(
            f"manifest identities/count differ from locked plan: {manifest_path}"
        )
    if expected_split is not None and any(
        record.split != expected_split for record in records
    ):
        raise ValueError(
            f"manifest contains rows outside locked split {expected_split}: "
            f"{manifest_path}"
        )
    return sample_ids


def validate_evaluation_manifests(
    protocol: ProtocolConfig,
    plan: EvaluationPlan,
    artifact_root: str | Path,
    *,
    data_root: str | Path | None = None,
    check_source_files: bool = True,
) -> EvaluationManifestValidation:
    """Validate the complete physical inventory and every final subset."""
    if plan.status != "locked":
        raise ValueError("final evaluation requires a populated locked plan")
    bindings = {
        "source_inventory": plan.source_inventory_manifest,
        "anchor": plan.anchor_manifest,
        "official": plan.official_query_manifest,
        "primary": plan.primary_query_manifest,
    }
    assert all(binding is not None for binding in bindings.values())
    source_binding = bindings["source_inventory"]
    assert source_binding is not None
    expected_source_count = protocol.dataset.expected_source_sample_count
    if source_binding.sample_count != expected_source_count:
        raise ValueError(
            f"source inventory must contain exactly {expected_source_count} "
            "NTU RGB+D 120 samples"
        )

    root = Path(artifact_root).resolve()
    paths: dict[str, Path] = {}
    expected_splits = {
        "source_inventory": None,
        "anchor": "novel_anchor",
        "official": "novel_query_official",
        "primary": "novel_query_primary",
    }
    for name, optional_binding in bindings.items():
        assert optional_binding is not None
        path = _locked_path(root, optional_binding.relative_path)
        validate_locked_manifest(
            optional_binding,
            path,
            expected_split=expected_splits[name],
        )
        paths[name] = path

    from pose_embed.data import load_manifest, verify_manifests
    from pose_embed.data.ntu import parse_ntu_sample_id

    source_records = load_manifest(paths["source_inventory"])
    verify_manifests(source_records, protocol)
    if {record.ntu.action for record in source_records} != set(range(1, 121)):
        raise ValueError("source inventory must cover all 120 dataset actions")
    if any(
        record.relative_path is None or record.sha256 is None
        for record in source_records
    ):
        raise ValueError("source inventory requires one path and checksum per sample")
    if len({record.relative_path for record in source_records}) != len(source_records):
        raise ValueError("source inventory paths must be unique")

    anchors = load_manifest(paths["anchor"])
    official = load_manifest(paths["official"])
    primary = load_manifest(paths["primary"])
    for records in (anchors, official, primary):
        verify_manifests(records, protocol)
    verify_manifests([*anchors, *official, *primary], protocol)

    expected_anchor_ids = protocol.dataset.official_one_shot_exemplars
    if tuple(record.sample_id for record in anchors) != expected_anchor_ids:
        raise ValueError("anchor manifest differs from the official one-shot exemplars")
    anchor_ids = set(expected_anchor_ids)
    novel_actions = set(protocol.dataset.novel_actions)
    source_novel = [
        record for record in source_records if record.ntu.action in novel_actions
    ]
    expected_official_ids = tuple(
        record.sample_id
        for record in source_novel
        if record.sample_id not in anchor_ids
    )
    if tuple(record.sample_id for record in official) != expected_official_ids:
        raise ValueError(
            "official queries must contain every non-anchor novel sample in "
            "the complete source inventory"
        )
    anchor_performances = {record.ntu.performance_id for record in anchors}
    expected_primary_ids = tuple(
        record.sample_id
        for record in official
        if record.ntu.performance_id not in anchor_performances
    )
    if tuple(record.sample_id for record in primary) != expected_primary_ids:
        raise ValueError(
            "primary queries must exactly exclude synchronized anchor performances"
        )

    source_by_id = {record.sample_id: record for record in source_records}
    for record in anchors:
        source = source_by_id.get(record.sample_id)
        if source is None or source.split != "novel_anchor":
            raise ValueError("source inventory does not identify every official anchor")
    for record in official:
        source = source_by_id.get(record.sample_id)
        if source is None or source.split != "novel_query_official":
            raise ValueError("source inventory does not identify every official query")
    for records in (anchors, official, primary):
        for record in records:
            source = source_by_id[record.sample_id]
            if (
                record.relative_path != source.relative_path
                or record.sha256 != source.sha256
            ):
                raise ValueError(
                    "evaluation subset path/checksum differs from source inventory"
                )

    inventory_payload = [
        {
            "sample_id": record.sample_id,
            "relative_path": record.relative_path,
            "sha256": record.sha256,
        }
        for record in source_records
    ]
    source_files_sha256 = hashlib.sha256(
        json.dumps(
            inventory_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    if check_source_files:
        raw_data_root = data_root or os.environ.get("POSE_EMBED_DATA_ROOT")
        if raw_data_root is None:
            raise ValueError(
                "POSE_EMBED_DATA_ROOT is required to verify the source inventory"
            )
        resolved_data_root = Path(raw_data_root)
        if not resolved_data_root.is_absolute():
            raise ValueError("POSE_EMBED_DATA_ROOT must be an absolute path")
        resolved_data_root = resolved_data_root.resolve()
        verify_manifests(
            source_records,
            protocol,
            data_root=resolved_data_root,
            check_files=True,
        )
        discovered: dict[str, str] = {}
        for candidate in resolved_data_root.rglob("*"):
            if not candidate.is_file():
                continue
            try:
                sample = parse_ntu_sample_id(candidate.name)
            except ValueError:
                continue
            resolved_candidate = candidate.resolve()
            try:
                relative_path = resolved_candidate.relative_to(
                    resolved_data_root
                ).as_posix()
            except ValueError as exc:
                raise ValueError(
                    "source inventory data path escapes data root"
                ) from exc
            previous = discovered.setdefault(sample.sample_id, relative_path)
            if previous != relative_path:
                raise ValueError(
                    f"multiple physical files identify source sample {sample.sample_id}"
                )
        declared = {record.sample_id: record.relative_path for record in source_records}
        if discovered != declared:
            missing = sorted(set(discovered) - set(declared))
            extra = sorted(set(declared) - set(discovered))
            mismatched = sorted(
                sample_id
                for sample_id in set(discovered) & set(declared)
                if discovered[sample_id] != declared[sample_id]
            )
            raise ValueError(
                "source inventory is not a complete filesystem-derived inventory; "
                f"unlisted={missing[:10]}, absent={extra[:10]}, "
                f"path_mismatches={mismatched[:10]}"
            )

    return EvaluationManifestValidation(
        paths=paths,
        source_file_count=len(source_records),
        source_files_sha256=source_files_sha256,
        source_files_verified=check_source_files,
    )


def final_run_for(run_set: FinalRunSet, method: str, seed: int) -> FinalRun:
    matches = [run for run in run_set.runs if run.method == method and run.seed == seed]
    if len(matches) != 1:
        raise ValueError("method/seed is absent from the locked final run set")
    return matches[0]


SCIENTIFIC_CODE_PATHS: dict[str, tuple[str, ...]] = {
    "training": (
        "src/pose_embed/__init__.py",
        "src/pose_embed/artifacts.py",
        "src/pose_embed/cli.py",
        "src/pose_embed/config.py",
        "src/pose_embed/features.py",
        "src/pose_embed/provenance.py",
        "src/pose_embed/training/__init__.py",
        "src/pose_embed/training/runner.py",
        "src/pose_embed/losses/__init__.py",
        "src/pose_embed/losses/contextual.py",
        "src/pose_embed/losses/multi_similarity.py",
        "src/pose_embed/losses/pairwise.py",
        "src/pose_embed/models/__init__.py",
        "src/pose_embed/models/action_head.py",
    ),
    "evaluation": (
        "src/pose_embed/evaluation/__init__.py",
        "src/pose_embed/evaluation/runner.py",
        "src/pose_embed/evaluation/metrics.py",
        "src/pose_embed/evaluation/result.py",
        "src/pose_embed/protocol.py",
        "src/pose_embed/test_access.py",
        "src/pose_embed/data/__init__.py",
        "src/pose_embed/data/manifest.py",
        "src/pose_embed/data/ntu.py",
    ),
    "sampler": ("src/pose_embed/training/sampler.py",),
    "corruptions": (
        "src/pose_embed/corruptions/__init__.py",
        "src/pose_embed/corruptions/pose.py",
    ),
    "analysis": (
        "src/pose_embed/evaluation/analysis.py",
        "src/pose_embed/report.py",
    ),
}


def current_code_hashes(repository_root: str | Path | None = None) -> CodeHashes:
    """Hash every package module that can affect scientific identity or output."""
    root = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    hashes: dict[str, str] = {}
    for component, relative_paths in SCIENTIFIC_CODE_PATHS.items():
        digest = hashlib.sha256()
        for relative_path in relative_paths:
            path = root / relative_path
            try:
                content = path.read_bytes()
            except FileNotFoundError as exc:
                raise ValueError(
                    f"cannot hash missing scientific code file: {path}"
                ) from exc
            digest.update(relative_path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(content)
            digest.update(b"\0")
        hashes[component] = digest.hexdigest()
    return CodeHashes.model_validate(hashes)


def _validate_head_checkpoint(
    path: Path,
    config: ExperimentConfig,
    *,
    initialization_sha256: str,
) -> None:
    try:
        import torch

        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise ValueError("head checkpoint is not a readable safe checkpoint") from exc
    expected_experiment = config.model_dump(mode="json")
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("config") != expected_experiment
    ):
        raise ValueError("head checkpoint configuration mismatch")
    state_dict = checkpoint.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError("head checkpoint is missing its state dictionary")
    weight = state_dict.get("projection.weight")
    bias = state_dict.get("projection.bias")
    expected_weight_shape = (config.embedding_dimension, config.input_dimension)
    if (
        not isinstance(weight, torch.Tensor)
        or tuple(weight.shape) != expected_weight_shape
        or not torch.isfinite(weight).all()
        or not isinstance(bias, torch.Tensor)
        or tuple(bias.shape) != (config.embedding_dimension,)
        or not torch.isfinite(bias).all()
    ):
        raise ValueError("head checkpoint state is invalid")
    from pose_embed.training.runner import NormalizedLinearHead, _state_dict_digest

    with torch.random.fork_rng():
        torch.manual_seed(config.seed)
        initialized = NormalizedLinearHead(
            config.input_dimension, config.embedding_dimension
        )
    if _state_dict_digest(initialized) != initialization_sha256:
        raise ValueError("locked initialization hash cannot be reproduced")
    final_head = NormalizedLinearHead(
        config.input_dimension, config.embedding_dimension
    )
    final_head.load_state_dict(state_dict, strict=True)
    if _state_dict_digest(final_head) == initialization_sha256:
        raise ValueError("final checkpoint is still the untrained initialization")


def _validate_batch_plan(
    path: Path,
    config: ExperimentConfig,
    *,
    labels: list[int],
    sample_order_sha256: str,
) -> list[str]:
    try:
        batch_plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("batch plan is invalid JSON") from exc
    expected_keys = {
        "schema_version",
        "seed",
        "classes_per_batch",
        "samples_per_class",
        "sample_order_sha256",
        "epoch_sha256",
        "epochs",
    }
    if set(batch_plan) != expected_keys or (
        batch_plan.get("schema_version") != 1
        or batch_plan.get("seed") != config.seed
        or batch_plan.get("classes_per_batch") != config.classes_per_batch
        or batch_plan.get("samples_per_class") != config.samples_per_class
        or batch_plan.get("sample_order_sha256") != sample_order_sha256
        or len(batch_plan.get("epochs", [])) != config.epochs
        or len(batch_plan.get("epoch_sha256", [])) != config.epochs
    ):
        raise ValueError("batch plan differs from the run configuration")
    from pose_embed.training.runner import _json_digest
    from pose_embed.training.sampler import BalancedBatchSampler

    expected_epochs = [
        [
            list(batch)
            for batch in BalancedBatchSampler(
                labels,
                classes_per_batch=config.classes_per_batch,
                samples_per_class=config.samples_per_class,
                seed=config.seed + epoch,
            )
        ]
        for epoch in range(config.epochs)
    ]
    expected_hashes = [_json_digest(epoch) for epoch in expected_epochs]
    if (
        batch_plan["epochs"] != expected_epochs
        or batch_plan["epoch_sha256"] != expected_hashes
    ):
        raise ValueError("batch plan is not the deterministic balanced P x K plan")
    return expected_hashes


def _validate_training_run_artifacts(
    run_set: FinalRunSet,
    run: FinalRun,
    artifact_root: str | Path,
    *,
    protocol: ProtocolConfig,
    resolved_files: dict[str, Path] | None = None,
    not_before: datetime | None = None,
    not_after: datetime | None = None,
    required_input_sha256: str | None = None,
    require_core_selection: bool = True,
) -> dict[str, Path]:
    """Verify complete training evidence for a core or exploratory run."""
    from pose_embed.provenance import sha256_file

    root = Path(artifact_root).resolve()
    if run_set.protocol_sha256 != protocol_digest(protocol):
        raise ValueError("final run set belongs to a different protocol")
    if run_set.code_sha256 != current_code_hashes():
        raise ValueError("scientific code changed after the final run set was locked")
    selected = next(
        (config for config in run_set.selected_configs if config.method == run.method),
        None,
    )
    if require_core_selection and (selected is None or run not in run_set.runs):
        raise ValueError("final run is absent from the locked core run set")
    files = resolved_files or {
        "config": _locked_path(root, run.config_relative_path),
        "run_manifest": _locked_path(root, run.run_manifest_relative_path),
        "checkpoint": _locked_path(root, run.checkpoint_relative_path),
        "batch_plan": _locked_path(root, run.batch_plan_relative_path),
        "metrics": _locked_path(root, run.metrics_relative_path),
        "attempt": _locked_path(root, run.attempt_relative_path),
        "outcome": _locked_path(root, run.outcome_relative_path),
    }
    expected_hashes = {
        "config": run.config_sha256,
        "run_manifest": run.run_manifest_sha256,
        "checkpoint": run.checkpoint_sha256,
        "batch_plan": run.batch_plan_sha256,
        "metrics": run.metrics_sha256,
        "attempt": run.attempt_sha256,
        "outcome": run.outcome_sha256,
    }
    for name, path in files.items():
        if sha256_file(path) != expected_hashes[name]:
            raise ValueError(
                f"locked final {name} hash mismatch for {run.method}/{run.seed}"
            )

    config = load_experiment(files["config"])
    validate_experiment_against_protocol(config, protocol)
    if (config.objective, config.seed) != (run.method, run.seed):
        raise ValueError("locked final config method/seed mismatch")
    if selected is not None and (
        experiment_hyperparameters_digest(config) != selected.hyperparameters_sha256
    ):
        raise ValueError(
            "locked final config differs from the selected method hyperparameters"
        )

    def load_json_object(name: str) -> dict[str, object]:
        try:
            payload = json.loads(files[name].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"locked final {name} is invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"locked final {name} must be a JSON object")
        return payload

    manifest = load_json_object("run_manifest")
    expected_manifest_keys = {
        "schema_version",
        "started_at",
        "ended_at",
        "command",
        "git_sha",
        "git_dirty",
        "dependency_lock_sha256",
        "configuration",
        "inputs",
        "environment",
        "scientific_use_allowed",
        "protocol_sha256",
        "feature_sidecar",
        "initialization_sha256",
        "batch_plan_sha256",
        "epoch_batch_plan_sha256",
        "telemetry",
        "outputs",
    }
    if set(manifest) != expected_manifest_keys:
        raise ValueError("locked final run manifest has incomplete provenance")
    from pose_embed.artifacts import FeatureSidecar
    from pose_embed.evaluation.result import EvaluationProvenance
    from pose_embed.provenance import RuntimeTelemetry, sha256_file

    provenance_fields = EvaluationProvenance.model_fields
    provenance = EvaluationProvenance.model_validate(
        {name: manifest[name] for name in provenance_fields}
    )
    telemetry = RuntimeTelemetry.model_validate(manifest.get("telemetry"))
    repository_root = Path(__file__).resolve().parents[2]
    expected_environment_keys = {
        "python",
        "platform",
        "torch",
        "cuda_available",
        "cuda_version",
        "device_count",
        "devices",
        "dependencies",
    }
    if (
        provenance.command != "train"
        or provenance.git_sha is None
        or provenance.git_dirty is not False
        or provenance.dependency_lock_sha256 != sha256_file(repository_root / "uv.lock")
        or provenance.started_at < (not_before or run_set.selection_locked_at)
        or provenance.ended_at > (not_after or run_set.locked_at)
        or abs(
            telemetry.wall_time_seconds
            - (provenance.ended_at - provenance.started_at).total_seconds()
        )
        > 1e-6
        or not expected_environment_keys <= set(provenance.environment)
    ):
        raise ValueError("locked final run provenance is not release-grade")
    expected_experiment = config.model_dump(mode="json")
    expected_configuration_keys = {"experiment", "device", "attempt_sha256"}
    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict) or set(configuration) != (
        expected_configuration_keys
    ):
        raise ValueError("locked final run configuration provenance is incomplete")
    experiment = configuration.get("experiment")
    outputs = manifest.get("outputs", {})
    if experiment != expected_experiment:
        raise ValueError("locked final run manifest configuration mismatch")
    if manifest.get("protocol_sha256") != run_set.protocol_sha256:
        raise ValueError("locked final run manifest protocol mismatch")
    if manifest.get("scientific_use_allowed") is not True:
        raise ValueError("locked final run manifest is not approved for scientific use")
    if configuration.get("attempt_sha256") != run.attempt_sha256:
        raise ValueError("locked final run manifest does not bind its attempt")
    inputs = provenance.inputs
    for raw_path, expected_sha256 in inputs.items():
        try:
            actual_sha256 = sha256_file(raw_path)
        except OSError as exc:
            raise ValueError(
                f"locked final training input is unavailable: {raw_path}"
            ) from exc
        if actual_sha256 != expected_sha256:
            raise ValueError(f"locked final training input hash mismatch: {raw_path}")
    if run.config_sha256 not in inputs.values():
        raise ValueError("locked final run manifest does not bind its configuration")
    if (
        required_input_sha256 is not None
        and required_input_sha256 not in inputs.values()
    ):
        raise ValueError("training run does not bind its required authorization input")
    if not isinstance(outputs, dict) or outputs != {
        "checkpoint": run.checkpoint_sha256,
        "metrics": run.metrics_sha256,
        "batch_plan": run.batch_plan_sha256,
    }:
        raise ValueError("locked final run output hashes are incomplete")
    if manifest.get("initialization_sha256") != run.initialization_sha256:
        raise ValueError("locked final run manifest initialization hash mismatch")
    sidecar = FeatureSidecar.model_validate(manifest.get("feature_sidecar"))
    if (
        sidecar.backend != "motionbert"
        or sidecar.method != "frozen_encoder_cache"
        or sidecar.role != "training"
        or sidecar.split != "final_train"
        or sidecar.training_seed is not None
        or not sidecar.scientific_use_allowed
        or sidecar.protocol_sha256 != run_set.protocol_sha256
    ):
        raise ValueError("locked final run uses an unauthorized training feature cache")
    source_candidates: list[Path] = []
    sidecar_candidates: list[Path] = []
    protocol_inputs: list[Path] = []
    training_manifest_candidates: list[Path] = []
    for raw_path, input_sha256 in inputs.items():
        candidate = Path(raw_path)
        if input_sha256 == sidecar.artifact_sha256:
            source_candidates.append(candidate)
        if input_sha256 == sidecar.manifest_sha256:
            try:
                from pose_embed.data import load_manifest

                records = load_manifest(candidate)
            except (OSError, ValueError):
                pass
            else:
                if tuple(
                    record.sample_id for record in records
                ) == sidecar.sample_ids and all(
                    record.split == "final_train" for record in records
                ):
                    training_manifest_candidates.append(candidate)
        if candidate.name.endswith(".npz.manifest.json"):
            try:
                candidate_sidecar = FeatureSidecar.model_validate_json(
                    candidate.read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                pass
            else:
                if candidate_sidecar == sidecar:
                    sidecar_candidates.append(candidate)
        try:
            input_protocol = load_protocol(candidate)
        except (OSError, ValueError):
            pass
        else:
            if protocol_digest(input_protocol) == run_set.protocol_sha256:
                protocol_inputs.append(candidate)
    if len(source_candidates) != 1 or len(sidecar_candidates) != 1:
        raise ValueError("locked final run does not bind its feature cache and sidecar")
    if len(protocol_inputs) != 1 or len(training_manifest_candidates) != 1:
        raise ValueError("locked final run does not bind protocol and data manifests")
    source_path = source_candidates[0]
    plan_path = _locked_path(root, protocol.test_access.evaluation_plan_relative_path)
    plan = load_evaluation_plan(plan_path)
    if evaluation_plan_digest(plan) != run_set.evaluation_plan_sha256:
        raise ValueError("training run uses a different locked evaluation plan")
    assert plan.source_inventory_manifest is not None
    source_manifest_path = _locked_path(
        root, plan.source_inventory_manifest.relative_path
    )
    validate_locked_manifest(plan.source_inventory_manifest, source_manifest_path)
    from pose_embed.data import load_manifest, verify_manifests

    source_records = load_manifest(source_manifest_path)
    training_records = load_manifest(training_manifest_candidates[0])
    verify_manifests(source_records, protocol)
    verify_manifests(training_records, protocol)
    expected_training_ids = tuple(
        record.sample_id
        for record in source_records
        if record.ntu.action not in set(protocol.dataset.novel_actions)
    )
    if (
        tuple(record.sample_id for record in training_records) != expected_training_ids
        or sidecar.sample_ids != expected_training_ids
        or {record.ntu.action for record in training_records}
        != set(range(1, 121)) - set(protocol.dataset.novel_actions)
    ):
        raise ValueError(
            "final training identities must equal all locked auxiliary samples"
        )

    import math

    import numpy as np

    with np.load(source_path, allow_pickle=False) as archive:
        required = {sidecar.array_key, "labels", "sample_ids"}
        if not required <= set(archive.files):
            raise ValueError("locked final training feature cache is incomplete")
        feature_array = np.asarray(archive[sidecar.array_key])
        labels_array = np.asarray(archive["labels"])
        sample_ids = tuple(np.asarray(archive["sample_ids"]).astype(str))
    if (
        tuple(feature_array.shape) != sidecar.shape
        or not np.isfinite(feature_array).all()
        or sample_ids != sidecar.sample_ids
        or labels_array.shape != (len(sample_ids),)
        or not np.array_equal(
            labels_array,
            np.asarray([int(sample_id[-3:]) for sample_id in sample_ids]),
        )
    ):
        raise ValueError("locked final training feature cache differs from its sidecar")

    metrics = load_json_object("metrics")
    expected_metrics_keys = {
        "objective",
        "seed",
        "epochs",
        "epoch_losses",
        "initial_loss",
        "final_loss",
        "input_metadata",
        "initialization_sha256",
        "batch_plan_sha256",
        "epoch_batch_plan_sha256",
        "checkpoint_sha256",
        "telemetry",
    }
    losses = metrics.get("epoch_losses")
    if (
        set(metrics) != expected_metrics_keys
        or metrics.get("objective") != run.method
        or metrics.get("seed") != run.seed
        or metrics.get("epochs") != config.epochs
        or not isinstance(losses, list)
        or len(losses) != config.epochs
        or not all(
            isinstance(loss, (int, float)) and math.isfinite(loss) for loss in losses
        )
        or metrics.get("initial_loss") != losses[0]
        or metrics.get("final_loss") != losses[-1]
        or losses[-1] >= losses[0]
        or metrics.get("input_metadata") != sidecar.model_dump(mode="json")
        or metrics.get("initialization_sha256") != run.initialization_sha256
        or metrics.get("batch_plan_sha256") != run.batch_plan_sha256
        or metrics.get("checkpoint_sha256") != run.checkpoint_sha256
        or metrics.get("telemetry") != telemetry.model_dump(mode="json")
    ):
        raise ValueError("locked final training metrics are incomplete or inconsistent")
    epoch_hashes = _validate_batch_plan(
        files["batch_plan"],
        config,
        labels=[int(value) for value in labels_array.tolist()],
        sample_order_sha256=sidecar.sample_order_sha256,
    )
    if (
        manifest.get("batch_plan_sha256") != run.batch_plan_sha256
        or manifest.get("epoch_batch_plan_sha256") != epoch_hashes
        or metrics.get("epoch_batch_plan_sha256") != epoch_hashes
    ):
        raise ValueError("locked final run batch provenance is inconsistent")

    attempt = load_json_object("attempt")
    attempt_provenance = attempt.get("provenance")
    if not isinstance(attempt_provenance, dict):
        raise ValueError("locked final attempt provenance is missing")
    parsed_attempt_provenance = EvaluationProvenance.model_validate(attempt_provenance)
    expected_attempt_keys = {
        "schema_version",
        "attempt_id",
        "status",
        "started_at",
        "objective",
        "seed",
        "device",
        "scientific_use_allowed",
        "protocol_sha256",
        "config_sha256",
        "input_artifact_sha256",
        "feature_sidecar_sha256",
        "manifest_sha256",
        "canonical_test_opening_ledger",
        "provenance",
    }
    try:
        attempt_started_at = datetime.fromisoformat(str(attempt.get("started_at")))
    except ValueError as exc:
        raise ValueError("locked final attempt timestamp is invalid") from exc
    for raw_path, expected_sha256 in parsed_attempt_provenance.inputs.items():
        try:
            if sha256_file(raw_path) != expected_sha256:
                raise ValueError(
                    f"locked final attempt input hash mismatch: {raw_path}"
                )
        except OSError as exc:
            raise ValueError(
                f"locked final attempt input is unavailable: {raw_path}"
            ) from exc
    if (
        set(attempt) != expected_attempt_keys
        or attempt.get("schema_version") != 1
        or attempt.get("status") != "started"
        or attempt.get("objective") != run.method
        or attempt.get("seed") != run.seed
        or attempt.get("scientific_use_allowed") is not True
        or attempt.get("protocol_sha256") != run_set.protocol_sha256
        or attempt.get("config_sha256") != run.config_sha256
        or attempt.get("input_artifact_sha256") != sidecar.artifact_sha256
        or attempt.get("feature_sidecar_sha256") != sha256_file(sidecar_candidates[0])
        or attempt.get("manifest_sha256") != sidecar.manifest_sha256
        or parsed_attempt_provenance.command != "train-attempt"
        or parsed_attempt_provenance.git_sha != provenance.git_sha
        or parsed_attempt_provenance.git_dirty is not False
        or parsed_attempt_provenance.dependency_lock_sha256
        != provenance.dependency_lock_sha256
        or parsed_attempt_provenance.configuration
        != {"experiment": expected_experiment, "device": configuration.get("device")}
        or not expected_environment_keys <= set(parsed_attempt_provenance.environment)
        or not {
            run.config_sha256,
            sidecar.artifact_sha256,
            sha256_file(sidecar_candidates[0]),
            sidecar.manifest_sha256,
        }
        <= set(parsed_attempt_provenance.inputs.values())
        or attempt.get("device") != configuration.get("device")
        or attempt_started_at.tzinfo is None
        or attempt_started_at != parsed_attempt_provenance.started_at
        or attempt_started_at != provenance.started_at
        or attempt_started_at < (not_before or run_set.selection_locked_at)
        or parsed_attempt_provenance.ended_at > provenance.ended_at
    ):
        raise ValueError("locked final training attempt is incomplete")

    outcome = load_json_object("outcome")
    expected_outcome_keys = {
        "schema_version",
        "attempt_id",
        "status",
        "ended_at",
        "checkpoint_sha256",
        "batch_plan_sha256",
        "metrics_sha256",
        "run_manifest_sha256",
    }
    try:
        outcome_ended_at = datetime.fromisoformat(str(outcome.get("ended_at")))
    except ValueError as exc:
        raise ValueError("locked final outcome timestamp is invalid") from exc
    if (
        set(outcome) != expected_outcome_keys
        or outcome.get("schema_version") != 1
        or outcome.get("attempt_id") != attempt.get("attempt_id")
        or outcome.get("status") != "success"
        or outcome.get("checkpoint_sha256") != run.checkpoint_sha256
        or outcome.get("batch_plan_sha256") != run.batch_plan_sha256
        or outcome.get("metrics_sha256") != run.metrics_sha256
        or outcome.get("run_manifest_sha256") != run.run_manifest_sha256
        or outcome_ended_at.tzinfo is None
        or outcome_ended_at < provenance.ended_at
        or outcome_ended_at > (not_after or run_set.locked_at)
    ):
        raise ValueError("locked final training outcome is incomplete")

    _validate_head_checkpoint(
        files["checkpoint"], config, initialization_sha256=run.initialization_sha256
    )
    return files


def validate_final_run_artifacts(
    run_set: FinalRunSet,
    run: FinalRun,
    artifact_root: str | Path,
    *,
    protocol: ProtocolConfig,
) -> dict[str, Path]:
    """Verify the selected settings and complete immutable evidence for one core run."""
    return _validate_training_run_artifacts(
        run_set,
        run,
        artifact_root,
        protocol=protocol,
    )


def derive_core_failure_status(protocol: ProtocolConfig) -> dict[str, object]:
    """Derive the final-training attempt ledger from immutable run directories."""
    from pose_embed.artifacts import FeatureSidecar
    from pose_embed.evaluation.result import EvaluationProvenance
    from pose_embed.provenance import sha256_file
    from pose_embed.test_access import TestOpeningLedger

    paths = resolve_scientific_paths(protocol)
    run_set = load_final_run_set(paths.final_run_set)
    ledger = TestOpeningLedger.model_validate_json(
        paths.test_opening_ledger.read_text(encoding="utf-8")
    )
    if (
        run_set.protocol_sha256 != protocol_digest(protocol)
        or ledger.final_run_set_sha256 != final_run_set_digest(run_set)
        or ledger.opened_at < run_set.locked_at
    ):
        raise ValueError("core attempt inventory differs from the locked study")

    def load_object(path: Path, label: str) -> dict[str, object]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid {label}: {path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"{label} must be a JSON object: {path}")
        return payload

    def binding(attempt: dict[str, object]) -> tuple[object, ...]:
        return (
            attempt.get("objective"),
            attempt.get("seed"),
            attempt.get("config_sha256"),
            attempt.get("input_artifact_sha256"),
            attempt.get("feature_sidecar_sha256"),
            attempt.get("manifest_sha256"),
        )

    selected: dict[tuple[object, ...], tuple[datetime, str, str]] = {}
    selected_attempt_hashes: set[str] = set()
    for run in run_set.runs:
        files = validate_final_run_artifacts(
            run_set,
            run,
            paths.root,
            protocol=protocol,
        )
        attempt = load_object(files["attempt"], "locked core attempt")
        started_at = datetime.fromisoformat(str(attempt.get("started_at")))
        attempt_sha256 = sha256_file(files["attempt"])
        selected[binding(attempt)] = (
            started_at,
            run.run_manifest_sha256,
            attempt_sha256,
        )
        selected_attempt_hashes.add(attempt_sha256)

    attempt_fields = {
        "schema_version",
        "attempt_id",
        "status",
        "started_at",
        "objective",
        "seed",
        "device",
        "scientific_use_allowed",
        "protocol_sha256",
        "config_sha256",
        "input_artifact_sha256",
        "feature_sidecar_sha256",
        "manifest_sha256",
        "canonical_test_opening_ledger",
        "provenance",
    }
    records: list[dict[str, object]] = []
    unresolved: list[str] = []
    core_methods = {"contrastive", "supcon", "contextual"}
    for attempt_path in sorted(paths.root.rglob("attempt.json"), key=str):
        attempt = load_object(attempt_path, "training attempt")
        if (
            attempt.get("protocol_sha256") != protocol_digest(protocol)
            or attempt.get("scientific_use_allowed") is not True
            or attempt.get("objective") not in core_methods
        ):
            continue
        try:
            started_at = datetime.fromisoformat(str(attempt.get("started_at")))
            provenance = EvaluationProvenance.model_validate(attempt.get("provenance"))
        except ValueError as exc:
            raise ValueError(f"invalid core training attempt: {attempt_path}") from exc
        if started_at < run_set.selection_locked_at:
            continue
        post_opening_violation = started_at > ledger.opened_at
        if set(attempt) != attempt_fields or (
            attempt.get("schema_version") != 1
            or attempt.get("status") != "started"
            or started_at.tzinfo is None
            or provenance.started_at != started_at
            or provenance.command != "train-attempt"
            or provenance.git_dirty is not False
            or attempt.get("canonical_test_opening_ledger")
            != str(paths.test_opening_ledger)
        ):
            raise ValueError(f"core training attempt is incomplete: {attempt_path}")
        for raw_path, expected_sha256 in provenance.inputs.items():
            if sha256_file(raw_path) != expected_sha256:
                raise ValueError(f"core attempt input hash mismatch: {raw_path}")
        required_hashes = {
            attempt.get("config_sha256"),
            attempt.get("input_artifact_sha256"),
            attempt.get("feature_sidecar_sha256"),
            attempt.get("manifest_sha256"),
        }
        if not required_hashes <= set(provenance.inputs.values()):
            raise ValueError(f"core attempt omits a required input: {attempt_path}")
        sidecar_paths = [
            Path(raw_path)
            for raw_path, digest in provenance.inputs.items()
            if digest == attempt.get("feature_sidecar_sha256")
        ]
        if len(sidecar_paths) != 1:
            raise ValueError(
                f"core attempt has no unique feature sidecar: {attempt_path}"
            )
        sidecar = FeatureSidecar.model_validate_json(
            sidecar_paths[0].read_text(encoding="utf-8")
        )
        if sidecar.split != "final_train":
            continue
        if (
            sidecar.backend != "motionbert"
            or sidecar.method != "frozen_encoder_cache"
            or not sidecar.scientific_use_allowed
        ):
            raise ValueError(
                f"core final attempt uses invalid features: {attempt_path}"
            )

        relative_attempt = attempt_path.relative_to(paths.root).as_posix()
        outcome_path = attempt_path.with_name("outcome.json")
        attempt_sha256 = sha256_file(attempt_path)
        status = "missing_outcome"
        resolution_sha256: str | None = None
        outcome_sha256: str | None = None
        if outcome_path.is_file():
            outcome = load_object(outcome_path, "training outcome")
            outcome_sha256 = sha256_file(outcome_path)
            try:
                outcome_ended_at = datetime.fromisoformat(str(outcome.get("ended_at")))
            except ValueError as exc:
                raise ValueError(
                    f"invalid core outcome timestamp: {outcome_path}"
                ) from exc
            if (
                outcome.get("schema_version") != 1
                or outcome.get("attempt_id") != attempt.get("attempt_id")
                or outcome_ended_at.tzinfo is None
                or outcome_ended_at < started_at
            ):
                raise ValueError(f"core training outcome is incomplete: {outcome_path}")
            post_opening_violation = (
                post_opening_violation or outcome_ended_at > ledger.opened_at
            )
            if outcome.get("status") == "success":
                status = (
                    "locked_selected_success"
                    if attempt_sha256 in selected_attempt_hashes
                    else "unselected_success"
                )
            elif outcome.get("status") == "failed":
                replacement = selected.get(binding(attempt))
                if replacement is not None and replacement[0] > outcome_ended_at:
                    status = "resolved_failure"
                    resolution_sha256 = replacement[1]
                else:
                    status = "unresolved_failure"
                artifacts = outcome.get("artifacts_written")
                if not isinstance(artifacts, dict):
                    raise ValueError(
                        f"failed core outcome omits artifact hashes: {outcome_path}"
                    )
                for name, expected_sha256 in artifacts.items():
                    if not isinstance(name, str) or not isinstance(
                        expected_sha256, str
                    ):
                        raise ValueError(f"invalid failed artifact: {outcome_path}")
                    if sha256_file(outcome_path.parent / name) != expected_sha256:
                        raise ValueError(f"failed core artifact hash mismatch: {name}")
            else:
                raise ValueError(f"unknown core outcome status: {outcome_path}")
        if post_opening_violation:
            status = "post_opening_protocol_violation"
        if status in {
            "missing_outcome",
            "unresolved_failure",
            "unselected_success",
            "post_opening_protocol_violation",
        }:
            unresolved.append(relative_attempt)
        records.append(
            {
                "attempt_path": relative_attempt,
                "attempt_sha256": attempt_sha256,
                "outcome_sha256": outcome_sha256,
                "method": attempt["objective"],
                "seed": attempt["seed"],
                "started_at": started_at.isoformat(),
                "status": status,
                "resolution_run_manifest_sha256": resolution_sha256,
            }
        )
    return {
        "schema_version": 1,
        "protocol_sha256": protocol_digest(protocol),
        "final_run_set_sha256": final_run_set_digest(run_set),
        "test_opening_ledger_sha256": sha256_file(paths.test_opening_ledger),
        "attempt_count": len(records),
        "failed_attempt_count": sum(
            record["status"] in {"resolved_failure", "unresolved_failure"}
            for record in records
        ),
        "protocol_violation_count": sum(
            record["status"] == "post_opening_protocol_violation" for record in records
        ),
        "attempts": records,
        "unresolved_failures": unresolved,
    }


def validate_post_core_stretch_authorization(
    protocol: ProtocolConfig,
    evidence_path: str | Path,
) -> None:
    """Authorize exploratory training only after every locked core gate is real."""
    from pose_embed.artifacts import validate_stretch_gate_evidence
    from pose_embed.provenance import sha256_file
    from pose_embed.test_access import TestOpeningLedger

    paths = resolve_scientific_paths(protocol)
    supplied_path = Path(evidence_path).resolve()
    if supplied_path != paths.stretch_gate_evidence:
        raise ValueError("scientific stretch evidence must use the canonical lock path")
    evidence = validate_stretch_gate_evidence(supplied_path, protocol=protocol)
    lock = load_protocol_lock(paths.protocol_lock)
    plan = load_evaluation_plan(paths.evaluation_plan)
    run_set = load_final_run_set(paths.final_run_set)
    verify_protocol_lock(protocol, lock, plan, run_set)
    if run_set.code_sha256 != current_code_hashes():
        raise ValueError("scientific code changed after the core run set was locked")
    ledger = TestOpeningLedger.model_validate_json(
        paths.test_opening_ledger.read_text(encoding="utf-8")
    )
    manifest_validation = validate_evaluation_manifests(
        protocol,
        plan,
        paths.root,
        check_source_files=False,
    )
    expected = (
        evaluation_plan_digest(plan),
        final_run_set_digest(run_set),
        sha256_file(paths.test_opening_ledger),
    )
    observed = (
        evidence.evaluation_plan_sha256,
        evidence.final_run_set_sha256,
        evidence.test_opening_ledger_sha256,
    )
    if observed != expected:
        raise ValueError("stretch evidence differs from the locked core study")
    assert plan.source_inventory_manifest is not None
    if (
        ledger.source_inventory_manifest_sha256,
        ledger.source_file_count,
        ledger.source_files_sha256,
    ) != (
        plan.source_inventory_manifest.sha256,
        manifest_validation.source_file_count,
        manifest_validation.source_files_sha256,
    ):
        raise ValueError("stretch evidence relies on a different source inventory")
    if evidence.recorded_at < ledger.opened_at:
        raise ValueError("stretch gates cannot predate the core test opening")

    for run in run_set.runs:
        validate_final_run_artifacts(
            run_set,
            run,
            paths.root,
            protocol=protocol,
        )
    gate_paths = {
        name: supplied_path.parent / record.evidence_path
        for name, record in evidence.gates.items()
    }
    if gate_paths["nine_core_checkpoints_verified"].resolve() != paths.final_run_set:
        raise ValueError("checkpoint gate must point to the locked final run set")

    core_report_path = gate_paths["full_core_result_matrix_verified"].resolve()
    if {
        core_report_path,
        gate_paths["core_figures_reproducible"].resolve(),
        gate_paths["no_unresolved_core_failures"].resolve(),
    } != {core_report_path}:
        raise ValueError("matrix and figure gates must use one recertified core report")
    canonical_protocol_path = (
        Path(__file__).resolve().parents[2] / "configs/protocol.v1.yaml"
    )
    if protocol_digest(load_protocol(canonical_protocol_path)) != protocol_digest(
        protocol
    ):
        raise ValueError("stretch authorization requires the canonical protocol")
    from pose_embed.report import validate_core_report_summary

    certification = validate_core_report_summary(
        core_report_path, canonical_protocol_path
    )
    if certification.get("unresolved_failures") != []:
        raise ValueError("stretch failure gate still has unresolved core failures")


def validate_exploratory_run_artifacts(
    protocol: ProtocolConfig,
    run_manifest_path: str | Path,
    *,
    seed: int,
    checkpoint_sha256: str,
    evidence_path: str | Path,
) -> dict[str, Path]:
    """Validate one post-core Multi-Similarity run without adding it to core."""
    from pose_embed.artifacts import validate_stretch_gate_evidence
    from pose_embed.provenance import sha256_file
    from pose_embed.test_access import TestOpeningLedger

    paths = resolve_scientific_paths(protocol)
    supplied_evidence = Path(evidence_path).resolve()
    if supplied_evidence != paths.stretch_gate_evidence:
        raise ValueError("exploratory evaluation requires canonical stretch evidence")
    evidence = validate_stretch_gate_evidence(supplied_evidence, protocol=protocol)
    lock = load_protocol_lock(paths.protocol_lock)
    plan = load_evaluation_plan(paths.evaluation_plan)
    run_set = load_final_run_set(paths.final_run_set)
    verify_protocol_lock(protocol, lock, plan, run_set)
    if run_set.code_sha256 != current_code_hashes():
        raise ValueError("scientific code changed after the core run set was locked")
    ledger = TestOpeningLedger.model_validate_json(
        paths.test_opening_ledger.read_text(encoding="utf-8")
    )
    if (
        evidence.evaluation_plan_sha256,
        evidence.final_run_set_sha256,
        evidence.test_opening_ledger_sha256,
    ) != (
        evaluation_plan_digest(plan),
        final_run_set_digest(run_set),
        sha256_file(paths.test_opening_ledger),
    ):
        raise ValueError("exploratory run uses evidence from a different core study")
    if evidence.recorded_at < ledger.opened_at:
        raise ValueError("exploratory authorization predates the test opening")

    validate_post_core_stretch_authorization(protocol, supplied_evidence)
    root = paths.root
    manifest_path = Path(run_manifest_path).resolve()
    if (
        not manifest_path.is_relative_to(root)
        or manifest_path.name != "run-manifest.json"
    ):
        raise ValueError("exploratory run manifest must be below the artifact root")
    files = {
        "run_manifest": manifest_path,
        "checkpoint": manifest_path.parent / "head.pt",
        "batch_plan": manifest_path.parent / "batch-plan.json",
        "metrics": manifest_path.parent / "metrics.json",
        "attempt": manifest_path.parent / "attempt.json",
        "outcome": manifest_path.parent / "outcome.json",
    }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("exploratory run manifest is invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("exploratory run manifest must be a JSON object")
    configuration = manifest.get("configuration")
    inputs = manifest.get("inputs")
    if not isinstance(configuration, dict) or not isinstance(inputs, dict):
        raise ValueError("exploratory run is missing configuration or hashed inputs")
    try:
        config = ExperimentConfig.model_validate(configuration.get("experiment"))
    except ValueError as exc:
        raise ValueError("exploratory run configuration is invalid") from exc
    validate_experiment_against_protocol(config, protocol)
    if (config.objective, config.seed) != ("multi_similarity_with_miner", seed):
        raise ValueError("exploratory run method/seed mismatch")
    config_candidates = []
    for raw_path in inputs:
        candidate = Path(raw_path)
        try:
            candidate_config = load_experiment(candidate)
        except (OSError, ValueError):
            continue
        if candidate_config == config:
            config_candidates.append(candidate)
    if len(config_candidates) != 1:
        raise ValueError("exploratory run must bind one exact experiment config")
    files["config"] = config_candidates[0]
    try:
        synthetic_run = FinalRun(
            method="multi_similarity_with_miner",
            seed=seed,
            config_relative_path="exploratory/config.yaml",
            config_sha256=sha256_file(files["config"]),
            run_manifest_relative_path="exploratory/run-manifest.json",
            run_manifest_sha256=sha256_file(files["run_manifest"]),
            checkpoint_relative_path="exploratory/head.pt",
            checkpoint_sha256=checkpoint_sha256,
            batch_plan_relative_path="exploratory/batch-plan.json",
            batch_plan_sha256=sha256_file(files["batch_plan"]),
            metrics_relative_path="exploratory/metrics.json",
            metrics_sha256=sha256_file(files["metrics"]),
            attempt_relative_path="exploratory/attempt.json",
            attempt_sha256=sha256_file(files["attempt"]),
            outcome_relative_path="exploratory/outcome.json",
            outcome_sha256=sha256_file(files["outcome"]),
            initialization_sha256=str(manifest.get("initialization_sha256")),
        )
    except (OSError, ValueError) as exc:
        raise ValueError("exploratory run evidence is incomplete") from exc
    paired_core = final_run_for(run_set, "contrastive", seed)
    if (
        synthetic_run.initialization_sha256 != paired_core.initialization_sha256
        or synthetic_run.batch_plan_sha256 != paired_core.batch_plan_sha256
    ):
        raise ValueError("exploratory run is not paired to the core seed")
    validated = _validate_training_run_artifacts(
        run_set,
        synthetic_run,
        root,
        protocol=protocol,
        resolved_files=files,
        not_before=evidence.recorded_at,
        not_after=datetime.now(UTC),
        required_input_sha256=sha256_file(supplied_evidence),
        require_core_selection=False,
    )
    paired_core_files = validate_final_run_artifacts(
        run_set,
        paired_core,
        root,
        protocol=protocol,
    )
    from pose_embed.artifacts import FeatureSidecar

    core_manifest = json.loads(
        paired_core_files["run_manifest"].read_text(encoding="utf-8")
    )
    core_sidecar = FeatureSidecar.model_validate(core_manifest.get("feature_sidecar"))
    exploratory_sidecar = FeatureSidecar.model_validate(manifest.get("feature_sidecar"))
    if (
        exploratory_sidecar.artifact_sha256 != core_sidecar.artifact_sha256
        or exploratory_sidecar.encoder_checkpoint_sha256
        != core_sidecar.encoder_checkpoint_sha256
        or exploratory_sidecar.upstream_sha256 != core_sidecar.upstream_sha256
        or exploratory_sidecar.preprocessing_sha256 != core_sidecar.preprocessing_sha256
    ):
        raise ValueError("exploratory run changes the core training-feature lineage")
    return {**validated, "stretch_gate_evidence": supplied_evidence}


def protocol_digest(protocol: ProtocolConfig) -> str:
    """Hash the canonical validated protocol, independent of YAML formatting."""
    return hashlib.sha256(canonical_json(protocol)).hexdigest()


def load_evaluation_plan(path: str | Path) -> EvaluationPlan:
    try:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"evaluation plan does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid evaluation plan YAML: {exc}") from exc
    return EvaluationPlan.model_validate(payload)


def evaluation_plan_digest(plan: EvaluationPlan) -> str:
    return hashlib.sha256(canonical_json(plan)).hexdigest()


def load_final_run_set(path: str | Path) -> FinalRunSet:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"final run set does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid final run-set JSON: {exc}") from exc
    return FinalRunSet.model_validate(payload)


def final_run_set_digest(run_set: FinalRunSet) -> str:
    return hashlib.sha256(canonical_json(run_set)).hexdigest()


def load_protocol_lock(path: str | Path) -> ProtocolLock:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"protocol lock does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid protocol lock JSON: {exc}") from exc
    return ProtocolLock.model_validate(payload)


def verify_protocol_lock(
    protocol: ProtocolConfig,
    lock: ProtocolLock,
    evaluation_plan: EvaluationPlan,
    final_run_set: FinalRunSet,
    *,
    now: datetime | None = None,
) -> str:
    """Return the digest when a lock is complete and matches the protocol."""
    digest = protocol_digest(protocol)
    if lock.protocol_id != protocol.protocol_id:
        raise ValueError(
            f"lock protocol_id {lock.protocol_id!r} does not match "
            f"{protocol.protocol_id!r}"
        )
    if lock.protocol_sha256 != digest:
        raise ValueError("protocol content changed after the supplied lock was created")
    if lock.evaluation_plan_sha256 != evaluation_plan_digest(evaluation_plan):
        raise ValueError("evaluation plan changed after the supplied lock was created")
    if evaluation_plan.status != "locked":
        raise ValueError(
            "final evaluation requires a locked, populated evaluation plan"
        )
    manifest_bindings = (
        evaluation_plan.source_inventory_manifest,
        evaluation_plan.anchor_manifest,
        evaluation_plan.official_query_manifest,
        evaluation_plan.primary_query_manifest,
    )
    assert all(binding is not None for binding in manifest_bindings)
    source, anchors, official, primary = manifest_bindings
    assert source is not None
    assert anchors is not None
    assert official is not None
    assert primary is not None
    if (
        lock.source_inventory_manifest_sha256,
        lock.anchor_manifest_sha256,
        lock.official_query_manifest_sha256,
        lock.primary_query_manifest_sha256,
    ) != (source.sha256, anchors.sha256, official.sha256, primary.sha256):
        raise ValueError(
            "protocol lock manifest hashes differ from the evaluation plan"
        )
    if lock.final_run_set_sha256 != final_run_set_digest(final_run_set):
        raise ValueError("final run set changed after the supplied lock was created")
    if final_run_set.protocol_sha256 != digest:
        raise ValueError("final run set is bound to a different protocol")
    if final_run_set.evaluation_plan_sha256 != evaluation_plan_digest(evaluation_plan):
        raise ValueError("final run set is bound to a different evaluation plan")
    if evaluation_plan.seeds != protocol.training.seeds:
        raise ValueError("evaluation-plan seeds differ from the protocol")
    if evaluation_plan.methods != protocol.objectives.core:
        raise ValueError("evaluation-plan methods differ from the protocol")
    if evaluation_plan.metrics != protocol.analysis.metrics:
        raise ValueError("evaluation-plan metrics differ from the protocol")
    anchor_actions = {int(sample_id[-3:]) for sample_id in anchors.sample_ids}
    if anchor_actions != set(protocol.dataset.novel_actions):
        raise ValueError("anchor manifest actions differ from the protocol novel set")
    if {run.seed for run in final_run_set.runs} != set(protocol.training.seeds):
        raise ValueError("final run-set seeds differ from the protocol")
    if lock.advisor_approved_at > lock.locked_at:
        raise ValueError("locked_at must not precede advisor_approved_at")
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("verification time must include a timezone")
    if lock.locked_at > current_time or lock.advisor_approved_at > current_time:
        raise ValueError("protocol lock timestamps must not be in the future")
    if final_run_set.locked_at > lock.locked_at:
        raise ValueError("protocol lock must not precede final run-set finalization")
    if (
        final_run_set.locked_at > current_time
        or final_run_set.selection_locked_at > current_time
    ):
        raise ValueError("final run-set timestamps must not be in the future")
    return digest


def verify_protocol(
    protocol_path: str | Path,
    *,
    lock_path: str | Path | None = None,
    evaluation_plan_path: str | Path | None = None,
    final_run_set_path: str | Path | None = None,
    require_locked: bool = False,
    now: datetime | None = None,
) -> tuple[ProtocolConfig, str]:
    """Validate a protocol and, when supplied or required, its approval lock."""
    protocol = load_protocol(protocol_path)
    digest = protocol_digest(protocol)
    if require_locked and lock_path is None:
        paths = resolve_scientific_paths(protocol)
        lock_path = paths.protocol_lock
        evaluation_plan_path = paths.evaluation_plan
        final_run_set_path = paths.final_run_set
    if lock_path is not None:
        if evaluation_plan_path is None:
            raise ValueError("an evaluation plan is required with a protocol lock")
        if final_run_set_path is None:
            raise ValueError("a final run set is required with a protocol lock")
        digest = verify_protocol_lock(
            protocol,
            load_protocol_lock(lock_path),
            load_evaluation_plan(evaluation_plan_path),
            load_final_run_set(final_run_set_path),
            now=now,
        )
    return protocol, digest
