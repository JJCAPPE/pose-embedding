"""Atomic, immutable evidence for the one-time novel-test opening."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pose_embed.config import ProtocolConfig
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.dataset_seal import (
    OPENING,
    guarded_opening,
    record_dataset_opening,
    validate_dataset_opening,
)
from pose_embed.protocol import (
    evaluation_plan_digest,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    load_protocol_lock,
    resolve_scientific_paths,
    validate_evaluation_manifests,
    validate_final_run_artifacts,
    verify_protocol_lock,
)
from pose_embed.provenance import sha256_file, write_immutable_json
from pose_embed.validation_proofs import verify_validation_proofs


class TestOpeningLedger(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int
    event_id: str = Field(min_length=1)
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    protocol_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_run_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_inventory_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_file_count: int = Field(gt=0)
    source_files_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    opened_at: datetime
    opening_capacity: ArtifactBinding | None = None

    @field_validator("schema_version")
    @classmethod
    def schema_is_v1(cls, value: int) -> int:
        if value != 2:
            raise ValueError("test-opening ledger schema must be version 2")
        return value

    @field_validator("opened_at")
    @classmethod
    def opened_at_is_valid(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("test-opening timestamp must include a timezone")
        if value > datetime.now(UTC):
            raise ValueError("test-opening timestamp must not be in the future")
        return value


def _load_ledger(path: Path) -> TestOpeningLedger:
    try:
        return TestOpeningLedger.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"test-opening ledger does not exist: {path}") from exc


def validate_recorded_test_opening(protocol: ProtocolConfig) -> TestOpeningLedger:
    """Recheck the complete archival opening identity without opening anything."""
    paths = resolve_scientific_paths(protocol)
    ledger = _load_ledger(paths.test_opening_ledger)
    lock = load_protocol_lock(paths.protocol_lock)
    plan = load_evaluation_plan(paths.evaluation_plan)
    runs = load_final_run_set(paths.final_run_set)
    digest = verify_protocol_lock(protocol, lock, plan, runs)
    manifests = validate_evaluation_manifests(
        protocol, plan, paths.root, check_source_files=False
    )
    assert plan.source_inventory_manifest is not None
    expected = {
        "protocol_sha256": digest,
        "protocol_lock_sha256": sha256_file(paths.protocol_lock),
        "evaluation_plan_sha256": evaluation_plan_digest(plan),
        "final_run_set_sha256": final_run_set_digest(runs),
        "source_inventory_manifest_sha256": plan.source_inventory_manifest.sha256,
        "source_file_count": manifests.source_file_count,
        "source_files_sha256": manifests.source_files_sha256,
    }
    if (
        any(getattr(ledger, key) != value for key, value in expected.items())
        or ledger.opened_at < lock.locked_at
    ):
        raise ValueError(
            "recorded test opening differs from the canonical authorization"
        )
    authorization = {
        key.replace(
            "source_inventory_manifest_sha256", "source_inventory_sha256"
        ): value
        for key, value in expected.items()
        if key not in {"source_file_count", "source_files_sha256"}
    }
    capacity_time = None
    if protocol.protocol_id == "protocol-v3":
        from pose_embed.opening_capacity_v3 import validate_opening_capacity

        if ledger.opening_capacity is None:
            raise ValueError("v3 opening is missing its fresh capacity evidence")
        capacity_time = validate_opening_capacity(
            protocol, ledger.opening_capacity, sha256_file(paths.protocol_lock)
        )
        authorization["opening_capacity"] = ledger.opening_capacity.model_dump()
    elif ledger.opening_capacity is not None:
        raise ValueError("historical opening cannot carry v3 capacity evidence")
    common = validate_dataset_opening(
        version=protocol.protocol_id, authorization=authorization
    )
    if capacity_time is not None and capacity_time > datetime.fromisoformat(
        common["opened_at"]
    ):
        raise ValueError("opening capacity evidence must precede the dataset opening")
    if datetime.fromisoformat(common["opened_at"]) > ledger.opened_at:
        raise ValueError("common opening must precede the protocol opening")
    return ledger


@guarded_opening
def open_final_test_once(
    protocol: ProtocolConfig,
    *,
    protocol_sha256: str,
) -> TestOpeningLedger:
    """Verify the full inventory, then create or validate one opening event."""
    paths = resolve_scientific_paths(protocol)
    if protocol.protocol_id == "protocol-v3":
        from pose_embed.protocol_v3 import require_v3_final_authorization

        require_v3_final_authorization(protocol)
    if (paths.root / "benchmark-v2/locks/test-opening.json").exists():
        raise ValueError("legacy test opening is forbidden after benchmark v2 opening")
    destination = paths.test_opening_ledger
    lock = load_protocol_lock(paths.protocol_lock)
    plan = load_evaluation_plan(paths.evaluation_plan)
    run_set = load_final_run_set(paths.final_run_set)
    verified_sha256 = verify_protocol_lock(protocol, lock, plan, run_set)
    if verified_sha256 != protocol_sha256:
        raise ValueError("test-opening protocol digest differs from the verified lock")
    lock_sha256 = sha256_file(paths.protocol_lock)
    plan_sha256 = evaluation_plan_digest(plan)
    run_set_sha256 = final_run_set_digest(run_set)
    initial_opening = not destination.exists()
    manifest_validation = validate_evaluation_manifests(
        protocol,
        plan,
        paths.root,
        check_source_files=initial_opening,
    )
    if initial_opening and not manifest_validation.source_files_verified:
        raise ValueError("initial test opening requires verified source files")
    if initial_opening:
        for run in run_set.runs:
            validate_final_run_artifacts(
                run_set,
                run,
                paths.root,
                protocol=protocol,
            )
    assert plan.source_inventory_manifest is not None
    source_manifest_sha256 = plan.source_inventory_manifest.sha256

    def validate_existing() -> TestOpeningLedger:
        existing = _load_ledger(destination)
        expected = (
            protocol_sha256,
            lock_sha256,
            plan_sha256,
            run_set_sha256,
            source_manifest_sha256,
            manifest_validation.source_file_count,
            manifest_validation.source_files_sha256,
        )
        observed = (
            existing.protocol_sha256,
            existing.protocol_lock_sha256,
            existing.evaluation_plan_sha256,
            existing.final_run_set_sha256,
            existing.source_inventory_manifest_sha256,
            existing.source_file_count,
            existing.source_files_sha256,
        )
        if observed != expected:
            raise ValueError(
                "test-opening ledger is bound to a different protocol lock or "
                "evaluation plan or final run set or source inventory"
            )
        return existing

    existing = validate_existing() if destination.exists() else None
    authorization = {
        "protocol_sha256": protocol_sha256,
        "protocol_lock_sha256": lock_sha256,
        "evaluation_plan_sha256": plan_sha256,
        "final_run_set_sha256": run_set_sha256,
        "source_inventory_sha256": source_manifest_sha256,
    }
    capacity = None
    capacity_time = None
    if protocol.protocol_id == "protocol-v3":
        from pose_embed.opening_capacity_v3 import (
            record_opening_capacity,
            validate_opening_capacity,
        )

        if existing is not None:
            capacity = existing.opening_capacity
            if capacity is None:
                raise ValueError("v3 opening is missing its fresh capacity evidence")
        elif (paths.root / OPENING).exists():
            # A common event already opened the dataset; recover only its bound receipt.
            common = json.loads((paths.root / OPENING).read_text())
            capacity = ArtifactBinding.model_validate(
                common.get("authorization", {}).get("opening_capacity")
            )
            validate_dataset_opening(
                version=protocol.protocol_id,
                authorization=authorization
                | {"opening_capacity": capacity.model_dump()},
            )
        else:
            capacity = record_opening_capacity(protocol, lock_sha256)
        capacity_time = validate_opening_capacity(protocol, capacity, lock_sha256)
        authorization["opening_capacity"] = capacity.model_dump()
    verify_validation_proofs()
    common = record_dataset_opening(
        version=protocol.protocol_id, authorization=authorization
    )
    if capacity_time is not None and capacity_time > datetime.fromisoformat(
        common["opened_at"]
    ):
        raise ValueError("opening capacity evidence must precede the dataset opening")
    if existing is not None:
        return existing
    destination.parent.mkdir(parents=True, exist_ok=True)
    ledger = TestOpeningLedger(
        schema_version=2,
        event_id=str(uuid.uuid4()),
        protocol_sha256=protocol_sha256,
        protocol_lock_sha256=lock_sha256,
        evaluation_plan_sha256=plan_sha256,
        final_run_set_sha256=run_set_sha256,
        source_inventory_manifest_sha256=source_manifest_sha256,
        source_file_count=manifest_validation.source_file_count,
        source_files_sha256=manifest_validation.source_files_sha256,
        opened_at=datetime.now(UTC),
        opening_capacity=capacity,
    )
    verify_validation_proofs()
    write_immutable_json(destination, ledger.model_dump(mode="json"))
    return ledger
