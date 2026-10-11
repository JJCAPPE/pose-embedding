from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from pose_embed.config import load_protocol
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.protocol import _validate_head_checkpoint, protocol_digest
from pose_embed.protocol_v3 import V3SelectionAuthorization
from pose_embed.protocol_v3_campaign import (
    CapacityReceipt,
    ResearcherAvailability,
    SelectionLedger,
    SelectionMatrix,
    _selection_table,
    _validate_capacity_availability,
)
from pose_embed.provenance import sha256_file
from pose_embed.training.runner import NormalizedLinearHead, _state_dict_digest


def _binding(root, path, value):
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value))
    return {"relative_path": path, "sha256": sha256_file(destination)}


def _matrix(protocol):
    return {
        "schema_version": 1,
        "protocol_sha256": protocol_digest(protocol),
        "slots": [
            {
                "method": method,
                "learning_rate": rate,
                "seed": seed,
                "config": {
                    "relative_path": f"configs/{method}-{rate}-{seed}.json",
                    "sha256": "a" * 64,
                },
            }
            for method in protocol.objectives.core
            for rate in (1e-4, 3e-4, 1e-3)
            for seed in (7, 17, 29)
        ],
    }


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    from pose_embed import protocol_v3_campaign

    protocol = load_protocol("configs/protocol.v3.yaml")
    matrix = _matrix(protocol)
    matrix_binding = _binding(tmp_path, "matrix.json", matrix)
    timestamp = datetime.now(UTC) - timedelta(days=1)
    authorization = SimpleNamespace(
        run_matrix=ArtifactBinding.model_validate(matrix_binding), recorded_at=timestamp
    )
    slots = []
    for slot in matrix["slots"]:
        name = f"{slot['method']}-{slot['learning_rate']}-{slot['seed']}"
        attempt = {
            "attempt_id": name,
            "protocol_sha256": protocol_digest(protocol),
            "stage": "development_selection",
            "scientific_use_allowed": True,
            "objective": slot["method"],
            "seed": slot["seed"],
            "config_sha256": "a" * 64,
            "started_at": (timestamp + timedelta(hours=1)).isoformat(),
        }
        outcome = {
            "attempt_id": name,
            "status": "success",
            "ended_at": (timestamp + timedelta(hours=2)).isoformat(),
        }
        record = {
            "attempt": _binding(tmp_path, f"{name}/attempt.json", attempt),
            "outcome": _binding(tmp_path, f"{name}/outcome.json", outcome),
            "failure": None,
        }
        _binding(
            tmp_path, f"{name}/epoch-020.json", {"scores": {"top1": 0.5, "mrr": 0.6}}
        )
        slots.append(
            {key: slot[key] for key in ("method", "learning_rate", "seed")}
            | {"attempts": [record]}
        )
    ledger = {
        "schema_version": 1,
        "protocol_sha256": protocol_digest(protocol),
        "run_matrix_sha256": matrix_binding["sha256"],
        "slots": slots,
    }
    monkeypatch.setattr(
        protocol_v3_campaign,
        "resolve_scientific_paths",
        lambda protocol: SimpleNamespace(root=tmp_path),
    )
    monkeypatch.setattr(
        protocol_v3_campaign,
        "_campaign_binding",
        lambda root, protocol, binding: protocol_v3_campaign._bound_file(root, binding),
    )

    def validate(path, *, stage):
        assert stage == "development_selection"
        attempt = json.loads((path / "attempt.json").read_text())
        return {
            "initialization_sha256": str(attempt["seed"]),
            "batch_plan_sha256": str(attempt["seed"]),
        }

    monkeypatch.setattr("pose_embed.training.runner.validate_v3_training_run", validate)
    return protocol, authorization, ledger, tmp_path


def test_matrix_cannot_omit_or_duplicate_one_slot():
    protocol = load_protocol("configs/protocol.v3.yaml")
    matrix = _matrix(protocol)
    assert len(SelectionMatrix.model_validate(matrix).slots) == 27
    matrix["slots"][-1] = matrix["slots"][0]
    with pytest.raises(ValueError, match="27 unique"):
        SelectionMatrix.model_validate(matrix)


