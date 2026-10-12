"""Fresh SCC capacity evidence for the one-way novel opening, with archival replay."""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from pose_embed.config_v3 import ArtifactBinding
from pose_embed.motionbert_reproducibility import parse_project_quota
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.protocol_v3 import (
    V3FinalLock,
    V3SelectionAuthorization,
    _bound_file,
)
from pose_embed.protocol_v3_campaign import (
    RESOURCE_CLASSES,
    AllocationCalendar,
    CapacityReceipt,
    ResearcherAvailability,
    _read,
    _receipt,
)
from pose_embed.provenance import sha256_file, write_immutable_json
from pose_embed.validation_proofs import verify_validation_proofs

GIB = 2**30


def _capacity(protocol, lock_sha256):
    paths = resolve_scientific_paths(protocol)
    if sha256_file(paths.protocol_lock) != lock_sha256:
        raise ValueError("opening capacity protocol lock hash differs")
    lock = V3FinalLock.model_validate_json(paths.protocol_lock.read_text())
    authorization_path = (
        paths.root / protocol.test_access.selection_authorization_relative_path
    )
    if sha256_file(authorization_path) != lock.selection_authorization_sha256:
        raise ValueError("opening capacity selection authorization hash differs")
    authorization = V3SelectionAuthorization.model_validate_json(
        authorization_path.read_text()
    )
    if (
        authorization.protocol_sha256 != protocol_digest(protocol)
        or authorization.design_lock_sha256 != lock.design_lock_sha256
    ):
        raise ValueError("opening capacity selection identity differs")
    capacity = _receipt(
        paths.root,
        authorization.capacity_report,
        CapacityReceipt,
        protocol,
        authorization,
    )
    return capacity, authorization.capacity_report


def _calendar_capacity(root, capacity, recorded_at):
    """Count only still-usable evaluation windows; completed training is excluded."""
    calendar = _read(root, capacity.allocation_calendar, AllocationCalendar)
    availability = _read(root, capacity.researcher_availability, ResearcherAvailability)
    timezone = ZoneInfo("America/New_York")
    if (
        recorded_at.tzinfo is None
        or capacity.recorded_at > recorded_at
        or calendar.recorded_at > capacity.recorded_at
        or availability.recorded_at > capacity.recorded_at
        or recorded_at.astimezone(timezone).date() > capacity.novel_completion_date
    ):
        raise ValueError("opening capacity chronology or novel deadline differs")
    usable_seconds = dict.fromkeys(RESOURCE_CLASSES, 0.0)
    for window in calendar.windows:
        if (
            window.starts_at.astimezone(timezone).date() <= capacity.final_lock_date
            or window.ends_at.astimezone(timezone).date()
            > capacity.novel_completion_date
        ):
            continue
        seconds = (
            window.ends_at - max(recorded_at, window.starts_at)
        ).total_seconds() - window.queue_allowance_seconds
        resource = window.resource_class
        if capacity.maximum_job_seconds_by_resource[
            resource
        ] * capacity.compute_slack <= min(seconds, window.job_wall_limit_seconds):
            usable_seconds[resource] += seconds
    required_seconds = {
        resource: capacity.remaining_evaluation_seconds_by_resource[resource]
        * capacity.compute_slack
        for resource in RESOURCE_CLASSES
    }
    delivery_hours = sum(
        hours
        for day, hours in availability.guaranteed_weekly_hours.items()
        if date(2026, 12, 7) <= day <= date(2026, 12, 18)
    )
    required_hours = (
        capacity.researcher_work_hours["final_analysis_delivery"]
        * capacity.researcher_slack
    )
    if (
        any(
            usable_seconds[resource] < required_seconds[resource]
            for resource in RESOURCE_CLASSES
        )
        or delivery_hours < required_hours
    ):
        raise ValueError("fresh calendar or delivery hours do not fit remaining work")
    return {
        "usable_evaluation_seconds_by_resource": usable_seconds,
        "required_evaluation_seconds_by_resource": required_seconds,
        "confirmed_delivery_hours": delivery_hours,
        "required_delivery_hours": required_hours,
    }


