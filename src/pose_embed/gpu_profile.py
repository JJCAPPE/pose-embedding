"""CUDA profiling for the pinned frozen MotionBERT encoder."""

from __future__ import annotations

import gc
import inspect
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

from pose_embed.protocol import verify_protocol
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
_PROTOCOL_CONFIG = _REPOSITORY / "configs" / "protocol.v1.yaml"
_BATCH_SIZES = (32, 64)
_PEOPLE = 2
_FRAMES = 100
_JOINTS = 17
_CHANNELS = 3
_REPRESENTATION_DIMENSION = 512
_PROFILE_SEED = 20260912
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


def _profile_contract() -> dict[str, object]:
    protocol, digest = verify_protocol(_PROTOCOL_CONFIG)
    declared = {
        "batch_sizes": (
            protocol.batch.physical_batch_size,
            protocol.batch.profile_batch_size,
        ),
        "people": protocol.encoder.people,
        "frames": protocol.dataset.frames,
        "joints": protocol.dataset.joints,
        "channels": len(protocol.input_pipeline.channels),
        "dtype": protocol.input_pipeline.dtype,
        "tensor_layout": protocol.input_pipeline.tensor_layout,
        "representation_dimension": protocol.encoder.representation_dimension,
    }
    expected = {
        "batch_sizes": _BATCH_SIZES,
        "people": _PEOPLE,
        "frames": _FRAMES,
        "joints": _JOINTS,
        "channels": _CHANNELS,
        "dtype": "float32",
        "tensor_layout": "people_frames_joints_channels",
        "representation_dimension": _REPRESENTATION_DIMENSION,
    }
    if declared != expected:
        raise ValueError("GPU profile constants differ from protocol v1")
    return {
        "protocol_id": protocol.protocol_id,
        "protocol_sha256": digest,
        **declared,
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
    status_result = _command(
        "git",
        "-C",
        str(upstream_root),
        "status",
        "--short",
        "--untracked-files=no",
    )
    if status_result.get("returncode") != 0 or status_result.get("stdout"):
        raise ValueError("the pinned MotionBERT checkout has tracked changes")
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
    implementation_path = Path(inspect.getfile(DSTformer)).resolve()
    expected_implementation_path = upstream_root / "lib" / "model" / "DSTformer.py"
    if implementation_path != expected_implementation_path:
        raise ValueError("MotionBERT imported from outside the pinned checkout")

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
        "implementation_path": str(implementation_path),
        "implementation_sha256": sha256_file(implementation_path),
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
    stage = "input_allocation"
    try:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)
        generator = torch.Generator(device=device).manual_seed(_PROFILE_SEED)
        poses = torch.rand(
            (batch_size, _PEOPLE, _FRAMES, _JOINTS, _CHANNELS),
            dtype=torch.float32,
            device=device,
            generator=generator,
        )
        flattened = poses.reshape(batch_size * _PEOPLE, _FRAMES, _JOINTS, _CHANNELS)
        stage = "warmup"
        with torch.inference_mode():
            for _ in range(_WARMUPS):
                represented = encoder.get_representation(flattened)  # type: ignore[attr-defined]
            torch.cuda.synchronize(device)
            represented = None
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)

            elapsed_ms: list[float] = []
            stage = "timed_forward"
            for _ in range(_REPEATS):
                start = torch.cuda.Event(enable_timing=True)
                end = torch.cuda.Event(enable_timing=True)
                start.record()
                represented = encoder.get_representation(flattened)  # type: ignore[attr-defined]
                end.record()
                end.synchronize()
                elapsed_ms.append(float(start.elapsed_time(end)))

        expected_shape = [
            batch_size * _PEOPLE,
            _FRAMES,
            _JOINTS,
            _REPRESENTATION_DIMENSION,
        ]
        if list(represented.shape) != expected_shape:
            raise RuntimeError(
                f"MotionBERT output shape differs from the protocol: "
                f"{list(represented.shape)}"
            )
        if represented.dtype != torch.float32:
            raise RuntimeError(
                "MotionBERT output dtype differs from the protocol: "
                f"{represented.dtype}"
            )
        if not bool(torch.isfinite(represented).all().item()):
            raise RuntimeError("MotionBERT output contains a non-finite value")

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
            "timing_source": "torch_cuda_event_device_time",
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
            "failure_stage": stage,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
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
            "PROJECT",
            "SGE_CELL",
            "SGE_ROOT",
        )
        if name in os.environ
    }
    job_id = scheduler_environment.get("JOB_ID")
    queue = scheduler_environment.get("QUEUE")
    project = scheduler_environment.get("PROJECT")
    return {
        "kind": "Grid Engine",
        "environment": scheduler_environment,
        "version": _command("qstat", "-help"),
        "job": _command("qstat", "-j", str(job_id)),
        "global_limits": _command("qconf", "-sconf"),
        "scheduler_limits": _command("qconf", "-ssconf"),
        "assigned_queue": _command("qconf", "-sq", str(queue)),
        "shared_gpu_limits": _command("qconf", "-srqs", "shared_gpu_queue_limits"),
        "shared_gpu_slot_limits": _command(
            "qconf", "-srqs", "shared_gpu_queue_limits_2"
        ),
        "project": _command("qconf", "-sprj", str(project)),
    }


