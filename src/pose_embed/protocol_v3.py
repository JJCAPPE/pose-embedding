"""Immutable, staged v3 design authorization; no template authorizes science."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from pose_embed.config import StrictModel, load_protocol
from pose_embed.config_v3 import SHA256, ArtifactBinding, ProtocolV3Config, V3Pilot
from pose_embed.protocol import (
    EvaluationPlan,
    FinalRunSet,
    ProtocolLock,
    protocol_digest,
    resolve_scientific_paths,
)
from pose_embed.provenance import sha256_file, write_immutable_json

COUNTS = {
    "development_train": 76013,
    "development_validation": 18988,
    "final_train": 95001,
    "novel_anchor": 20,
    "novel_query_primary": 18884,
    "novel_query_official": 18924,
    "development_gallery": 20,
    "development_queries": 18929,
}


class V3DesignLock(StrictModel):
    schema_version: Literal[3]
    kind: Literal["v3_auxiliary_design_and_pilot_authorization"]
    protocol_sha256: SHA256
    protocol_relative_path: Literal[
        "study-v3/locks/protocol.v3.json",
        "study-v3/revisions/execution-r1/locks/protocol.v3.json",
    ]
    predecessor_design: ArtifactBinding | None = None
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    manifests: dict[str, ArtifactBinding]
    code_sha256: dict[str, SHA256] = Field(min_length=1)
    artifact_root_registry_sha256: SHA256
    pilot: V3Pilot
    epochs: Literal[20]
    novel_access_authorized: Literal[False]

    @model_validator(mode="after")
    def complete_design(self) -> V3DesignLock:
        _timestamp(self.recorded_at)
        successor = self.protocol_relative_path.startswith("study-v3/revisions/")
        if successor != (self.predecessor_design is not None):
            raise ValueError("execution revision requires its predecessor design")
        if set(self.manifests) != set(COUNTS):
            raise ValueError("design lock requires all eight identity-bound manifests")
        return self


class V3SelectionAuthorization(StrictModel):
    schema_version: Literal[3]
    kind: Literal["v3_selection_authorization"]
    protocol_sha256: SHA256
    design_lock_sha256: SHA256
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    pilot_records: dict[Literal["contrastive", "supcon", "contextual"], ArtifactBinding]
    corruption_verification: ArtifactBinding
    analysis_verification: ArtifactBinding
    capacity_report: ArtifactBinding
    seal_audit: ArtifactBinding
    run_matrix: ArtifactBinding
    capacity_passed: Literal[True]
    novel_access_authorized: Literal[False]

    @model_validator(mode="after")
    def all_pilots(self) -> V3SelectionAuthorization:
        _timestamp(self.recorded_at)
        if set(self.pilot_records) != {"contrastive", "supcon", "contextual"}:
            raise ValueError("selection requires every complete engineering pilot")
        return self


class V3EvaluationPlan(EvaluationPlan):
    schema_version: Literal[3]
    plan_id: Literal["final-evaluation-v3"]

    @model_validator(mode="after")
    def v3_fixed_seeds(self) -> V3EvaluationPlan:
        if self.seeds != (7, 17, 29):
            raise ValueError("v3 evaluation requires seeds 7, 17, 29")
        if self.status == "locked":
            for binding, count in (
                (self.source_inventory_manifest, 113945),
                (self.official_query_manifest, 18924),
                (self.primary_query_manifest, 18884),
            ):
                if binding is None or binding.sample_count != count:
                    raise ValueError("v3 evaluation identity counts differ")
        return self


class V3FinalRunSet(FinalRunSet):
    schema_version: Literal[3]
    run_set_id: Literal["final-core-run-set-v3"]
    selection_authorization_sha256: SHA256
    selection_evidence: ArtifactBinding

    @model_validator(mode="after")
    def v3_final_runs(self) -> V3FinalRunSet:
        if {run.seed for run in self.runs} != {7, 17, 29}:
            raise ValueError("v3 final run set requires exact paired seeds")
        for run in self.runs:
            for name, value in run.model_dump().items():
                if name.endswith("_relative_path") and not value.startswith(
                    "study-v3/"
                ):
                    raise ValueError("v3 final artifacts must use the v3 namespace")
        return self


class V3FinalLock(ProtocolLock):
    """Final schema only; auxiliary design freeze never authorizes novel access."""

    protocol_id: Literal["protocol-v3"]
    design_lock_sha256: SHA256
    selection_authorization_sha256: SHA256
    artifact_root_registry_sha256: SHA256


def _timestamp(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None or value > datetime.now(UTC):
        raise ValueError("record timestamp must have a timezone and not be in future")


def _bound_file(root: Path, binding: ArtifactBinding) -> Path:
    path = (root / binding.relative_path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"missing or escaping bound artifact: {binding.relative_path}")
    if sha256_file(path) != binding.sha256:
        raise ValueError(f"bound artifact hash mismatch: {binding.relative_path}")
    return path


def v3_design_code_hashes() -> dict[str, str]:
    """Freeze the complete v3 command, authorization and scientific path."""
    from pose_embed.motionbert_inputs import MOTIONBERT_CODE_PATHS

    root = Path(__file__).resolve().parents[2]
    files = {
        "src/pose_embed/config.py",
        "src/pose_embed/config_v3.py",
        "src/pose_embed/cli.py",
        "src/pose_embed/v3_commands.py",
        "src/pose_embed/protocol_v3.py",
        "src/pose_embed/artifacts.py",
        "src/pose_embed/features.py",
        "src/pose_embed/motionbert_inputs.py",
        "src/pose_embed/motionbert_features.py",
        "src/pose_embed/dataset_seal.py",
        "src/pose_embed/preparation_v3.py",
        "uv.lock",
        "third_party/upstreams.toml",
        "data/manifests/motionbert-checkpoint.v1.json",
        "src/pose_embed/training/runner.py",
        "src/pose_embed/training/sampler.py",
        "src/pose_embed/evaluation/metrics.py",
        "src/pose_embed/revision_v3.py",
        "src/pose_embed/novel_subset_v3.py",
        "src/pose_embed/geometry_v3.py",
        "src/pose_embed/protocol_v3_campaign.py",
        "src/pose_embed/protocol.py",
        "src/pose_embed/test_access.py",
        "src/pose_embed/opening_capacity_v3.py",
        "src/pose_embed/evaluation/runner.py",
        "src/pose_embed/evaluation/result.py",
        "src/pose_embed/evaluation/analysis.py",
        "src/pose_embed/report.py",
        "docs/protocol/v3-report-template.md",
        "scripts/run_v3_execution.py",
        "scripts/time_v3_resident.py",
        "scripts/validate_v3_execution.py",
        "scripts/study_v3_execution.qsub",
        "scripts/study_v3.qsub",
    }
    files.update(MOTIONBERT_CODE_PATHS)
    for folder in ("data", "corruptions", "models", "losses"):
        files.update(
            str(path.relative_to(root))
            for path in (root / "src/pose_embed" / folder).rglob("*.py")
        )
    return {name: sha256_file(root / name) for name in sorted(files)}


def _validate_identities(
    protocol: ProtocolV3Config, root: Path
) -> dict[str, list[str]]:
    from pose_embed.data.development import build_development_episode
    from pose_embed.data.inventory import build_split_manifests, load_inventory
    from pose_embed.dataset_seal import validate_registered_source_inventory

    prep = protocol.preparation
    if prep is None:
        raise ValueError("unresolved v3 template cannot authorize scientific work")
    payload = json.loads(_bound_file(root, prep.identities).read_text())
    if (
        payload.get("schema_version") != 1
        or payload.get("selection_prefix")
        != protocol.provenance.development_anchor_prefix
        or payload.get("historical_episode_sha256")
        != protocol.provenance.historical_development_episode_sha256
    ):
        raise ValueError("v3 identity provenance differs from the historical episode")
    inventory_path = _bound_file(root, prep.source_inventory)
    validate_registered_source_inventory(prep.source_inventory.sha256)
    inventory = load_inventory(inventory_path)
    if len(inventory) != 113945:
        raise ValueError("v3 requires the complete 113945-row source inventory")
    manifests = build_split_manifests(inventory, protocol)
    expected = {
        Path(name).stem.replace("-", "_"): [r.sample_id for r in rows]
        for name, rows in manifests.items()
        if name != "official-novel.jsonl"
    }
    gallery, queries, _ = build_development_episode(
        manifests["development-validation.jsonl"], protocol
    )
    expected["development_gallery"] = [r.sample_id for r in gallery]
    expected["development_queries"] = [r.sample_id for r in queries]
    if payload.get("ordered_sample_ids") != dict(expected):
        raise ValueError(
            "v3 exact ordered identities differ from the adopted source/episode"
        )
    if {name: len(ids) for name, ids in expected.items()} != COUNTS:
        raise ValueError("v3 complete split counts differ from the fixed episode")
    return dict(expected)


def _validate_design_inputs(
    protocol: ProtocolV3Config, lock: V3DesignLock, root: Path
) -> None:
    from pose_embed.corruptions.fallback import validate_torso_fallback_v3
    from pose_embed.data.manifest import load_manifest
    from pose_embed.models.motionbert import verify_motionbert_assets

    if protocol.status != "resolved" or protocol.preparation is None:
        raise ValueError("unresolved v3 template cannot authorize scientific work")
    if (
        lock.protocol_sha256 != protocol_digest(protocol)
        or lock.pilot != protocol.training.pilot
        or lock.protocol_relative_path
        != protocol.test_access.resolved_protocol_relative_path
    ):
        raise ValueError("v3 design lock differs from the protocol/pilot specification")
    if lock.predecessor_design is not None:
        validate_execution_revision(protocol, lock, root)
    prep = protocol.preparation
    assets = verify_motionbert_assets(_registry_path().parents[1])
    if prep.encoder_checkpoint_sha256 != assets[
        "checkpoint_sha256"
    ] or prep.upstream_sha256 != {name: assets[name] for name in prep.upstream_sha256}:
        raise ValueError("v3 protocol encoder asset hashes differ from verified assets")
    _bound_file(root, prep.auxiliary_container)
    identities = _validate_identities(protocol, root)
    for name, binding in lock.manifests.items():
        records = load_manifest(_bound_file(root, binding))
        expected_split = (
            "development_validation"
            if name in {"development_gallery", "development_queries"}
            else name
        )
        if [r.sample_id for r in records] != identities[name] or any(
            r.split != expected_split for r in records
        ):
            raise ValueError(f"v3 manifest identities/role differ: {name}")
    fallback = json.loads(_bound_file(root, prep.fallback_evidence).read_text())
    from pose_embed.preparation_v3 import auxiliary_preprocessing_digest

    value = validate_torso_fallback_v3(
        fallback,
        expected_sample_ids=identities["development_train"],
        source_inventory_sha256=prep.source_inventory.sha256,
        source_manifest_sha256=lock.manifests["development_train"].sha256,
        preprocessing_sha256=auxiliary_preprocessing_digest(protocol),
    )
    if value != prep.fallback_value:
        raise ValueError(
            "v3 fallback value differs from its measured immutable evidence"
        )
    if sha256_file(_registry_path()) != lock.artifact_root_registry_sha256:
        raise ValueError(
            "historical artifact-root registry changed after design freeze"
        )
    repository = Path(__file__).resolve().parents[2]
    expected_files = v3_design_code_hashes()
    if lock.code_sha256 != expected_files:
        raise ValueError("cache-affecting code changed after v3 design freeze")
    for name, digest in lock.code_sha256.items():
        _bound_file(repository, ArtifactBinding(relative_path=name, sha256=digest))


def require_v3_design(protocol: ProtocolV3Config) -> V3DesignLock:
    """Validate resolved scientific design and all metadata before auxiliary work."""
    if not isinstance(protocol, ProtocolV3Config) or protocol.preparation is None:
        raise ValueError("unresolved v3 template cannot authorize scientific work")
    root = resolve_scientific_paths(protocol).root
    lock_path = root / protocol.test_access.design_lock_relative_path
    try:
        lock = V3DesignLock.model_validate_json(lock_path.read_text())
    except OSError as exc:
        raise ValueError("v3 requires its canonical immutable design lock") from exc
    resolved = load_protocol(root / lock.protocol_relative_path)
    if resolved != protocol:
        raise ValueError(
            "supplied v3 protocol differs from the canonical resolved protocol"
        )
    _validate_design_inputs(protocol, lock, root)
    return lock


def _write_same_or_new(path: Path, payload: object) -> None:
    if path.exists():
        if json.loads(path.read_text()) != payload:
            raise ValueError(f"refusing to replace prior immutable design: {path}")
        return
    write_immutable_json(path, payload)


def _registry_path() -> Path:
    data_root = os.environ.get("POSE_EMBED_DATA_ROOT")
    if not data_root or not Path(data_root).is_absolute():
        raise ValueError("v3 requires an absolute POSE_EMBED_DATA_ROOT")
    return Path(data_root) / "provenance/artifact-roots.v3.json"


def freeze_v3_design(
    protocol: ProtocolV3Config,
    *,
    manifests: dict[str, ArtifactBinding | dict],
    recorded_by: str,
    code_sha256: dict[str, str] | None = None,
    predecessor_design: ArtifactBinding | None = None,
) -> V3DesignLock:
    """Publish the complete design only after measured preparation is verified."""
    from pose_embed.dataset_seal import require_dataset_unopened

    require_dataset_unopened(require_registry=True)
    root = resolve_scientific_paths(protocol).root
    lock_path = root / protocol.test_access.design_lock_relative_path
    if lock_path.exists():
        return require_v3_design(protocol)
    lock = V3DesignLock(
        schema_version=3,
        kind="v3_auxiliary_design_and_pilot_authorization",
        protocol_sha256=protocol_digest(protocol),
        protocol_relative_path=protocol.test_access.resolved_protocol_relative_path,
        predecessor_design=predecessor_design,
        recorded_at=datetime.now(UTC),
        recorded_by=recorded_by,
        manifests=manifests,
        code_sha256=code_sha256 or v3_design_code_hashes(),
        artifact_root_registry_sha256=sha256_file(_registry_path()),
        pilot=protocol.training.pilot,
        epochs=20,
        novel_access_authorized=False,
    )
    _validate_design_inputs(protocol, lock, root)
    _write_same_or_new(
        root / lock.protocol_relative_path, protocol.model_dump(mode="json")
    )
    write_immutable_json(lock_path, lock.model_dump(mode="json"))
    return require_v3_design(protocol)


def validate_execution_revision(
    protocol: ProtocolV3Config, lock: V3DesignLock, root: Path
) -> None:
    """Permit only the declared path revision, retaining the complete old design."""
    binding = lock.predecessor_design
    if binding is None or binding.relative_path != "study-v3/locks/design-lock.v3.json":
        raise ValueError("execution revision requires the original immutable design")
    previous = V3DesignLock.model_validate_json(_bound_file(root, binding).read_text())
    prior = load_protocol(root / previous.protocol_relative_path)
    if (
        previous.predecessor_design is not None
        or protocol_digest(prior) != previous.protocol_sha256
        or previous.recorded_at >= lock.recorded_at
        or previous.artifact_root_registry_sha256 != lock.artifact_root_registry_sha256
    ):
        raise ValueError("execution revision predecessor or chronology differs")
    old = prior.model_dump(mode="json")
    new = protocol.model_dump(mode="json")
    for payload in (old, new):
        for field in tuple(payload["test_access"]):
            if field.endswith("_relative_path"):
                del payload["test_access"][field]
    if old != new:
        raise ValueError("execution revision changes scientific design or preparation")
    for role, original in previous.manifests.items():
        current = lock.manifests[role]
        if (
            _bound_file(root, original).read_bytes()
            != _bound_file(root, current).read_bytes()
        ):
            raise ValueError("execution revision changes original manifest bytes")


def require_v3_selection_authorization(
    protocol: ProtocolV3Config,
) -> V3SelectionAuthorization:
    """Dispatch the later campaign audit without changing frozen cache interfaces."""
    from pose_embed.protocol_v3_campaign import require_selection_authorization

    require_v3_design(protocol)
    return require_selection_authorization(protocol)


def require_v3_final_authorization(
    protocol: ProtocolV3Config, *, now: datetime | None = None
) -> V3FinalLock:
    """Require every final head and the complete canonical cross-binding."""
    from pose_embed.protocol import (
        load_evaluation_plan,
        load_final_run_set,
        load_protocol_lock,
        validate_evaluation_manifests,
        validate_final_run_artifacts,
        verify_protocol_lock,
    )
    from pose_embed.protocol_v3_campaign import (
        require_selected_configurations,
        selected_configs_path,
    )

    if protocol.preparation is None or "execution-r1" not in (
        protocol.test_access.design_lock_relative_path
    ):
        raise ValueError(
            "v3 final authorization is unavailable before the measured campaign audit; "
            "the completion release is required"
        )
    paths = resolve_scientific_paths(protocol)
    selected = require_selected_configurations(protocol)
    authorization = V3SelectionAuthorization.model_validate_json(
        (
            paths.root / protocol.test_access.selection_authorization_relative_path
        ).read_text()
    )
    lock = load_protocol_lock(paths.protocol_lock)
    plan = load_evaluation_plan(paths.evaluation_plan)
    runs = load_final_run_set(paths.final_run_set)
    if not isinstance(lock, V3FinalLock) or not isinstance(runs, V3FinalRunSet):
        raise ValueError("v3 requires its complete final lock and run-set schemas")
    selection_hash = sha256_file(
        paths.root / protocol.test_access.selection_authorization_relative_path
    )
    if (
        lock.design_lock_sha256 != authorization.design_lock_sha256
        or lock.selection_authorization_sha256 != selection_hash
        or runs.selection_authorization_sha256 != selection_hash
        or lock.artifact_root_registry_sha256 != sha256_file(_registry_path())
        or runs.selection_locked_at <= authorization.recorded_at
        or runs.selection_locked_at != selected.recorded_at
        or (paths.root / runs.selection_evidence.relative_path).resolve()
        != selected_configs_path(protocol).resolve()
        or runs.selection_evidence.sha256
        != sha256_file(selected_configs_path(protocol))
    ):
        raise ValueError("v3 final lock authorization bindings or chronology differ")
    _bound_file(paths.root, runs.selection_evidence)
    verify_protocol_lock(protocol, lock, plan, runs, now=now)
    validate_evaluation_manifests(protocol, plan, paths.root, check_source_files=False)
    for run in runs.runs:
        validate_final_run_artifacts(runs, run, paths.root, protocol=protocol)
    return lock