def _capture_resources(root, resources):
    """Keep partial raw evidence in the receipt even if a later command fails."""
    import torch

    resources.update(
        job_id=os.environ.get("JOB_ID", ""),
        tmpdir=os.environ.get("TMPDIR", ""),
        nslots=os.environ.get("NSLOTS", ""),
        hostname=socket.gethostname(),
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    )
    if (
        not resources["job_id"].isdigit()
        or not resources["nslots"].isdigit()
        or not Path(resources["tmpdir"]).is_dir()
        or not resources["tmpdir"]
    ):
        raise ValueError("opening requires a live SCC scheduler allocation")
    for label, command in (
        ("qstat_job", ["qstat", "-j", resources["job_id"]]),
        ("qstat_xml", ["qstat", "-xml"]),
        ("project_quota_report", ["pquota", "textconv"]),
        ("nvidia_smi", ["nvidia-smi"]),
    ):
        resources[label] = subprocess.check_output(
            command, text=True, timeout=30, env=os.environ | {"LC_ALL": "C"}
        )
    resources["system_memory"] = Path("/proc/meminfo").read_text()
    resources["filesystem_free_bytes"] = shutil.disk_usage(root).free
    resources["gpu_count"] = torch.cuda.device_count()
    if resources["gpu_count"] != 1 or not resources["cuda_visible_devices"]:
        raise ValueError("opening requires exactly one scheduler-visible GPU")
    resources["gpu_name"] = torch.cuda.get_device_name(0)
    resources["gpu_free_bytes"], resources["gpu_total_bytes"] = torch.cuda.mem_get_info(
        0
    )
    resources["measured_at"] = datetime.now(UTC).isoformat()


def _validate_resources(root, resources, capacity):
    jobs = ElementTree.fromstring(resources["qstat_xml"]).findall(".//job_list")
    jobs = [job for job in jobs if job.findtext("JB_job_number") == resources["job_id"]]
    if len(jobs) != 1:
        raise ValueError("opening scheduler job is absent or ambiguous")
    job = jobs[0]
    queue_host = (job.findtext("queue_name") or "").partition("@")[2]
    if (
        job.get("state") != "running"
        or job.findtext("state") != "r"
        or queue_host.split(".")[0] != resources["hostname"].split(".")[0]
        or int(job.findtext("slots", "0")) != int(resources["nslots"])
    ):
        raise ValueError("opening scheduler job is not running on this host/slots")
    hard = re.search(r"^hard resource_list:\s*(.+)$", resources["qstat_job"], re.M)
    if hard is None:
        raise ValueError("opening scheduler hard resource request is missing")
    requested = dict(part.strip().split("=", 1) for part in hard[1].split(","))
    wall_limit = requested.get("h_rt", "")
    if re.fullmatch(r"\d+", wall_limit):
        wall_seconds = int(wall_limit)
    elif re.fullmatch(r"\d+:[0-5]\d:[0-5]\d", wall_limit):
        hours, minutes, seconds = map(int, wall_limit.split(":"))
        wall_seconds = hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError("opening scheduler wall-time limit is missing or invalid")
    started = datetime.fromisoformat(job.findtext("JAT_start_time", ""))
    # Grid Engine's unqualified SCC timestamps use the Boston local timezone.
    if started.tzinfo is None:
        started = started.replace(tzinfo=ZoneInfo("America/New_York"))
    measured = datetime.fromisoformat(resources["measured_at"])
    if measured.tzinfo is None or measured < started:
        raise ValueError("opening scheduler runtime chronology differs")
    remaining_wall_seconds = wall_seconds - (measured - started).total_seconds()
    required_wall_seconds = (
        capacity.maximum_job_seconds_by_resource["gpu"] * capacity.compute_slack
    )
    if remaining_wall_seconds < required_wall_seconds:
        raise ValueError(
            "complete opening job does not fit remaining scheduler wall time"
        )
    memory = re.fullmatch(r"(\d+(?:\.\d+)?)([GM])", requested.get("mem_per_core", ""))
    if (
        memory is None
        or requested.get("gpus") != "1"
        or requested.get("gpu_type") != "L40S"
        or resources["gpu_count"] != 1
        or resources["gpu_name"] != "NVIDIA L40S"
        or not resources["cuda_visible_devices"]
    ):
        raise ValueError("opening requires one L40S and explicit per-core memory")
    allocated_memory = (
        float(memory[1])
        * (GIB if memory[2] == "G" else 2**20)
        * int(resources["nslots"])
    )
    available_memory = re.search(
        r"^MemAvailable:\s+(\d+)\s+kB$", resources["system_memory"], re.M
    )
    if available_memory is None or min(
        allocated_memory, int(available_memory[1]) * 1024
    ) < max(32 * GIB, capacity.peak_host_bytes):
        raise ValueError("opening has insufficient allocated or available host RAM")
    if min(resources["gpu_free_bytes"], resources["gpu_total_bytes"]) < max(
        16 * GIB, capacity.peak_gpu_bytes
    ):
        raise ValueError("opening has insufficient allocated GPU VRAM")
    quota = parse_project_quota(resources["project_quota_report"], root)
    required_storage = 200 * GIB + 1.25 * capacity.remaining_peak_bytes
    if min(resources["filesystem_free_bytes"], quota["free_bytes"]) < required_storage:
        raise ValueError("opening capacity storage reserve is insufficient")
    return {
        "resource_class": "gpu",
        "required_job_wall_seconds": required_wall_seconds,
        "remaining_job_wall_seconds": remaining_wall_seconds,
        "host_memory_limit_bytes": int(allocated_memory),
        "system_memory_available_bytes": int(available_memory[1]) * 1024,
        "quota_remaining_bytes": quota["free_bytes"],
        "required_storage_bytes": required_storage,
    }


