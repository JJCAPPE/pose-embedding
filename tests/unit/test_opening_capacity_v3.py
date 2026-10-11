from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from pose_embed import opening_capacity_v3 as opening
from pose_embed.config import load_protocol
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.protocol_v3_campaign import CapacityReceipt
from pose_embed.provenance import sha256_file


def _bind(root, name, value):
    path = root / name
    path.write_text(json.dumps(value))
    return {"relative_path": name, "sha256": sha256_file(path)}


@pytest.fixture
def capacity(tmp_path):
    from test_campaign_v3 import _capacity

    payload = _capacity()
    payload["recorded_at"] = "2026-10-10T12:00:00Z"
    payload["remaining_peak_bytes"] = 100 * opening.GIB
    payload["allocation_calendar"] = _bind(
        tmp_path,
        "calendar.json",
        {
            "recorded_at": payload["recorded_at"],
            "recorded_by": "researcher",
            "access": "ordinary_queued_access",
            "reserved": False,
            "windows": [
                {
                    "starts_at": f"{day}T12:00:00Z",
                    "ends_at": f"{day}T16:00:00Z",
                    "job_wall_limit_seconds": 7200,
                    "queue_allowance_seconds": 3600,
                    "concurrent_scientific_processes": 1,
                }
                for day in ("2026-11-01", "2026-11-30")
            ],
        },
    )
    payload["researcher_availability"] = _bind(
        tmp_path,
        "availability.json",
        {
            "recorded_at": payload["recorded_at"],
            "recorded_by": "researcher",
            "source": "explicit confirmation",
            "normal_weekly_hours": 5,
            "contingency_weekly_hours": 10,
            "guaranteed_weekly_hours": {"2026-12-07": 5, "2026-12-14": 5},
        },
    )
    return CapacityReceipt.model_validate(payload)


def _resources(root):
    return {
        "job_id": "123",
        "tmpdir": "/scratch/123",
        "nslots": "4",
        "hostname": "scc-w01.bu.edu",
        "cuda_visible_devices": "2",
        "qstat_job": (
            "hard resource_list: mem_per_core=8G,gpus=1,gpu_type=L40S,h_rt=12:00:00\n"
        ),
        "qstat_xml": """<job_info><queue_info><job_list state="running">
          <JB_job_number>123</JB_job_number><state>r</state>
          <JAT_start_time>2026-11-30T07:00:00</JAT_start_time>
          <queue_name>gpu@scc-w01</queue_name><slots>4</slots>
          </job_list></queue_info></job_info>""",
        "measured_at": "2026-11-30T13:00:00Z",
        "project_quota_report": f"{root} 2000 0 1000 0\n",
        "nvidia_smi": "raw report retained",
        "system_memory": "MemAvailable: 134217728 kB\n",
        "filesystem_free_bytes": 1000 * opening.GIB,
        "gpu_count": 1,
        "gpu_name": "NVIDIA L40S",
        "gpu_free_bytes": 40 * opening.GIB,
        "gpu_total_bytes": 48 * opening.GIB,
    }


@pytest.fixture
def configured(tmp_path, monkeypatch, capacity):
    protocol = load_protocol("configs/protocol.v3.yaml")
    binding = ArtifactBinding.model_validate(
        _bind(tmp_path, "capacity.json", capacity.model_dump(mode="json"))
    )
    monkeypatch.setattr(
        opening, "resolve_scientific_paths", lambda _: SimpleNamespace(root=tmp_path)
    )
    monkeypatch.setattr(opening, "_capacity", lambda *_: (capacity, binding))
    monkeypatch.setattr(
        opening,
        "_capture_resources",
        lambda root, resources: resources.update(_resources(root)),
    )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 30, 13, tzinfo=UTC)

    monkeypatch.setattr(opening, "datetime", Clock)
    return protocol, tmp_path


def test_fresh_capacity_passes_and_archival_validation_never_measures(
    configured, monkeypatch
):
    protocol, root = configured
    binding = opening.record_opening_capacity(protocol, "a" * 64)
    receipt = json.loads((root / binding.relative_path).read_text())
    assert receipt["status"] == "passed"
    assert receipt["calendar_summary"]["usable_evaluation_seconds"] == 7200
    assert receipt["calendar_summary"]["confirmed_delivery_hours"] == 10

    def forbidden(*args, **kwargs):
        raise AssertionError("historical validation must not probe resources")

    monkeypatch.setattr(opening, "_capture_resources", forbidden)
    monkeypatch.setattr(opening.subprocess, "check_output", forbidden)

    class LaterClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2027, 1, 1, tzinfo=UTC)

    monkeypatch.setattr(opening, "datetime", LaterClock)
    assert opening.validate_opening_capacity(protocol, binding, "a" * 64) == datetime(
        2026, 11, 30, 13, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("hostname", "other-host", "this host/slots"),
        ("nslots", "8", "this host/slots"),
        ("gpu_count", 2, "one L40S"),
        ("gpu_name", "NVIDIA A100", "one L40S"),
        ("gpu_free_bytes", 15 * opening.GIB, "GPU VRAM"),
        ("system_memory", "MemAvailable: 16777216 kB\n", "host RAM"),
        ("filesystem_free_bytes", 200 * opening.GIB, "storage reserve"),
    ],
)
def test_resource_failures_retain_attempt_without_opening(
    configured, monkeypatch, field, value, message
):
    protocol, root = configured
    resources = _resources(root) | {field: value}
    monkeypatch.setattr(
        opening, "_capture_resources", lambda _, target: target.update(resources)
    )
    for _ in range(2):
        with pytest.raises(ValueError, match=message):
            opening.record_opening_capacity(protocol, "a" * 64)
    receipts = list((root / "study-v3/operations/opening-capacity").glob("*.json"))
    assert len(receipts) == 2
    assert all(json.loads(path.read_text())["status"] == "failed" for path in receipts)
    assert not (root / "locks/dataset-opening.json").exists()
    assert not (root / protocol.test_access.opening_ledger_relative_path).exists()
    failed = ArtifactBinding(
        relative_path=str(receipts[0].relative_to(root)),
        sha256=sha256_file(receipts[0]),
    )
    with pytest.raises(ValueError, match="passed status"):
        opening.validate_opening_capacity(protocol, failed, "a" * 64)