def test_revision_binding_rejects_artifacts_outside_campaign(tmp_path):
    from pose_embed.protocol_v3_campaign import _campaign_binding

    protocol = load_protocol("configs/protocol.v3.yaml")
    wrong = ArtifactBinding.model_validate(_binding(tmp_path, "elsewhere.json", {}))
    with pytest.raises(ValueError, match="different execution revision"):
        _campaign_binding(tmp_path, protocol, wrong)
    valid = ArtifactBinding.model_validate(
        _binding(tmp_path, "study-v3/receipt.json", {})
    )
    assert _campaign_binding(tmp_path, protocol, valid).is_file()


def test_all_three_seeds_and_exact_clean_tie_breaks(campaign):
    protocol, authorization, ledger, root = campaign
    candidates, rates = _selection_table(
        protocol, authorization, SelectionLedger.model_validate(ledger)
    )
    assert len(candidates) == 9
    assert set(rates.values()) == {1e-4}
    for seed in (7, 17, 29):
        path = root / f"contextual-0.001-{seed}/epoch-020.json"
        path.write_text(json.dumps({"scores": {"top1": 0.5, "mrr": 0.7}}))
    _, rates = _selection_table(
        protocol, authorization, SelectionLedger.model_validate(ledger)
    )
    assert rates["contextual"] == 0.001
    slot = ledger["slots"][-1]
    record = slot["attempts"][0]
    record["failure"] = "numerical"
    record["outcome"] = _binding(
        root,
        record["outcome"]["relative_path"],
        {
            "attempt_id": "contextual-0.001-29",
            "status": "failed",
            "ended_at": datetime.now(UTC).isoformat(),
        },
    )
    record["evidence"] = [_binding(root, "failure.json", {"nonfinite": True})]
    candidates, rates = _selection_table(
        protocol, authorization, SelectionLedger.model_validate(ledger)
    )
    assert rates["contextual"] == 1e-4
    assert candidates[-1]["eligible"] is False
    assert candidates[-1]["mean_top1"] is None


def test_ledger_hash_tampering_and_precompletion_lock_are_rejected(campaign):
    protocol, authorization, ledger, root = campaign
    with pytest.raises(ValueError, match="chronology"):
        _selection_table(
            protocol,
            authorization,
            SelectionLedger.model_validate(ledger),
            not_after=authorization.recorded_at,
        )
    path = root / ledger["slots"][0]["attempts"][0]["attempt"]["relative_path"]
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        _selection_table(
            protocol, authorization, SelectionLedger.model_validate(ledger)
        )


def test_implementation_failure_blocks_selection_stage(campaign):
    protocol, authorization, ledger, root = campaign
    record = ledger["slots"][0]["attempts"][0]
    attempt = json.loads((root / record["attempt"]["relative_path"]).read_text())
    record["failure"] = "implementation"
    record["outcome"] = _binding(
        root,
        record["outcome"]["relative_path"],
        {
            "attempt_id": attempt["attempt_id"],
            "status": "failed",
            "ended_at": datetime.now(UTC).isoformat(),
        },
    )
    record["evidence"] = [_binding(root, "defect.json", {"wrong_formula": True})]
    with pytest.raises(ValueError, match="implementation/provenance defect blocks"):
        _selection_table(
            protocol, authorization, SelectionLedger.model_validate(ledger)
        )


def test_retry_cannot_follow_a_numerical_failure(campaign):
    protocol, authorization, ledger, root = campaign
    slot = ledger["slots"][0]
    original = slot["attempts"][0]
    attempt_path = root / original["attempt"]["relative_path"]
    attempt = json.loads(attempt_path.read_text())
    old_id = attempt["attempt_id"]
    original["failure"] = "numerical"
    original["outcome"] = _binding(
        root,
        original["outcome"]["relative_path"],
        {
            "attempt_id": old_id,
            "status": "failed",
            "ended_at": datetime.now(UTC).isoformat(),
        },
    )
    original["evidence"] = [_binding(root, "failure.json", {"nonfinite": True})]
    attempt["attempt_id"] = "retry"
    slot["attempts"].append(
        {
            "attempt": _binding(root, "retry/attempt.json", attempt),
            "outcome": None,
            "failure": "unresolved",
            "retry_of": old_id,
        }
    )
    with pytest.raises(ValueError, match="only evidenced infrastructure"):
        _selection_table(
            protocol, authorization, SelectionLedger.model_validate(ledger)
        )


