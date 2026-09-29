"""Full auxiliary-cache repeatability and conservative Week 3 resource gates."""

from __future__ import annotations

import math
import re
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from pose_embed.artifacts import sidecar_path_for, validate_feature_artifact
from pose_embed.config import load_protocol
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.provenance import require_path_within, sha256_file, write_immutable_json

GIB = 1024**3
# Conservative reservation for all retained pre-head caches, nine heads and
# their clean/corrupted embeddings, validation checkpoints, logs and evidence.
REMAINING_ARTIFACT_BUDGET_BYTES = 100 * GIB


def extraction_forecast(
    runs: list[dict[str, Any]],
    *,
    full_sample_count: int,
    free_bytes: int,
    project_quota_free_bytes: int,
) -> dict[str, Any]:
    if len(runs) != 2:
        raise ValueError("repeatability requires exactly two extraction runs")
    if (
        type(full_sample_count) is not int
        or full_sample_count <= 0
        or type(free_bytes) is not int
        or free_bytes < 0
        or type(project_quota_free_bytes) is not int
        or project_quota_free_bytes < 0
    ):
        raise ValueError(
            "forecast requires a positive sample count and nonnegative "
            "filesystem and project-quota free bytes"
        )
    required = (
        "wall_time_seconds",
        "sample_count",
        "artifact_bytes",
        "peak_gpu_memory_bytes",
        "peak_host_memory_bytes",
    )
    for run in runs:
        if any(
            type(run.get(key)) not in {int, float}
            or not math.isfinite(run[key])
            or run[key] <= 0
            for key in required
        ):
            raise ValueError("GPU extraction telemetry is missing, nonfinite or zero")
        if any(type(run[key]) is not int for key in required[1:]):
            raise ValueError(
                "GPU extraction counts and byte measurements must be integers"
            )
        if run["sample_count"] > full_sample_count:
            raise ValueError(
                "extraction sample count exceeds the full source inventory"
            )
    seconds = (
        max(
            run["wall_time_seconds"] * full_sample_count / run["sample_count"]
            for run in runs
        )
        * 1.25
    )
    cache_bytes = math.ceil(
        max(
            run["artifact_bytes"] * full_sample_count / run["sample_count"]
            for run in runs
        )
        * 1.1
    )
    limits = {
        "full_extraction_seconds": 4 * 3600,
        "full_cache_bytes": 6 * GIB,
        "peak_gpu_memory_bytes": 16 * GIB,
        "peak_host_memory_bytes": 32 * GIB,
        "required_free_bytes": 2 * REMAINING_ARTIFACT_BUDGET_BYTES,
    }
    checks = {
        "runtime": seconds <= limits["full_extraction_seconds"],
        "cache_storage": cache_bytes <= limits["full_cache_bytes"],
        "gpu_memory": max(r["peak_gpu_memory_bytes"] for r in runs)
        <= limits["peak_gpu_memory_bytes"],
        "host_memory": max(r["peak_host_memory_bytes"] for r in runs)
        <= limits["peak_host_memory_bytes"],
        "remaining_storage": min(free_bytes, project_quota_free_bytes)
        >= limits["required_free_bytes"],
    }
    return {
        "full_sample_count": full_sample_count,
        "projected_seconds": seconds,
        "projected_cache_bytes": cache_bytes,
        "runtime_margin": 1.25,
        "storage_margin": 1.1,
        "remaining_artifact_budget_bytes": REMAINING_ARTIFACT_BUDGET_BYTES,
        "observed_free_bytes": free_bytes,
        "observed_filesystem_free_bytes": free_bytes,
        "observed_project_quota_free_bytes": project_quota_free_bytes,
        "effective_free_bytes": min(free_bytes, project_quota_free_bytes),
        "limits": limits,
        "checks": checks,
        "passed": all(checks.values()),
    }