def test_scheduler_and_quota_requests_are_replayed(tmp_path, capacity):
    resources = _resources(tmp_path)
    resources["qstat_xml"] = resources["qstat_xml"].replace("<state>r", "<state>s")
    with pytest.raises(ValueError, match="not running"):
        opening._validate_resources(tmp_path, resources, capacity)
    resources = _resources(tmp_path)
    resources["qstat_job"] = resources["qstat_job"].replace("8G", "4G")
    with pytest.raises(ValueError, match="host RAM"):
        opening._validate_resources(tmp_path, resources, capacity)
    resources = _resources(tmp_path)
    resources["project_quota_report"] = f"{tmp_path} 2000 0 1900 0\n"
    with pytest.raises(ValueError, match="storage reserve"):
        opening._validate_resources(tmp_path, resources, capacity)


def test_fresh_calendar_rejects_expired_or_fragmented_windows(tmp_path, capacity):
    for when in (
        datetime(2026, 11, 30, 15, tzinfo=UTC),
        datetime(2026, 12, 1, tzinfo=UTC),
        datetime(2026, 12, 7, 12, tzinfo=UTC),
    ):
        with pytest.raises(ValueError, match="calendar|deadline"):
            opening._calendar_capacity(tmp_path, capacity, when)
    no_delivery = capacity.model_copy(
        update={
            "researcher_work_hours": capacity.researcher_work_hours
            | {"final_analysis_delivery": 10}
        }
    )
    with pytest.raises(ValueError, match="delivery hours"):
        opening._calendar_capacity(
            tmp_path, no_delivery, datetime(2026, 11, 30, 13, tzinfo=UTC)
        )


def test_remaining_allocated_wall_time_uses_actual_start_and_slack(tmp_path, capacity):
    resources = _resources(tmp_path)
    summary = opening._validate_resources(tmp_path, resources, capacity)
    assert summary["remaining_job_wall_seconds"] == 11 * 3600
    resources["qstat_job"] = resources["qstat_job"].replace("12:00:00", "43200")
    resources["qstat_xml"] = resources["qstat_xml"].replace(
        "2026-11-30T07:00:00", "2026-11-30T12:00:00+00:00"
    )
    assert opening._validate_resources(tmp_path, resources, capacity) == summary
    resources["qstat_job"] = resources["qstat_job"].replace("43200", "3674")
    with pytest.raises(ValueError, match="remaining scheduler wall time"):
        opening._validate_resources(tmp_path, resources, capacity)
    resources["qstat_job"] = resources["qstat_job"].replace("3674", "3675")
    assert (
        opening._validate_resources(tmp_path, resources, capacity)[
            "remaining_job_wall_seconds"
        ]
        == 75
    )


def test_archival_capacity_rejects_changed_hash_and_identity(configured):
    protocol, root = configured
    binding = opening.record_opening_capacity(protocol, "a" * 64)
    with pytest.raises(ValueError, match="identity"):
        opening.validate_opening_capacity(protocol, binding, "b" * 64)
    path = root / binding.relative_path
    payload = json.loads(path.read_text())
    payload["resources"]["gpu_free_bytes"] = 1
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="hash mismatch"):
        opening.validate_opening_capacity(protocol, binding, "a" * 64)
    tampered = ArtifactBinding(
        relative_path=binding.relative_path, sha256=sha256_file(path)
    )
    with pytest.raises(ValueError, match="GPU VRAM"):
        opening.validate_opening_capacity(protocol, tampered, "a" * 64)


def test_capture_rejects_login_node_before_running_commands(tmp_path, monkeypatch):
    monkeypatch.delenv("JOB_ID", raising=False)
    resources = {}
    with pytest.raises(ValueError, match="scheduler allocation"):
        opening._capture_resources(tmp_path, resources)
    assert resources["job_id"] == ""
    assert "qstat_job" not in resources