def test_ledger_cannot_omit_preserved_selection_attempt(campaign):
    protocol, authorization, ledger, root = campaign
    original = root / ledger["slots"][0]["attempts"][0]["attempt"]["relative_path"]
    attempt = json.loads(original.read_text())
    attempt["attempt_id"] = "omitted-failure"
    _binding(root, "omitted-failure/attempt.json", attempt)
    with pytest.raises(ValueError, match="omits a preserved"):
        _selection_table(
            protocol, authorization, SelectionLedger.model_validate(ledger)
        )


def _capacity():
    binding = {"relative_path": "evidence.json", "sha256": "a" * 64}
    return {
        "schema_version": 1,
        "protocol_sha256": "a" * 64,
        "design_lock_sha256": "b" * 64,
        "recorded_at": datetime.now(UTC).isoformat(),
        "recorded_by": "fixture",
        "scientific_use_allowed": True,
        "status": "passed",
        "evidence": [binding],
        "code_sha256": {},
        "filesystem_free_bytes": 10**12,
        "quota_remaining_bytes": 10**12,
        "remaining_peak_bytes": 10**11,
        "compute_slack": 1.25,
        "researcher_slack": 1.25,
        "allocation_calendar": binding,
        "researcher_availability": binding,
        "final_lock_date": "2026-11-29",
        "novel_completion_date": "2026-12-06",
        "measured_stage_seconds": {
            stage: 1.0
            for stage in (
                "hashing",
                "loading",
                "preprocessing",
                "encoding",
                "projection",
                "artifact_validation",
                "retrieval",
                "serialization",
                "final_resident_training",
            )
        },
        "peak_host_bytes": 1,
        "peak_gpu_bytes": 1,
        "host_memory_limit_bytes": 2,
        "gpu_memory_limit_bytes": 2,
        "maximum_job_seconds": 60.0,
        "retained_bytes": 1,
        "full_size_resident_rows": 95001,
        "timing_optimization_actions": 80,
        "remaining_preopening_seconds": 60.0,
        "remaining_evaluation_seconds": 60.0,
        "researcher_work_hours": {
            name: 1.0
            for name in (
                "implementation_review",
                "release_revalidation",
                "corruption_audit",
                "analysis_report_verification",
                "resource_planning",
                "selection_final_supervision",
                "final_analysis_delivery",
            )
        },
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("quota_remaining_bytes", 200 * 2**30),
        ("compute_slack", 1.24),
        ("researcher_slack", 1.24),
        ("final_lock_date", "2026-11-30"),
        ("novel_completion_date", "2026-12-07"),
        ("scientific_use_allowed", False),
        ("full_size_resident_rows", 76013),
        ("peak_host_bytes", 3),
        ("peak_gpu_bytes", 3),
    ],
)
def test_capacity_fails_closed_for_resource_or_evidence_shortfall(field, value):
    payload = _capacity()
    CapacityReceipt.model_validate(payload)
    payload[field] = value
    with pytest.raises(ValueError):
        CapacityReceipt.model_validate(payload)


def test_unchanged_finite_head_is_only_allowed_when_explicit(tmp_path):
    from test_training_v3 import _config

    config = _config()
    torch.manual_seed(config.seed)
    head = NormalizedLinearHead(config.input_dimension, config.embedding_dimension)
    digest = _state_dict_digest(head)
    path = tmp_path / "head.pt"
    torch.save(
        {"state_dict": head.state_dict(), "config": config.model_dump(mode="json")},
        path,
    )
    with pytest.raises(ValueError, match="untrained initialization"):
        _validate_head_checkpoint(path, config, initialization_sha256=digest)
    _validate_head_checkpoint(
        path, config, initialization_sha256=digest, allow_unchanged=True
    )


def test_authorization_schema_does_not_accept_fixture_assertion():
    payload = json.loads(
        Path("configs/selection-authorization.v3.template.json").read_text()
    )
    with pytest.raises(ValueError):
        V3SelectionAuthorization.model_validate(payload)


