"""Append-only training continuation checkpoints and verified parent chains."""

from __future__ import annotations

import math
import platform
import random
import signal
import threading
import time
from pathlib import Path

import numpy as np
import torch

from pose_embed.benchmark.runtime import (
    digest,
    now,
    read_json,
    save_checkpoint,
)
from pose_embed.provenance import sha256_file, write_immutable_json

SHARED_FILES = {
    "attempt.json",
    "batch-plan.json",
    "initialization.json",
    "memory-plan.json",
    "memory-initialization.json",
    "effective-configuration.json",
    "secondary-data-plan.json",
}


def capture_rng():
    numpy = np.random.get_state()
    return {
        "python": random.getstate(),
        "numpy": {
            "generator": numpy[0],
            "keys": torch.tensor(numpy[1].astype(np.int64)),
            "position": numpy[2],
            "has_gaussian": numpy[3],
            "gaussian": numpy[4],
        },
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else [],
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": str(torch.__version__),
            "cuda": torch.version.cuda,
        },
    }


def restore_rng(state):
    current = capture_rng()
    if state["runtime"] != current["runtime"] or len(state["cuda"]) != len(
        current["cuda"]
    ):
        raise ValueError(
            "continuation RNG runtime or visible CUDA device count differs"
        )
    numpy = state["numpy"]
    random.setstate(state["python"])
    np.random.set_state(
        (
            numpy["generator"],
            numpy["keys"].numpy().astype(np.uint32),
            numpy["position"],
            numpy["has_gaussian"],
            numpy["gaussian"],
        )
    )
    torch.set_rng_state(state["torch"])
    if state["cuda"]:
        torch.cuda.set_rng_state_all(state["cuda"])


def optimizer_layout(model, criterion, optimizer):
    names = {id(value): "model." + key for key, value in model.named_parameters()}
    names.update(
        {id(value): "criterion." + key for key, value in criterion.named_parameters()}
    )
    return [
        [names[id(value)] for value in group["params"]]
        for group in optimizer.param_groups
    ]


def restore_optimizer(model, criterion, optimizer, state, layout):
    if optimizer_layout(model, criterion, optimizer) != layout:
        raise ValueError("continuation optimizer parameter layout differs")
    groups, states = state.get("param_groups", []), state.get("state", {})
    if len(groups) != len(optimizer.param_groups):
        raise ValueError("continuation optimizer groups differ")
    indices = set()
    for live, stored in zip(optimizer.param_groups, groups, strict=True):
        if len(live["params"]) != len(stored["params"]):
            raise ValueError("continuation optimizer group is incomplete")
        if {key: value for key, value in stored.items() if key != "params"} != {
            key: value for key, value in live.items() if key != "params"
        }:
            raise ValueError("continuation optimizer hyperparameters differ")
        for parameter, index in zip(live["params"], stored["params"], strict=True):
            if index in indices:
                raise ValueError("continuation optimizer parameter is duplicated")
            indices.add(index)
            if index in states and set(states[index]) != {
                "step",
                "exp_avg",
                "exp_avg_sq",
            }:
                raise ValueError("continuation optimizer moment state is incomplete")
            for name, value in states.get(index, {}).items():
                if (
                    not isinstance(value, torch.Tensor)
                    or not torch.isfinite(value).all()
                ):
                    raise ValueError("continuation optimizer has invalid moments")
                if name in {"exp_avg", "exp_avg_sq"} and value.shape != parameter.shape:
                    raise ValueError("continuation optimizer moment shape differs")
    if not set(states).issubset(indices):
        raise ValueError("continuation optimizer has unknown parameters")
    optimizer.load_state_dict(state)


class StopAtBoundary:
    """Signals request a stop; no partial optimizer update is checkpointed."""

    def __init__(self):
        self.reason = None
        self.previous = {}

    def __enter__(self):
        if threading.current_thread() is threading.main_thread():
            for name in ("SIGTERM", "SIGINT", "SIGUSR1"):
                if hasattr(signal, name):
                    number = getattr(signal, name)
                    self.previous[number] = signal.getsignal(number)
                    signal.signal(number, self._request)
        return self

    def _request(self, number, _frame):
        self.reason = "signal:" + signal.Signals(number).name

    def __exit__(self, *_args):
        for number, handler in self.previous.items():
            signal.signal(number, handler)


