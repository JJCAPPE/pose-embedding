"""CUDA profiling for the pinned frozen MotionBERT encoder."""

from __future__ import annotations

import gc
import json
import os
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import torch
import yaml
from torch import nn

from pose_embed.provenance import (
    capture_provenance,
    require_path_within,
    sha256_file,
    write_immutable_json,
)

_REPOSITORY = Path(__file__).resolve().parents[2]
_UPSTREAM_MANIFEST = _REPOSITORY / "third_party" / "upstreams.toml"
_CHECKPOINT_MANIFEST = (
    _REPOSITORY / "data" / "manifests" / "motionbert-checkpoint.v1.json"
)
_JOB_SCRIPT = _REPOSITORY / "scripts" / "profile_motionbert_gpu.qsub"
_BATCH_SIZES = (32, 64)
_PEOPLE = 2
_FRAMES = 100
_JOINTS = 17
_CHANNELS = 3
_WARMUPS = 3
_REPEATS = 10


def _required_root(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} must be set")
    return Path(value).resolve()


def _command(*arguments: str) -> dict[str, object]:
    try:
        result = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": list(arguments), "error": type(exc).__name__}
    return {
        "command": list(arguments),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _disk_usage(path: Path) -> dict[str, int | str]:
    usage = shutil.disk_usage(path)
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


def _load_frozen_encoder(data_root: Path) -> tuple[nn.Module, dict[str, object]]:
    with _UPSTREAM_MANIFEST.open("rb") as stream:
        upstream_document = tomllib.load(stream)
    entries = {entry["name"]: entry for entry in upstream_document.get("upstream", [])}
    motionbert = entries.get("MotionBERT")
    if motionbert is None or motionbert.get("reference_only"):
        raise ValueError("MotionBERT is not an approved inference upstream")

    upstream_root = (
        _REPOSITORY / upstream_document["cache_directory"] / "MotionBERT"
    ).resolve()
    commit_result = _command("git", "-C", str(upstream_root), "rev-parse", "HEAD")
    if (
        commit_result.get("returncode") != 0
        or commit_result.get("stdout") != motionbert["commit"]
    ):
        raise ValueError("the pinned MotionBERT checkout is missing or changed")
    for license_file in motionbert["license_files"]:
        if not (upstream_root / license_file).is_file():
            raise ValueError(f"MotionBERT license file is missing: {license_file}")

    with _CHECKPOINT_MANIFEST.open(encoding="utf-8") as stream:
        checkpoint_manifest = json.load(stream)
    checkpoint_path = (data_root / checkpoint_manifest["filename"]).resolve()
    if not checkpoint_path.is_file():
        raise ValueError("the verified MotionBERT checkpoint is missing")
    if checkpoint_path.stat().st_size != checkpoint_manifest["bytes"]:
        raise ValueError("MotionBERT checkpoint byte size differs from its manifest")
    if sha256_file(checkpoint_path) != checkpoint_manifest["sha256"]:
        raise ValueError("MotionBERT checkpoint SHA-256 differs from its manifest")

    config_path = upstream_root / "configs" / "pretrain" / "MB_pretrain.yaml"
    config_match = re.search(
        r"sha256:\s*([0-9a-f]{64})",
        checkpoint_manifest["architecture_config_id"],
    )
    if config_match is None or sha256_file(config_path) != config_match.group(1):
        raise ValueError("MotionBERT architecture config differs from its manifest")
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    sys.path.insert(0, str(upstream_root))
    try:
        from lib.model.DSTformer import DSTformer
    finally:
        sys.path.remove(str(upstream_root))

    encoder = DSTformer(
        dim_in=_CHANNELS,
        dim_out=3,
        dim_feat=config["dim_feat"],
        dim_rep=config["dim_rep"],
        depth=config["depth"],
        num_heads=config["num_heads"],
        mlp_ratio=config["mlp_ratio"],
        num_joints=config["num_joints"],
        maxlen=config["maxlen"],
        norm_layer=partial(nn.LayerNorm, eps=1e-6),
        att_fuse=config["att_fuse"],
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    state_dict = checkpoint.get("model_pos")
    if not isinstance(state_dict, dict):
        raise ValueError("MotionBERT checkpoint has no model_pos state dictionary")
    normalized: dict[str, torch.Tensor] = {}
    for key, value in state_dict.items():
        normalized_key = key.removeprefix("module.")
        if normalized_key in normalized:
            raise ValueError("MotionBERT checkpoint has duplicate normalized keys")
        normalized[normalized_key] = value
    encoder.load_state_dict(normalized, strict=True)
    encoder.requires_grad_(False).eval()
    if encoder.training or any(
        parameter.requires_grad for parameter in encoder.parameters()
    ):
        raise RuntimeError(
            "MotionBERT encoder did not remain frozen in evaluation mode"
        )
    return encoder, {
        "upstream_root": str(upstream_root),
        "upstream_commit": motionbert["commit"],
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": checkpoint_manifest["sha256"],
        "state_dict_entries": len(normalized),
        "parameter_count": sum(parameter.numel() for parameter in encoder.parameters()),
        "trainable_parameter_count": 0,
    }


def _profile_batch(encoder: nn.Module, batch_size: int) -> dict[str, object]:
    device = torch.device("cuda", torch.cuda.current_device())
    poses: torch.Tensor | None = None
    represented: torch.Tensor | None = None
    try:
        generator = torch.Generator(device=device).manual_seed(20260912)
        poses = torch.rand(
            (batch_size, _PEOPLE, _FRAMES, _JOINTS, _CHANNELS),
            dtype=torch.float32,
            device=device,
            generator=generator,
        )
        flattened = poses.reshape(batch_size * _PEOPLE, _FRAMES, _JOINTS, _CHANNELS)
        with torch.inference_mode():
            for _ in range(_WARMUPS):
                represented = encoder.get_representation(flattened)  # type: ignore[attr-defined]
            torch.cuda.synchronize(device)
            represented = None
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)

            elapsed_ms: list[float] = []
            for _ in range(_REPEATS):
                start = torch.cuda.Event(enable_timing=True)
                end = torch.cuda.Event(enable_timing=True)
                start.record()
                represented = encoder.get_representation(flattened)  # type: ignore[attr-defined]
                end.record()
                end.synchronize()
                elapsed_ms.append(float(start.elapsed_time(end)))

        median_ms = statistics.median(elapsed_ms)
        return {
            "status": "success",
            "physical_batch_size": batch_size,
            "encoder_batch_size": batch_size * _PEOPLE,
            "input_shape": list(poses.shape),
            "input_dtype": str(poses.dtype),
            "output_shape": list(represented.shape),
            "warmups": _WARMUPS,
            "repeats": _REPEATS,
            "forward_times_ms": elapsed_ms,
            "median_forward_ms": median_ms,
            "samples_per_second_at_median": batch_size / (median_ms / 1000),
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        }
    except torch.OutOfMemoryError:
        return {
            "status": "cuda_out_of_memory",
            "physical_batch_size": batch_size,
            "encoder_batch_size": batch_size * _PEOPLE,
            "input_shape": [batch_size, _PEOPLE, _FRAMES, _JOINTS, _CHANNELS],
            "input_dtype": "torch.float32",
        }
    finally:
        del represented, poses
        gc.collect()
        torch.cuda.empty_cache()


def _scheduler_profile() -> dict[str, object]:
    scheduler_environment = {
        name: os.environ[name]
        for name in (
            "JOB_ID",
            "JOB_NAME",
            "QUEUE",
            "NSLOTS",
            "PE",
            "SGE_CELL",
            "SGE_ROOT",
        )
        if name in os.environ
    }
    job_id = scheduler_environment.get("JOB_ID")
    return {
        "kind": "Grid Engine",
        "environment": scheduler_environment,
        "version": _command("qstat", "-help"),
        "job": _command("qstat", "-j", str(job_id)),
        "global_limits": _command("qconf", "-sconf"),
        "resource_quota_sets": _command("qconf", "-srqs"),
    }


def profile_motionbert_gpu(output_path: str | Path) -> dict[str, object]:
    """Profile the protocol-defined MotionBERT batches on one CUDA device."""
    if not torch.cuda.is_available():
        raise RuntimeError("a CUDA GPU is required for the MotionBERT profile")
    if not os.environ.get("JOB_ID") or not os.environ.get("QUEUE"):
        raise RuntimeError("the GPU profile must run inside a Grid Engine job")

    data_root = _required_root("POSE_EMBED_DATA_ROOT")
    artifact_root = _required_root("POSE_EMBED_ARTIFACT_ROOT")
    if not data_root.is_dir() or not artifact_root.is_dir():
        raise ValueError("configured data and artifact roots must already exist")
    destination = require_path_within(
        output_path,
        artifact_root,
        label="GPU profile output",
    )
    if destination.exists():
        raise ValueError(f"refusing to overwrite immutable artifact: {destination}")

    started_at = datetime.now(UTC)
    encoder, model_profile = _load_frozen_encoder(data_root)
    device_index = torch.cuda.current_device()
    device = torch.device("cuda", device_index)
    encoder.to(device)
    properties = torch.cuda.get_device_properties(device)
    batches = [_profile_batch(encoder, size) for size in _BATCH_SIZES]
    batch_32_ok = batches[0]["status"] == "success"
    batch_64_ok = batches[1]["status"] == "success"
    if not batch_32_ok:
        decision = "no_feasible_protocol_batch"
        justification = "Physical batch 32 did not complete on the assigned GPU."
    elif not batch_64_ok:
        decision = "retain_physical_batch_32"
        justification = "Batch 32 completed and batch 64 exhausted CUDA memory."
    else:
        decision = "retain_physical_batch_32_pending_core_method_profile"
        justification = (
            "Both encoder forwards completed, but protocol v1 permits batch 64 only "
            "after every core objective fits during the Week 4 method-level profile."
        )

    ended_at = datetime.now(UTC)
    profile: dict[str, Any] = {
        "schema_version": 1,
        "profile_scope": "synthetic-input compute profile; not encoder parity evidence",
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "host": socket.gethostname(),
        "device": {
            "index": device_index,
            "name": properties.name,
            "total_memory_bytes": properties.total_memory,
            "compute_capability": list(torch.cuda.get_device_capability(device)),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "driver": _command(
                "nvidia-smi",
                "--query-gpu=driver_version",
                "--format=csv,noheader",
            ),
        },
        "software": {
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
        },
        "model": model_profile,
        "scheduler": _scheduler_profile(),
        "storage": {
            "data_root": _disk_usage(data_root),
            "artifact_root": _disk_usage(artifact_root),
            "account_quota": _command("quota", "-s"),
        },
        "batches": batches,
        "decision": {
            "physical_batch_size": 32 if batch_32_ok else None,
            "status": decision,
            "justification": justification,
            "week_1_gate_supported": batch_32_ok,
        },
    }
    profile["provenance"] = capture_provenance(
        command=f"pose-embed profile gpu --output {destination}",
        configuration={
            "batch_sizes": list(_BATCH_SIZES),
            "people": _PEOPLE,
            "frames": _FRAMES,
            "joints": _JOINTS,
            "channels": _CHANNELS,
            "warmups": _WARMUPS,
            "repeats": _REPEATS,
        },
        inputs=(
            Path(__file__),
            _JOB_SCRIPT,
            _UPSTREAM_MANIFEST,
            _CHECKPOINT_MANIFEST,
            model_profile["config_path"],
            model_profile["checkpoint_path"],
        ),
        repository=_REPOSITORY,
        started_at=started_at,
        ended_at=ended_at,
    )
    write_immutable_json(destination, profile)
    return profile