def test_conservative_researcher_hours_preserve_contingency_and_holiday():
    payload = {
        "recorded_at": "2026-10-10T12:00:00Z",
        "recorded_by": "researcher",
        "source": "explicit availability confirmation",
        "normal_weekly_hours": 5,
        "contingency_weekly_hours": 10,
        "guaranteed_weekly_hours": {"2026-11-16": 5, "2026-11-23": 0},
    }
    ResearcherAvailability.model_validate(payload)
    payload["guaranteed_weekly_hours"]["2026-11-16"] = 10
    with pytest.raises(ValueError, match="authorized contingency"):
        ResearcherAvailability.model_validate(payload)
    payload["contingency_weeks"] = ["2026-11-16"]
    ResearcherAvailability.model_validate(payload)
    payload["guaranteed_weekly_hours"]["2026-11-16"] = 10.1
    with pytest.raises(ValueError, match="authorized contingency"):
        ResearcherAvailability.model_validate(payload)
    payload["guaranteed_weekly_hours"]["2026-11-16"] = 5
    with pytest.raises(ValueError, match="authorized contingency"):
        ResearcherAvailability.model_validate(payload)


def test_capacity_uses_dated_queued_windows_and_preserves_delivery_hours(tmp_path):
    payload = _capacity()
    payload["recorded_at"] = "2026-10-10T12:00:00Z"
    allocation = {
        "recorded_at": payload["recorded_at"],
        "recorded_by": "researcher",
        "access": "ordinary_queued_access",
        "reserved": False,
        "windows": [
            {
                "starts_at": f"{day}T12:00:00Z",
                "ends_at": f"{day}T14:00:00Z",
                "job_wall_limit_seconds": 3600,
                "queue_allowance_seconds": 3600,
                "concurrent_scientific_processes": 1,
            }
            for day in ("2026-11-01", "2026-11-30")
        ],
    }
    availability = {
        "recorded_at": payload["recorded_at"],
        "recorded_by": "researcher",
        "source": "confirmed hours",
        "normal_weekly_hours": 5,
        "contingency_weekly_hours": 10,
        "guaranteed_weekly_hours": {
            "2026-11-02": 5,
            "2026-11-09": 5,
            "2026-11-23": 0,
            "2026-12-07": 5,
            "2026-12-14": 5,
        },
    }
    payload["allocation_calendar"] = _binding(tmp_path, "calendar.json", allocation)
    payload["researcher_availability"] = _binding(tmp_path, "hours.json", availability)
    _validate_capacity_availability(tmp_path, CapacityReceipt.model_validate(payload))
    with pytest.raises(ValueError, match="past allocation window"):
        _validate_capacity_availability(
            tmp_path,
            CapacityReceipt.model_validate(payload),
            as_of=datetime(2026, 11, 2, tzinfo=UTC),
        )
    payload["researcher_work_hours"]["final_analysis_delivery"] = 9
    with pytest.raises(ValueError, match="planned hours"):
        _validate_capacity_availability(
            tmp_path, CapacityReceipt.model_validate(payload)
        )
    payload["researcher_work_hours"]["final_analysis_delivery"] = 1
    payload["remaining_preopening_seconds"] = 3600
    with pytest.raises(ValueError, match="allocation windows"):
        _validate_capacity_availability(
            tmp_path, CapacityReceipt.model_validate(payload)
        )


def test_capacity_cannot_split_a_complete_job_across_short_windows(tmp_path):
    payload = _capacity()
    payload["recorded_at"] = "2026-10-10T12:00:00Z"
    windows = []
    for day in ("2026-11-01", "2026-11-30"):
        for index in range(8):
            start = datetime.fromisoformat(f"{day}T12:00:00+00:00") + timedelta(
                seconds=20 * index
            )
            windows.append(
                {
                    "starts_at": start.isoformat(),
                    "ends_at": (start + timedelta(seconds=10)).isoformat(),
                    "job_wall_limit_seconds": 3600,
                    "queue_allowance_seconds": 0,
                    "concurrent_scientific_processes": 1,
                }
            )
    payload["allocation_calendar"] = _binding(
        tmp_path,
        "calendar.json",
        {
            "recorded_at": payload["recorded_at"],
            "recorded_by": "researcher",
            "access": "ordinary_queued_access",
            "reserved": False,
            "windows": windows,
        },
    )
    payload["researcher_availability"] = _binding(
        tmp_path,
        "hours.json",
        {
            "recorded_at": payload["recorded_at"],
            "recorded_by": "researcher",
            "source": "confirmed hours",
            "normal_weekly_hours": 5,
            "contingency_weekly_hours": 10,
            "guaranteed_weekly_hours": {
                "2026-11-02": 5,
                "2026-11-09": 5,
                "2026-12-07": 5,
            },
        },
    )
    with pytest.raises(ValueError, match="usable allocation windows"):
        _validate_capacity_availability(
            tmp_path, CapacityReceipt.model_validate(payload)
        )