def _command_succeeded(record: object) -> bool:
    if not isinstance(record, dict) or record.get("returncode") != 0:
        return False
    return bool(record.get("stdout") or record.get("stderr"))


def _profile_decision(
    batches: list[dict[str, object]], *, evidence_complete: bool
) -> dict[str, object]:
    batch_32_ok = batches[0]["status"] == "success"
    batch_64_ok = batches[1]["status"] == "success"
    if not batch_32_ok:
        status = "no_feasible_protocol_batch"
        justification = "Physical batch 32 did not complete on the assigned GPU."
    elif not evidence_complete:
        status = "profile_evidence_incomplete"
        justification = (
            "Physical batch 32 completed, but required device, scheduler, or quota "
            "evidence could not be captured."
        )
    elif not batch_64_ok:
        status = "retain_physical_batch_32"
        justification = "Batch 32 completed and batch 64 exhausted CUDA memory."
    else:
        status = "retain_physical_batch_32_pending_core_method_profile"
        justification = (
            "Both encoder forwards completed, but protocol v1 permits batch 64 only "
            "after every core objective fits during the Week 4 method-level profile."
        )
    return {
        "physical_batch_size": 32 if batch_32_ok else None,
        "status": status,
        "justification": justification,
        "week_1_gate_supported": batch_32_ok and evidence_complete,
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
    contract = _profile_contract()
    encoder, model_profile = _load_frozen_encoder(data_root)
    device_index = torch.cuda.current_device()
    device = torch.device("cuda", device_index)
    encoder.to(device)
    properties = torch.cuda.get_device_properties(device)
    batches = [_profile_batch(encoder, size) for size in _BATCH_SIZES]
    driver_profile = _command(
        "nvidia-smi",
        "--query-gpu=driver_version",
        "--format=csv,noheader",
    )
    scheduler_profile = _scheduler_profile()
    scheduler_environment = scheduler_profile["environment"]
    if not isinstance(scheduler_environment, dict):
        raise RuntimeError("scheduler environment evidence is malformed")
    project = scheduler_environment.get("PROJECT")
    storage_profile = {
        "data_root": _disk_usage(data_root),
        "artifact_root": _disk_usage(artifact_root),
        "home_quota": _command("quota", "-s"),
        "project_quota": _command("pquota", "-u", str(project)),
    }
    evidence_commands = {
        "device_driver": driver_profile,
        "scheduler_version": scheduler_profile["version"],
        "scheduler_job": scheduler_profile["job"],
        "scheduler_global_limits": scheduler_profile["global_limits"],
        "scheduler_limits": scheduler_profile["scheduler_limits"],
        "assigned_queue": scheduler_profile["assigned_queue"],
        "shared_gpu_limits": scheduler_profile["shared_gpu_limits"],
        "shared_gpu_slot_limits": scheduler_profile["shared_gpu_slot_limits"],
        "scheduler_project": scheduler_profile["project"],
        "home_quota": storage_profile["home_quota"],
        "project_quota": storage_profile["project_quota"],
    }
    failed_evidence = [
        name
        for name, record in evidence_commands.items()
        if not _command_succeeded(record)
    ]
    evidence_complete = not failed_evidence
    decision = _profile_decision(batches, evidence_complete=evidence_complete)

    ended_at = datetime.now(UTC)
    profile: dict[str, Any] = {
        "schema_version": 1,
        "profile_scope": (
            "dense synthetic-input compute and memory profile only; not "
            "preprocessing or encoder-parity evidence"
        ),
        "protocol": contract,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "host": socket.gethostname(),
        "device": {
            "index": device_index,
            "name": properties.name,
            "total_memory_bytes": properties.total_memory,
            "compute_capability": list(torch.cuda.get_device_capability(device)),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "driver": driver_profile,
        },
        "software": {
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
        },
        "model": model_profile,
        "scheduler": scheduler_profile,
        "storage": storage_profile,
        "evidence": {
            "complete": evidence_complete,
            "failed_commands": failed_evidence,
        },
        "batches": batches,
        "decision": decision,
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
            "profile_seed": _PROFILE_SEED,
            "protocol_sha256": contract["protocol_sha256"],
        },
        inputs=(
            Path(__file__),
            _JOB_SCRIPT,
            _UPSTREAM_MANIFEST,
            _CHECKPOINT_MANIFEST,
            _PROTOCOL_CONFIG,
            Path(str(model_profile["implementation_path"])),
            Path(str(model_profile["config_path"])),
            Path(str(model_profile["checkpoint_path"])),
        ),
        repository=_REPOSITORY,
        started_at=started_at,
        ended_at=ended_at,
    )
    write_immutable_json(destination, profile)
    return profile
