"""Command-local success markers for two deterministic numerical checks.

This is not an authorization or hash cache. Every use rereads every explicitly
bound file; all callers keep their metadata, source and live authority checks.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import threading
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch

from pose_embed.provenance import require_path_within, sha256_file

_REPOSITORY = Path(__file__).resolve().parents[2]


def _owner() -> tuple[int, int, int | None]:
    try:
        task = asyncio.current_task()
    except RuntimeError:
        task = None
    return os.getpid(), threading.get_ident(), id(task) if task else None


@dataclass
class _Session:
    owner: tuple[int, int, int | None] = field(default_factory=_owner)
    proofs: set[str] = field(default_factory=set)
    running: set[str] = field(default_factory=set)
    files: dict[str, tuple[str, str]] = field(default_factory=dict)
    invalid: bool = False
    hits: int = 0
    checks: int = 0
    rehash_seconds: float = 0.0
    numerical_seconds: float = 0.0

    def statistics(self) -> dict[str, int | float]:
        return {
            key: getattr(self, key)
            for key in ("hits", "checks", "rehash_seconds", "numerical_seconds")
        }


_SESSION: ContextVar[_Session | None] = ContextVar("numerical_proofs", default=None)


def _session() -> _Session | None:
    current = _SESSION.get()
    # A copied context, fork, or a new thread must not inherit numerical trust.
    return current if current is not None and current.owner == _owner() else None


def _rehash(session: _Session, files: Mapping[str, tuple[str, str]]) -> None:
    started = perf_counter()
    try:
        if session.invalid:
            raise ValueError("numerical proof session was invalidated")
        for raw, (resolved, digest) in files.items():
            if (
                str(Path(raw).resolve(strict=True)) != resolved
                or sha256_file(raw) != digest
            ):
                raise ValueError(f"numerical proof dependency changed: {raw}")
    except (OSError, ValueError) as exc:
        session.invalid = True
        raise ValueError(
            f"numerical proof dependency verification failed: {exc}"
        ) from exc
    finally:
        session.rehash_seconds += perf_counter() - started


def verify_validation_proofs() -> None:
    """Recheck committed inputs immediately before a caller publishes outputs."""
    current = _session()
    if current is not None:
        _rehash(current, current.files)


def validation_statistics() -> dict[str, int | float]:
    current = _session()
    return current.statistics() if current is not None else _Session().statistics()


@contextmanager
def validation_session(*, fresh: bool = False):
    """Nested APIs share a scope; independent recertification requests a fresh one."""
    current = _session()
    if current is not None and not fresh:
        yield current
        return
    current = _Session()
    token = _SESSION.set(current)
    try:
        yield current
        verify_validation_proofs()
    finally:
        # Clear even when an exception occurs or a copied context retains the object.
        current.proofs.clear()
        current.running.clear()
        current.files.clear()
        current.invalid = True
        _SESSION.reset(token)


def validation_command(*, fresh: bool = False):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with validation_session(fresh=fresh):
                return function(*args, **kwargs)

        return wrapped

    return decorate


def proof_reuse_allowed(protocol, *, scientific_use_allowed: bool) -> bool:
    """Historical scientific releases never acquire successor reuse semantics."""
    return protocol.schema_version == 3 and (
        not scientific_use_allowed
        or protocol.test_access.resolved_protocol_relative_path
        == "study-v3/revisions/execution-r2/locks/protocol.v3.json"
    )


def proof_source_bindings(protocol, *, scientific_use_allowed: bool) -> dict[str, str]:
    """Commit the already-validated design/source bytes through publication.

    This does not authorize anything; callers still run require_v3_design and all
    live guards. Fixtures bind the dependency lock without inventing a design.
    """
    files = {str(_REPOSITORY / "uv.lock"): sha256_file(_REPOSITORY / "uv.lock")}
    if not scientific_use_allowed or not proof_reuse_allowed(
        protocol, scientific_use_allowed=True
    ):
        return files
    from pose_embed.config import load_protocol
    from pose_embed.protocol import protocol_digest, resolve_scientific_paths
    from pose_embed.protocol_v3 import V3DesignLock

    root = resolve_scientific_paths(protocol).root
    path = require_path_within(
        root / protocol.test_access.design_lock_relative_path,
        root,
        label="proof design",
    )
    content = path.read_bytes()
    design = V3DesignLock.model_validate_json(content)
    resolved = require_path_within(
        root / design.protocol_relative_path, root, label="proof protocol"
    )
    if (
        design.protocol_sha256 != protocol_digest(protocol)
        or design.protocol_relative_path
        != protocol.test_access.resolved_protocol_relative_path
        or load_protocol(resolved) != protocol
    ):
        raise ValueError("numerical proof source bindings differ from active design")
    files.update(
        {
            str(path): hashlib.sha256(content).hexdigest(),
            str(resolved): sha256_file(resolved),
        }
    )
    files.update(
        {
            str(
                require_path_within(
                    _REPOSITORY / name, _REPOSITORY, label="proof source"
                )
            ): digest
            for name, digest in design.code_sha256.items()
        }
    )
    return files


def numerical_runtime() -> dict[str, Any]:
    """Read current CPU/BLAS settings without setting flags or initializing CUDA."""
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": str(torch.__version__),
        "numpy": np.__version__,
        "numpy_build": np.__config__.show(mode="dicts"),
        "torch_build": torch.__config__.show(),
        "cpu_capability": torch.backends.cpu.get_cpu_capability(),
        "threads": torch.get_num_threads(),
        "interop_threads": torch.get_num_interop_threads(),
        "dtype": str(torch.get_default_dtype()),
        "device": str(torch.get_default_device()),
        "matmul_precision": torch.get_float32_matmul_precision(),
        "deterministic": torch.are_deterministic_algorithms_enabled(),
        "warn_only": torch.is_deterministic_algorithms_warn_only_enabled(),
        "mkldnn": (torch.backends.mkldnn.enabled, torch.backends.mkldnn.deterministic),
        "tf32": (
            torch.backends.cuda.matmul.allow_tf32,
            torch.backends.cudnn.allow_tf32,
        ),
        "cudnn": (torch.backends.cudnn.benchmark, torch.backends.cudnn.deterministic),
        "autocast_cpu": torch.is_autocast_enabled("cpu"),
        "autocast_cpu_dtype": str(torch.get_autocast_dtype("cpu")),
        "environment": {
            name: os.environ.get(name)
            for name in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_CBWR",
                "ATEN_CPU_CAPABILITY",
                "CUBLAS_WORKSPACE_CONFIG",
                "POSE_EMBED_DATA_ROOT",
                "POSE_EMBED_ARTIFACT_ROOT",
            )
        },
    }


def check_numerical_proof(
    name: str,
    *,
    enabled: bool,
    files: Mapping[str | Path, str],
    metadata: Mapping[str, Any],
    check: Callable[[], None],
) -> None:
    """Reuse success only; never retain arrays, outputs, exceptions, or partial work."""
    current = _session()
    if current is None or not enabled:
        check()
        return
    files = {__file__: sha256_file(__file__), **files}
    bindings = {}
    resolved_digests = {}
    for path, digest in files.items():
        raw, resolved = str(Path(path).absolute()), str(Path(path).resolve())
        if resolved in resolved_digests and resolved_digests[resolved] != digest:
            current.invalid = True
            raise ValueError(f"numerical proof dependency aliases conflict: {raw}")
        resolved_digests[resolved] = digest
        bindings[raw] = (resolved, digest)
    for path, identity in bindings.items():
        if path in current.files and current.files[path] != identity:
            current.invalid = True
            raise ValueError(f"numerical proof dependency was replaced: {path}")
    _rehash(current, bindings)
    runtime = numerical_runtime()
    payload = json.dumps(
        [1, name, bindings, metadata, runtime],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    key = hashlib.sha256(payload.encode()).hexdigest()
    if key in current.proofs:
        current.hits += 1
        return
    if key in current.running:
        current.invalid = True
        raise ValueError("recursive numerical proof validation is forbidden")
    current.running.add(key)
    started = perf_counter()
    try:
        if check() is not None:
            raise ValueError("numerical proof checks must not return mutable results")
    finally:
        current.running.remove(key)
        current.numerical_seconds += perf_counter() - started
        current.checks += 1
    _rehash(current, bindings)
    if (
        numerical_runtime() != runtime
        or json.dumps(
            [1, name, bindings, metadata, runtime],
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        != payload
    ):
        current.invalid = True
        raise ValueError("numerical metadata/runtime changed during proof validation")
    current.files.update(bindings)
    current.proofs.add(key)