def _member(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError("continuation artifact escaped its experiment")
    return path


def verify_chain(root, leaf, identity, *, completed=False):
    """Hash every ancestor and checkpoint, accumulating one unbroken step history."""
    root = Path(root).resolve()
    leaf = Path(leaf).resolve()
    if leaf.is_dir():
        leaf /= "segment-manifest.json"
    if not leaf.is_relative_to(root / "segments"):
        raise ValueError("resume checkpoint must belong to this experiment")
    chain, seen = [], set()
    path = leaf
    expected_hash = None
    while path is not None:
        if path in seen:
            raise ValueError("continuation parent chain contains a cycle")
        seen.add(path)
        if expected_hash is not None and sha256_file(path) != expected_hash:
            raise ValueError("continuation parent manifest changed")
        manifest = read_json(path)
        if (
            manifest.get("schema_version") != 1
            or manifest.get("kind") != "training_segment"
            or manifest.get("identity_sha256") != digest(identity)
        ):
            raise ValueError("continuation segment identity differs")
        for name, checksum in manifest.get("outputs", {}).items():
            if Path(name).name != name or sha256_file(path.parent / name) != checksum:
                raise ValueError("continuation segment evidence changed")
        if not {"checkpoint.pt", "history.json", "attempt.json"}.issubset(
            manifest.get("outputs", {})
        ):
            raise ValueError("continuation segment evidence is incomplete")
        for name, checksum in manifest.get("shared", {}).items():
            if name not in SHARED_FILES or sha256_file(root / name) != checksum:
                raise ValueError("continuation shared evidence changed")
        if set(manifest.get("shared", {})) != {
            name for name in SHARED_FILES if (root / name).exists()
        }:
            raise ValueError("continuation shared bindings are incomplete")
        best = manifest.get("best")
        if (
            best is not None
            and sha256_file(_member(root, best["path"])) != best["sha256"]
        ):
            raise ValueError("continuation selected checkpoint changed")
        chain.append((path, manifest))
        parent = manifest.get("parent")
        path = _member(root, parent["path"]) if parent else None
        expected_hash = parent["sha256"] if parent else None
    chain.reverse()
    rows, elapsed = [], 0.0
    batches = read_json(root / "batch-plan.json")["steps"]
    peak_allocated = peak_reserved = 0
    for index, (path, manifest) in enumerate(chain):
        if index and chain[index - 1][1]["status"] != "resumable":
            raise ValueError("a completed segment cannot have a continuation")
        start, end = manifest.get("start_step"), manifest.get("end_step")
        if (
            type(start) is not int
            or type(end) is not int
            or start != len(rows) + 1
            or not start <= end <= identity["steps"]
        ):
            raise ValueError("continuation step chain is incomplete")
        part = read_json(path.parent / "history.json")["steps"]
        if len(part) != end - start + 1 or any(
            row.get("step") != step or not math.isfinite(row.get("loss", math.nan))
            for step, row in zip(range(start, end + 1), part, strict=True)
        ):
            raise ValueError("continuation history prefix is invalid")
        rows.extend(part)
        from pose_embed.benchmark.training import phase_for_step

        recipe = identity["training_recipe"]
        if any(row.get("phase") != phase_for_step(recipe, row["step"]) for row in part):
            raise ValueError("continuation training phase differs")
        if identity["stage"] == "development":
            every = identity["configuration"]["training"]["validation_every"]
            expected = [
                i
                for i in range(start, end + 1)
                if i % every == 0 or i == identity["steps"]
            ]
            if [row["step"] for row in part if "validation" in row] != expected:
                raise ValueError("continuation validation schedule differs")
            eligible = [
                row
                for row in rows
                if "validation" in row
                and row["step"] >= recipe["minimum_selected_step"]
                and ("secondary" not in identity or row["step"] == identity["steps"])
            ]
            best = manifest["best"]
            if eligible:
                chosen = max(eligible, key=lambda row: row["validation"]["r_at_1"])
                if (
                    best is None
                    or best["selected_step"] != chosen["step"]
                    or best["score"] != chosen["validation"]["r_at_1"]
                ):
                    raise ValueError(
                        "continuation selected validation checkpoint differs"
                    )
            elif best is not None:
                raise ValueError(
                    "continuation selected a checkpoint before eligibility"
                )
        if manifest.get("batch_prefix_sha256") != digest(batches[:end]) or manifest.get(
            "history_prefix_sha256"
        ) != digest(rows):
            raise ValueError("continuation batch/history prefix differs")
        if manifest.get("status") != (
            "complete" if end == identity["steps"] else "resumable"
        ):
            raise ValueError("continuation status differs from the experiment budget")
        telemetry = manifest["telemetry"]
        if (
            not math.isfinite(telemetry["segment_elapsed_seconds"])
            or telemetry["segment_elapsed_seconds"] < 0
        ):
            raise ValueError("continuation telemetry is invalid")
        elapsed += telemetry["segment_elapsed_seconds"]
        peak_allocated = max(peak_allocated, telemetry["peak_allocated_bytes"])
        peak_reserved = max(peak_reserved, telemetry["peak_reserved_bytes"])
        if (
            telemetry["elapsed_seconds"] != elapsed
            or telemetry["training_steps"] != end
        ):
            raise ValueError("continuation cumulative telemetry differs")
    if completed and len(rows) != identity["steps"]:
        raise ValueError("continuation experiment is not complete")
    return {
        "manifest": chain[-1][1],
        "path": leaf,
        "rows": rows,
        "elapsed_seconds": elapsed,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "chain": [str(path.relative_to(root)) for path, _ in chain],
    }


def begin_segment(root, identity, parent=None):
    root = Path(root)
    if (root / "outcome.json").exists() or (root / "run-manifest.json").exists():
        raise ValueError("a finalized experiment cannot be continued")
    directory = root / "segments"
    directory.mkdir(exist_ok=True)
    existing = sorted(p for p in directory.iterdir() if p.is_dir() and p.name.isdigit())
    sealed = [
        p / "segment-manifest.json"
        for p in existing
        if (p / "segment-manifest.json").exists()
    ]
    if (
        sealed and (parent is None or sealed[-1].resolve() != parent["path"].resolve())
    ) or (parent and not sealed):
        raise ValueError("resume must extend the latest sealed segment")
    number = max((int(p.name) for p in existing), default=0) + 1
    leaf = directory / f"{number:06d}"
    leaf.mkdir(exist_ok=False)
    write_immutable_json(
        leaf / "attempt.json",
        {
            "identity_sha256": digest(identity),
            "parent_sha256": sha256_file(parent["path"]) if parent else None,
            "started_at": now(),
        },
    )
    return leaf


def seal_segment(
    root,
    leaf,
    identity,
    parent,
    checkpoint,
    best_state,
    best_result,
    selected_step,
    best_score,
    history,
    batches,
    elapsed,
    environment,
    peak_allocated,
    peak_reserved,
    reason,
):
    seal_started = time.perf_counter()
    root, leaf = Path(root), Path(leaf)
    start = len(parent["rows"]) + 1 if parent else 1
    end = checkpoint["step"]
    prior_elapsed = parent["elapsed_seconds"] if parent else 0.0
    best = parent["manifest"]["best"] if parent else None
    if best_state is not None and (
        best is None or selected_step != best["selected_step"]
    ):
        save_checkpoint(
            leaf / "best.pt",
            {
                "identity": identity,
                "selected_step": selected_step,
                "result": best_result,
                **best_state,
            },
        )
        best = {
            "path": str((leaf / "best.pt").relative_to(root)),
            "sha256": sha256_file(leaf / "best.pt"),
            "selected_step": selected_step,
            "score": best_score,
        }
    checkpoint.update(
        {
            "identity": identity,
            "best": best,
            "history_prefix_sha256": digest(history),
            "batch_prefix_sha256": digest(batches[:end]),
        }
    )
    save_checkpoint(leaf / "checkpoint.pt", checkpoint)
    write_immutable_json(leaf / "history.json", {"steps": history[start - 1 :]})
    outputs = ["attempt.json", "checkpoint.pt", "history.json"]
    if (leaf / "best.pt").exists():
        outputs.append("best.pt")
    checkpoint_seconds = time.perf_counter() - seal_started
    elapsed += checkpoint_seconds
    manifest = {
        "schema_version": 1,
        "kind": "training_segment",
        "identity_sha256": digest(identity),
        "parent": {
            "path": str(parent["path"].relative_to(root)),
            "sha256": sha256_file(parent["path"]),
        }
        if parent
        else None,
        "status": "complete" if end == identity["steps"] else "resumable",
        "start_step": start,
        "end_step": end,
        "reason": reason,
        "batch_prefix_sha256": digest(batches[:end]),
        "history_prefix_sha256": digest(history),
        "best": best,
        "outputs": {name: sha256_file(leaf / name) for name in outputs},
        "shared": {
            name: sha256_file(root / name)
            for name in sorted(SHARED_FILES)
            if (root / name).exists()
        },
        "telemetry": {
            "checkpoint_write_seconds": checkpoint_seconds,
            "checkpoint_bytes": (leaf / "checkpoint.pt").stat().st_size,
            "new_best_checkpoint_bytes": (leaf / "best.pt").stat().st_size
            if (leaf / "best.pt").exists()
            else 0,
            "segment_elapsed_seconds": elapsed,
            "elapsed_seconds": prior_elapsed + elapsed,
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "training_steps": end,
            "environment": environment,
        },
        "sealed_at": now(),
    }
    write_immutable_json(leaf / "segment-manifest.json", manifest)
    return manifest


def _equal_state(first, second):
    if isinstance(first, torch.Tensor):
        return (
            isinstance(second, torch.Tensor)
            and first.dtype == second.dtype
            and torch.equal(first, second)
        )
    if isinstance(first, dict):
        return (
            isinstance(second, dict)
            and first.keys() == second.keys()
            and all(_equal_state(value, second[key]) for key, value in first.items())
        )
    if isinstance(first, (list, tuple)):
        return (
            isinstance(second, type(first))
            and len(first) == len(second)
            and all(_equal_state(a, b) for a, b in zip(first, second, strict=True))
        )
    return first == second


def verify_completed_segments(root, identity, checkpoint, history):
    record = read_json(root / "segments.json")
    leaf = _member(root, record["leaf"])
    if record.get("schema_version") != 1 or sha256_file(leaf) != record.get(
        "leaf_sha256"
    ):
        raise ValueError("completed continuation chain binding differs")
    chain = verify_chain(root, leaf, identity, completed=True)
    if (
        chain["chain"] != record.get("chain")
        or chain["rows"] != history["steps"]
        or chain["elapsed_seconds"] != history["elapsed_seconds"]
    ):
        raise ValueError("completed continuation history differs from the experiment")
    best = chain["manifest"]["best"]
    if best is None:
        raise ValueError("completed continuation lacks its selected checkpoint")
    selected = torch.load(
        _member(root, best["path"]), map_location="cpu", weights_only=True
    )
    selected.pop("result")
    if not _equal_state(selected, checkpoint):
        raise ValueError("completed continuation selected state differs")
    telemetry = read_json(root / "telemetry.json")
    if (
        telemetry["elapsed_seconds"] != chain["elapsed_seconds"]
        or telemetry["peak_allocated_bytes"] != chain["peak_allocated_bytes"]
        or telemetry["peak_reserved_bytes"] != chain["peak_reserved_bytes"]
    ):
        raise ValueError("completed continuation resource totals differ")
    return chain


def load_continuation(root, parent, identity):
    state = torch.load(
        parent["path"].parent / "checkpoint.pt", map_location="cpu", weights_only=True
    )
    manifest = parent["manifest"]
    if (
        state.get("identity") != identity
        or state.get("step") != manifest["end_step"]
        or state.get("history_prefix_sha256") != manifest["history_prefix_sha256"]
        or state.get("batch_prefix_sha256") != manifest["batch_prefix_sha256"]
        or state.get("best") != manifest["best"]
    ):
        raise ValueError("continuation checkpoint differs from its sealed evidence")
    if state["step"] >= identity["steps"]:
        raise ValueError("completed experiment cannot be resumed")
    if (
        state.get("training_state", {}).get("step") != state["step"]
        or state["training_state"].get("phase") != parent["rows"][-1]["phase"]
    ):
        raise ValueError("continuation training cursor differs from its history")
    best = (
        torch.load(
            _member(Path(root), manifest["best"]["path"]),
            map_location="cpu",
            weights_only=True,
        )
        if manifest["best"]
        else None
    )
    if best is not None and (
        best.get("identity") != identity
        or best.get("selected_step") != manifest["best"]["selected_step"]
    ):
        raise ValueError("continuation best checkpoint identity differs")
    return state, best


def verify_environment(previous, current):
    excluded = {"hostname", "cuda_device_uuid", "device_index"}
    if {k: v for k, v in previous.items() if k not in excluded} != {
        k: v for k, v in current.items() if k not in excluded
    }:
        raise ValueError("continuation numeric environment or device model differs")


def restore_module(module, state):
    expected = module.state_dict()
    if state.keys() != expected.keys() or any(
        not isinstance(value, torch.Tensor)
        or value.dtype != expected[key].dtype
        or value.shape != expected[key].shape
        or not torch.isfinite(value).all()
        for key, value in state.items()
    ):
        raise ValueError(
            "continuation model/criterion state shape, dtype or values differ"
        )
    module.load_state_dict(state, strict=True)
