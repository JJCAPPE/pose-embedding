"""Atomic, immutable evidence for the one-time novel-test opening."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pose_embed.config import ProtocolConfig
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
from pose_embed.provenance import sha256_file


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


def open_final_test_once(
    protocol: ProtocolConfig,
    *,
    protocol_sha256: str,
) -> TestOpeningLedger:
    """Verify the full inventory, then create or validate one opening event."""
    paths = resolve_scientific_paths(protocol)
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

    if destination.exists():
        return validate_existing()
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
    )
    encoded = (
        json.dumps(ledger.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return validate_existing()
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return ledger