def _directory(protocol, root):
    revision = Path(protocol.test_access.resolved_protocol_relative_path).parent.parent
    return root / revision / "operations/opening-capacity"


def record_opening_capacity(protocol, protocol_lock_sha256) -> ArtifactBinding:
    """Called under the opening guard after all nine final heads are validated."""
    root = resolve_scientific_paths(protocol).root
    receipt_path = _directory(protocol, root) / f"{uuid.uuid4()}.json"
    receipt = {
        "schema_version": 2,
        "kind": "v3_fresh_opening_capacity",
        "protocol_sha256": protocol_digest(protocol),
        "protocol_lock_sha256": protocol_lock_sha256,
        "source_sha256": sha256_file(Path(__file__)),
        "started_at": datetime.now(UTC).isoformat(),
        "resources": {},
    }
    try:
        capacity, binding = _capacity(protocol, protocol_lock_sha256)
        receipt["selection_capacity"] = binding.model_dump()
        _capture_resources(root, receipt["resources"])
        receipt["resource_summary"] = _validate_resources(
            root, receipt["resources"], capacity
        )
        recorded_at = datetime.now(UTC)
        receipt["recorded_at"] = recorded_at.isoformat()
        receipt["calendar_summary"] = _calendar_capacity(root, capacity, recorded_at)
        verify_validation_proofs()
        receipt["status"] = "passed"
    except BaseException as error:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(error).__name__}: {error}"
        receipt["recorded_at"] = datetime.now(UTC).isoformat()
        raise
    finally:
        write_immutable_json(receipt_path, receipt)
    return ArtifactBinding(
        relative_path=str(receipt_path.relative_to(root)),
        sha256=sha256_file(receipt_path),
    )


def validate_opening_capacity(protocol, binding, protocol_lock_sha256) -> datetime:
    """Validate the immutable historical measurement, never probe live resources."""
    root = resolve_scientific_paths(protocol).root
    path = _bound_file(root, binding)
    if path.parent != _directory(protocol, root).resolve():
        raise ValueError("opening capacity belongs to a different execution revision")
    receipt = json.loads(path.read_text())
    capacity, capacity_binding = _capacity(protocol, protocol_lock_sha256)
    if (
        receipt.get("schema_version") != 2
        or receipt.get("kind") != "v3_fresh_opening_capacity"
        or receipt.get("status") != "passed"
        or receipt.get("protocol_sha256") != protocol_digest(protocol)
        or receipt.get("protocol_lock_sha256") != protocol_lock_sha256
        or receipt.get("source_sha256") != sha256_file(Path(__file__))
        or receipt.get("selection_capacity") != capacity_binding.model_dump()
    ):
        raise ValueError("opening capacity receipt identity or passed status differs")
    recorded_at = datetime.fromisoformat(receipt["recorded_at"])
    started_at = datetime.fromisoformat(receipt["started_at"])
    measured_at = datetime.fromisoformat(receipt["resources"]["measured_at"])
    if (
        started_at.tzinfo is None
        or recorded_at.tzinfo is None
        or measured_at.tzinfo is None
        or not started_at <= measured_at <= recorded_at
    ):
        raise ValueError("opening capacity measurement chronology differs")
    if receipt["resource_summary"] != _validate_resources(
        root, receipt["resources"], capacity
    ) or receipt["calendar_summary"] != _calendar_capacity(root, capacity, recorded_at):
        raise ValueError("opening capacity recorded summary differs from evidence")
    return recorded_at