def parse_project_quota(raw: str, artifact_root: Path) -> dict[str, Any]:
    """Select the SCC project-space row containing this artifact directory."""
    root = artifact_root.resolve()
    rows = []
    pattern = re.compile(r"^(/\S+)\s+(\d+(?:\.\d+)?)\s+\d+\s+(\d+(?:\.\d+)?)\s+\d+\s*$")
    for line in raw.splitlines():
        match = pattern.fullmatch(line.strip())
        if match is None:
            continue
        space = Path(match.group(1))
        if root.is_relative_to(space):
            rows.append((space, Decimal(match.group(2)), Decimal(match.group(3))))
    if not rows:
        raise ValueError("project quota report has no row for the artifact root")
    longest = max(len(space.parts) for space, _, _ in rows)
    matches = [row for row in rows if len(row[0].parts) == longest]
    if len(matches) != 1:
        raise ValueError("project quota report has ambiguous artifact-root rows")
    space, quota_gb, usage_gb = matches[0]
    if quota_gb <= 0 or usage_gb < 0:
        raise ValueError("project quota report has invalid capacity or usage")
    return {
        "project_space": str(space),
        "quota_gb": str(quota_gb),
        "usage_gb": str(usage_gb),
        "free_bytes": max(0, int((quota_gb - usage_gb) * 1_000_000_000)),
    }


