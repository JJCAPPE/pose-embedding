"""Hashing and immutable run-manifest utilities."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import torch
from pydantic import BaseModel, ConfigDict, Field


class RuntimeTelemetry(BaseModel):
    """Strict wall-time and peak-memory evidence for an expensive operation."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    wall_time_seconds: float = Field(ge=0)
    peak_memory_bytes: int = Field(ge=0)
    peak_memory_source: Literal[
        "torch_cuda_max_memory_allocated", "process_max_rss", "not_available"
    ]


def reset_peak_memory(device: str | torch.device | None = None) -> None:
    """Reset operation-scoped CUDA peak accounting when CUDA is in use."""
    if device is None:
        return
    resolved = torch.device(device)
    if resolved.type == "cuda":
        torch.cuda.synchronize(resolved)
        torch.cuda.reset_peak_memory_stats(resolved)


def capture_runtime_telemetry(
    *,
    started_at: datetime,
    ended_at: datetime,
    device: str | torch.device | None = None,
) -> RuntimeTelemetry:
    """Capture deterministic duration and the best available peak-memory counter."""
    if started_at.tzinfo is None or ended_at.tzinfo is None or ended_at < started_at:
        raise ValueError("telemetry timestamps must be ordered and timezone-aware")
    peak_memory_bytes = 0
    peak_memory_source: Literal[
        "torch_cuda_max_memory_allocated", "process_max_rss", "not_available"
    ] = "not_available"
    resolved = torch.device(device) if device is not None else None
    if resolved is not None and resolved.type == "cuda":
        torch.cuda.synchronize(resolved)
        peak_memory_bytes = int(torch.cuda.max_memory_allocated(resolved))
        peak_memory_source = "torch_cuda_max_memory_allocated"
    else:
        try:
            import resource

            peak_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        except (ImportError, OSError, ValueError):
            pass
        else:
            peak_memory_bytes = (
                peak_rss if sys.platform == "darwin" else peak_rss * 1024
            )
            peak_memory_source = "process_max_rss"
    return RuntimeTelemetry(
        wall_time_seconds=(ended_at - started_at).total_seconds(),
        peak_memory_bytes=peak_memory_bytes,
        peak_memory_source=peak_memory_source,
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_path_within(
    path: str | Path,
    root: str | Path,
    *,
    label: str,
) -> Path:
    """Resolve an output path and reject writes outside its authorized root."""
    destination = Path(path).resolve()
    try:
        destination.relative_to(Path(root).resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must be inside POSE_EMBED_ARTIFACT_ROOT") from exc
    return destination


def _git_sha(repository: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _git_dirty(repository: Path) -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def capture_provenance(
    *,
    command: str,
    configuration: dict[str, Any],
    inputs: Iterable[str | Path] = (),
    repository: str | Path | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> dict[str, Any]:
    """Capture the minimum provenance needed to audit a run."""
    root = Path(repository or Path.cwd())
    input_hashes = {
        str(Path(path)): sha256_file(path)
        for path in sorted((Path(item) for item in inputs), key=str)
    }
    dependencies: dict[str, str] = {}
    for package in (
        "numpy",
        "pydantic",
        "pytorch-metric-learning",
        "PyYAML",
        "torch",
    ):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = "not-installed"
    finished_at = ended_at or datetime.now(UTC)
    effective_start = started_at or finished_at
    if (
        effective_start.tzinfo is None
        or finished_at.tzinfo is None
        or finished_at < effective_start
    ):
        raise ValueError("provenance timestamps must be ordered and timezone-aware")
    lock_path = root / "uv.lock"
    return {
        "schema_version": 1,
        "started_at": effective_start.astimezone(UTC).isoformat(),
        "ended_at": finished_at.astimezone(UTC).isoformat(),
        "command": command,
        "git_sha": _git_sha(root),
        "git_dirty": _git_dirty(root),
        "dependency_lock_sha256": sha256_file(lock_path)
        if lock_path.is_file()
        else None,
        "configuration": configuration,
        "inputs": input_hashes,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "devices": [
                torch.cuda.get_device_name(index)
                for index in range(torch.cuda.device_count())
            ],
            "dependencies": dependencies,
        },
    }


def write_immutable_json(path: str | Path, payload: object) -> None:
    """Create a JSON artifact and refuse to overwrite prior evidence."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise ValueError(
            f"refusing to overwrite immutable artifact: {destination}"
        ) from exc
