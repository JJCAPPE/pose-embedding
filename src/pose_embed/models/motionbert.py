"""Verified, device-independent loading of the pinned MotionBERT encoder.

MotionBERT (Zhu et al., ICCV 2023) is imported from its pinned Apache-2.0
checkout. No encoder source or checkpoint is redistributed by this module.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import socket
import subprocess
import sys
import tomllib
from functools import partial
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn

from pose_embed.provenance import require_path_within, sha256_file

_REPOSITORY = Path(__file__).resolve().parents[3]
_UPSTREAM_MANIFEST = _REPOSITORY / "third_party" / "upstreams.toml"
_CHECKPOINT_MANIFEST = _REPOSITORY / "data/manifests/motionbert-checkpoint.v1.json"


def configure_deterministic_inference() -> None:
    """Require deterministic float32 kernels before the first CUDA operation."""
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") not in {None, ":4096:8"}:
        raise ValueError(
            "CUBLAS_WORKSPACE_CONFIG must be :4096:8 for the locked inference path"
        )
    if torch.cuda.is_initialized() and not os.environ.get("CUBLAS_WORKSPACE_CONFIG"):
        raise RuntimeError("configure deterministic inference before initializing CUDA")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")


def inference_environment(device: torch.device | str) -> dict[str, object]:
    """Record the runtime and device controls that bound repeatability evidence."""
    selected = torch.device(device)
    properties = (
        torch.cuda.get_device_properties(selected) if selected.type == "cuda" else None
    )
    uuid = getattr(properties, "uuid", None)
    return {
        "device_type": selected.type,
        "device_index": (
            selected.index
            if selected.index is not None
            else torch.cuda.current_device()
        )
        if selected.type == "cuda"
        else None,
        "hostname": socket.gethostname(),
        "cuda_device_name": properties.name if properties is not None else None,
        "cuda_device_uuid": str(uuid) if uuid is not None else None,
        "torch": str(torch.__version__),
        "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "numpy": str(np.__version__),
        "dtype": "float32",
        "batch_size": 32,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "deterministic_warn_only": (
            torch.is_deterministic_algorithms_warn_only_enabled()
        ),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
    }


def verify_motionbert_assets(data_root: Path) -> dict[str, object]:
    """Verify the checkout, license, architecture, and checkpoint without loading it."""
    with _UPSTREAM_MANIFEST.open("rb") as stream:
        document = tomllib.load(stream)
    entries = {entry["name"]: entry for entry in document.get("upstream", [])}
    upstream = entries.get("MotionBERT")
    if (
        upstream is None
        or upstream.get("reference_only")
        or upstream["license"] != "Apache-2.0"
    ):
        raise ValueError("MotionBERT is not an approved inference upstream")
    root = (_REPOSITORY / document["cache_directory"] / "MotionBERT").resolve()
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if commit.returncode or commit.stdout.strip() != upstream["commit"]:
        raise ValueError("the pinned MotionBERT checkout is missing or changed")
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--short", "--untracked-files=no"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if status.returncode or status.stdout.strip():
        raise ValueError("the pinned MotionBERT checkout has tracked changes")
    for filename in upstream["license_files"]:
        if not (root / filename).is_file():
            raise ValueError(f"MotionBERT license file is missing: {filename}")
    with _CHECKPOINT_MANIFEST.open(encoding="utf-8") as stream:
        checkpoint_manifest = json.load(stream)
    checkpoint = require_path_within(
        data_root / checkpoint_manifest["filename"],
        data_root,
        label="MotionBERT checkpoint",
    )
    if not checkpoint.is_file():
        raise ValueError("the verified MotionBERT checkpoint is missing")
    if checkpoint.stat().st_size != checkpoint_manifest["bytes"]:
        raise ValueError("MotionBERT checkpoint byte size differs from its manifest")
    if sha256_file(checkpoint) != checkpoint_manifest["sha256"]:
        raise ValueError("MotionBERT checkpoint SHA-256 differs from its manifest")
    config = root / "configs/pretrain/MB_pretrain.yaml"
    config_match = re.search(
        r"sha256:\s*([0-9a-f]{64})", checkpoint_manifest["architecture_config_id"]
    )
    if config_match is None or sha256_file(config) != config_match.group(1):
        raise ValueError("MotionBERT architecture config differs from its manifest")
    implementation = root / "lib/model/DSTformer.py"
    tracked = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "lib",
            "configs/pretrain/MB_pretrain.yaml",
            "LICENSE",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    file_hashes = {
        name: sha256_file(root / name)
        for name in sorted(tracked.stdout.decode("utf-8").split("\0"))
        if name
    }
    upstream_sha256 = hashlib.sha256(
        json.dumps(file_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "upstream_root": str(root),
        "upstream_commit": upstream["commit"],
        "upstream_sha256": upstream_sha256,
        "license_sha256": sha256_file(root / "LICENSE"),
        "implementation_path": str(implementation),
        "implementation_sha256": sha256_file(implementation),
        "config_path": str(config),
        "config_sha256": sha256_file(config),
        "checkpoint_path": str(checkpoint),
        "checkpoint_bytes": checkpoint.stat().st_size,
        "checkpoint_sha256": checkpoint_manifest["sha256"],
    }


def _encoder_class(upstream_root: Path) -> type[nn.Module]:
    sys.path.insert(0, str(upstream_root))
    try:
        from lib.model.DSTformer import DSTformer
    finally:
        sys.path.remove(str(upstream_root))
    if (
        Path(inspect.getfile(DSTformer)).resolve()
        != upstream_root / "lib/model/DSTformer.py"
    ):
        raise ValueError("MotionBERT imported from outside the pinned checkout")
    return DSTformer


def load_frozen_encoder(
    data_root: Path, device: torch.device | str = "cpu"
) -> tuple[nn.Module, dict[str, object]]:
    """Strictly load the authorized checkpoint; keep every parameter frozen."""
    metadata = verify_motionbert_assets(data_root)
    with Path(str(metadata["config_path"])).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    encoder_class = _encoder_class(Path(str(metadata["upstream_root"])))
    encoder = encoder_class(
        dim_in=3,
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
    checkpoint = torch.load(
        str(metadata["checkpoint_path"]), map_location="cpu", weights_only=True
    )
    state = checkpoint.get("model_pos") if isinstance(checkpoint, dict) else None
    if not isinstance(state, dict):
        raise ValueError("MotionBERT checkpoint has no model_pos state dictionary")
    normalized: dict[str, torch.Tensor] = {}
    for key, value in state.items():
        if not isinstance(key, str) or not isinstance(value, torch.Tensor):
            raise ValueError(
                "MotionBERT state dictionary entries must be named tensors"
            )
        normalized_key = key.removeprefix("module.")
        if normalized_key in normalized:
            raise ValueError("MotionBERT checkpoint has duplicate normalized keys")
        if not bool(torch.isfinite(value).all()):
            raise ValueError("MotionBERT checkpoint contains non-finite parameters")
        normalized[normalized_key] = value
    encoder.load_state_dict(normalized, strict=True)
    encoder.to(device=device, dtype=torch.float32).requires_grad_(False).eval()
    if encoder.training or any(
        parameter.requires_grad for parameter in encoder.parameters()
    ):
        raise RuntimeError(
            "MotionBERT encoder did not remain frozen in evaluation mode"
        )
    return encoder, {
        **metadata,
        "state_dict_entries": len(normalized),
        "parameter_count": sum(parameter.numel() for parameter in encoder.parameters()),
        "trainable_parameter_count": 0,
    }