def _run_evidence(
    sidecar: Any, path: Path
) -> tuple[dict[str, Any], datetime, datetime]:
    telemetry = sidecar.provenance.get("extraction")
    if (
        not isinstance(telemetry, dict)
        or type(telemetry.get("sample_count")) is not int
        or telemetry["sample_count"] != sidecar.shape[0]
        or type(telemetry.get("artifact_bytes")) is not int
        or telemetry["artifact_bytes"] != path.stat().st_size
    ):
        raise ValueError(
            "extraction telemetry differs from the verified cache count or bytes"
        )
    stages = telemetry.get("stage_seconds")
    required_stages = {
        "source_verification_load",
        "encoder_load_and_parity_validation",
        "preprocessing",
        "transfer",
        "encoder",
        "pooling",
        "serialization",
    }
    if (
        not isinstance(stages, dict)
        or not required_stages <= set(stages)
        or any(
            type(value) not in {int, float} or not math.isfinite(value) or value < 0
            for value in stages.values()
        )
        or type(telemetry.get("wall_time_seconds")) not in {int, float}
        or not math.isfinite(telemetry["wall_time_seconds"])
        or sum(stages.values()) > telemetry["wall_time_seconds"] + 1
    ):
        raise ValueError("extraction stage timing evidence is missing or inconsistent")
    try:
        start = datetime.fromisoformat(sidecar.provenance["started_at"])
        end = datetime.fromisoformat(sidecar.provenance["ended_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("extraction timestamps are missing or malformed") from exc
    if (
        start.tzinfo is None
        or end.tzinfo is None
        or not start < end <= datetime.now(UTC)
    ):
        raise ValueError(
            "extraction timestamps must be ordered, past, and timezone-aware"
        )
    elapsed = (end - start).total_seconds()
    # Provenance can finish before final cache verification. Wall time must
    # cover that recorded interval, with one second for clock granularity.
    if telemetry["wall_time_seconds"] + 1 < elapsed:
        raise ValueError("extraction wall time differs from the recorded run interval")
    return telemetry, start, end


def verify_repeatability(
    first_path: str | Path,
    second_path: str | Path,
    *,
    protocol_path: str | Path,
    manifest_path: str | Path,
    output_path: str | Path,
    project_quota_report: str | Path,
) -> dict[str, Any]:
    protocol = load_protocol(protocol_path)
    scientific = resolve_scientific_paths(protocol)
    if (
        scientific.test_opening_ledger.exists()
        or (scientific.root / "benchmark-v2/locks/test-opening.json").exists()
    ):
        raise ValueError("Week 3 verification requires the novel test to remain sealed")
    destination = require_path_within(
        output_path, scientific.root, label="repeatability evidence"
    )
    if destination.exists():
        raise ValueError("repeatability output already exists")
    paths = [Path(first_path).resolve(), Path(second_path).resolve()]
    if paths[0] == paths[1] or (
        paths[0].exists() and paths[1].exists() and paths[0].samefile(paths[1])
    ):
        raise ValueError("repeatability requires two distinct extraction outputs")
    sidecars = [
        validate_feature_artifact(path, protocol=protocol, manifest_path=manifest_path)
        for path in paths
    ]
    for sidecar in sidecars:
        if (
            sidecar.method != "frozen_encoder_cache"
            or sidecar.split != "final_train"
            or sidecar.role != "training"
            or sidecar.shape != (95001, 8704)
        ):
            raise ValueError(
                "repeatability requires both complete 95,001-row auxiliary caches"
            )
    first, second = sidecars
    for key in ("artifact_sha256", "sample_order_sha256", "manifest_sha256"):
        if getattr(first, key) != getattr(second, key):
            raise ValueError(f"repeat extraction mismatch: {key}")
    environments = [s.provenance.get("inference_environment") for s in sidecars]
    if (
        not isinstance(environments[0], dict)
        or environments[0] != environments[1]
        or environments[0].get("device_type") != "cuda"
        or any(
            not isinstance(environments[0].get(key), str)
            or not environments[0][key].strip()
            for key in ("cuda_device_uuid", "cuda_device_name", "hostname")
        )
    ):
        raise ValueError("repeat runs must use the same identified GPU and environment")
    processes = [s.provenance.get("process") for s in sidecars]
    if (
        any(
            not isinstance(p, dict)
            or not isinstance(p.get("job_id"), str)
            or not p["job_id"].isdecimal()
            or int(p["job_id"]) <= 0
            or type(p.get("pid")) is not int
            or p["pid"] <= 0
            for p in processes
        )
        or processes[0]["job_id"] != processes[1]["job_id"]
        or processes[0]["pid"] == processes[1]["pid"]
    ):
        raise ValueError(
            "repeat runs require fresh processes in the same scheduler job"
        )
    evidence = [
        _run_evidence(sidecar, path)
        for sidecar, path in zip(sidecars, paths, strict=True)
    ]
    if evidence[0][2] > evidence[1][1]:
        raise ValueError(
            "repeat extraction processes must run sequentially in recorded order"
        )
    quota_path = require_path_within(
        project_quota_report, scientific.root, label="project quota evidence"
    )
    observed_at = datetime.fromtimestamp(quota_path.stat().st_mtime, UTC)
    if observed_at < evidence[1][2] or observed_at > datetime.now(UTC):
        raise ValueError("project quota evidence must be captured after both runs")
    quota = parse_project_quota(quota_path.read_text(encoding="utf-8"), scientific.root)
    quota.update(
        evidence_path=str(quota_path),
        evidence_sha256=sha256_file(quota_path),
        observed_at=observed_at.isoformat(),
    )
    with (
        np.load(paths[0], allow_pickle=False) as left,
        np.load(paths[1], allow_pickle=False) as right,
    ):
        for key in ("features", "labels", "sample_ids"):
            if not np.array_equal(left[key], right[key]):
                raise ValueError(f"repeat extraction arrays differ: {key}")
    forecast = extraction_forecast(
        [item[0] for item in evidence],
        full_sample_count=protocol.dataset.expected_source_sample_count,
        free_bytes=shutil.disk_usage(scientific.root).free,
        project_quota_free_bytes=quota["free_bytes"],
    )
    report = {
        "schema_version": 1,
        "status": "passed" if forecast["passed"] else "failed",
        "protocol_sha256": protocol_digest(protocol),
        "identical_arrays": True,
        "identical_npz": True,
        "sample_order_sha256": first.sample_order_sha256,
        "inference_environment": environments[0],
        "processes": processes,
        "inputs": {
            str(path): sha256_file(path)
            for path in (
                *paths,
                *(sidecar_path_for(path) for path in paths),
                Path(manifest_path).resolve(),
            )
        },
        "forecast": forecast,
        "project_quota": quota,
    }
    write_immutable_json(destination, report)
    if not forecast["passed"]:
        raise ValueError(f"resource gate failed; evidence preserved at {destination}")
    return report
