"""Synthetic checks for the external parity input correction; no SCC or data access."""

import hashlib
import importlib.util
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest


def load(path):
    spec = importlib.util.spec_from_file_location("parity_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    revision = tmp_path / "execution-r2"
    cache = revision / "accepted-cache"
    cache.mkdir(parents=True)
    for name in ("development-gallery.npz", "development-gallery.npz.manifest.json"):
        (cache / name).write_text("synthetic gallery fixture")
    (cache / "parity.json").write_text("original GPU parity")
    destination = revision / "corruption-inputs/fresh-allocation"
    helper = load("scripts/operations/week5_corruption_parity.py")
    return helper, revision, cache, destination


def test_frozen_commands_use_fresh_parity_and_original_gallery(inputs, monkeypatch):
    helper, revision, cache, destination = inputs
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(revision / "synthetic-data"))
    helper.prepare_inputs(cache, destination, revision)
    (destination / "parity.json").write_text("new GPU parity")
    operations = load("scripts/run_v3_execution.py")
    commands = list(
        operations.corruption_commands(
            revision / "protocol.json",
            revision / "manifests",
            destination,
            [revision / arm for arm in operations.METHODS],
            revision / "outputs",
        )
    )
    assert len(commands) == 66
    assert len([c for c in commands if c[1:3] == ["features", "extract"]]) == 9
    for command in commands:
        if "--parity-evidence" in command:
            assert (
                Path(command[command.index("--parity-evidence") + 1])
                == destination / "parity.json"
            )
        if (
            "--input" in command
            and "development-gallery.npz" in command[command.index("--input") + 1]
        ):
            assert (
                Path(command[command.index("--input") + 1]).resolve()
                == cache / "development-gallery.npz"
            )
    assert (
        destination / "development-gallery.npz.manifest.json"
    ).resolve() == cache / "development-gallery.npz.manifest.json"
    assert (cache / "parity.json").read_text() == "original GPU parity"


@pytest.mark.parametrize("fault", ["escape", "existing", "missing", "alias"])
def test_input_links_reject_escape_overwrite_and_unbound_gallery(inputs, fault):
    helper, revision, cache, destination = inputs
    gallery = cache / "development-gallery.npz"
    if fault == "escape":
        destination = revision.parent / "outside"
    elif fault == "existing":
        destination.mkdir(parents=True)
    elif fault == "missing":
        gallery.unlink()
    else:
        gallery.rename(cache / "other.npz")
        gallery.symlink_to(cache / "other.npz")
    with pytest.raises((ValueError, FileExistsError)):
        helper.prepare_inputs(cache, destination, revision)


@pytest.mark.parametrize(
    "fault", [None, "lock", "parity", "seal", "escape", "existing"]
)
@pytest.mark.parametrize("mode", ["corruptions", "parity-only"])
def test_prelude_retains_failures_and_only_executes_controller_after_success(
    inputs, monkeypatch, fault, mode
):
    helper, revision, cache, destination = inputs
    root = revision.parent
    revision.rename(root / "old")
    revision = root / "study-v3/revisions/execution-r2"
    revision.parent.mkdir(parents=True)
    (root / "old").rename(revision)
    cache, destination = revision / cache.name, revision / "corruption-inputs/fresh"
    if fault == "escape":
        destination = root / "outside"
    elif fault == "existing":
        destination.mkdir(parents=True)
    child = [
        ".venv/bin/python",
        "scripts/operations/week5_gpu_controller.py",
        "corruptions",
        "--cache-dir",
        str(destination),
        "--remaining-peak-bytes",
        "202000000000",
    ]
    packet = root / "packet.json"
    payload = {
        "bindings": {},
        "remaining_peak_bytes": 202000000000,
        "input_dir": str(destination),
        "diagnostic_receipt": "fixture-diagnostic",
        "diagnostic_sha256": "a" * 64,
    }
    if mode == "corruptions":
        payload.update(
            runtime_gate="fixture-gate.py",
            controller_command=child,
            cache_dir=str(cache),
            cache_acceptance="fixture-acceptance",
        )
    packet.write_text(json.dumps(payload))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prelude",
            mode,
            "--inputs",
            str(packet),
            "--inputs-sha256",
            hashlib.sha256(packet.read_bytes()).hexdigest(),
            "--expected-release",
            helper.RELEASE,
            "--revision",
            helper.REVISION,
            "--remaining-peak-bytes",
            "202000000000",
        ],
    )
    monkeypatch.setenv("JOB_ID", "123")
    monkeypatch.setenv("NSLOTS", "4")
    monkeypatch.setattr(helper, "canonical_artifact_root", lambda: root)
    monkeypatch.setattr(helper, "dataset_access", nullcontext)
    monkeypatch.setattr(helper, "load_protocol", lambda _: None)
    monkeypatch.setattr(helper, "require_v3_design", lambda _: None)
    calls, executed, commands, cuda_guards = [], [], [], []

    def seal(**_):
        calls.append("seal")
        if fault == "seal" and len(calls) == 2:
            raise ValueError("synthetic seal failure")

    def run(command, attempt, index, *args):
        commands.append(command)
        if index == 1:
            if fault == "parity":
                raise RuntimeError("synthetic parity failure")
            (destination / "parity.json").write_text("synthetic parity")

    modules = {
        "operations": SimpleNamespace(
            interrupted=lambda *_: None, require_dataset_unopened=seal, run_command=run
        ),
        "controller": SimpleNamespace(
            require_cuda_free_parent=lambda: cuda_guards.append(True),
            execution_binding=lambda *_: {},
            validate_allocation=lambda **_: None,
            validate_diagnostic=lambda *_, **__: None,
            subprocess=SimpleNamespace(
                check_output=lambda *_, **__: "synthetic allocation"
            ),
        ),
        "gate": SimpleNamespace(check_command=lambda _: None),
    }
    monkeypatch.setattr(
        helper.importlib.util,
        "spec_from_file_location",
        lambda name, _: SimpleNamespace(
            name=name, loader=SimpleNamespace(exec_module=lambda _: None)
        ),
    )
    monkeypatch.setattr(
        helper.importlib.util, "module_from_spec", lambda spec: modules[spec.name]
    )
    monkeypatch.setattr(helper.signal, "signal", lambda *_: None)
    monkeypatch.setattr(helper.os, "execv", lambda *args: executed.append(args))
    if fault == "lock":

        def locked(*_):
            raise BlockingIOError("synthetic lock conflict")

        monkeypatch.setattr(helper.fcntl, "flock", locked)
    if fault:
        with pytest.raises(
            (RuntimeError, ValueError, BlockingIOError, FileExistsError)
        ):
            helper.main()
    else:
        helper.main()
    suffix = "corruption-parity" if mode == "corruptions" else "runtime-parity"
    attempt = root / f"study-v3/operations/{destination.name}-123-{suffix}"
    outcome = json.loads((attempt / "outcome.json").read_text())
    assert outcome["status"] == ("failed" if fault else "passed")
    assert executed == (
        [(child[0], child)] if not fault and mode == "corruptions" else []
    )
    if mode == "parity-only":
        assert outcome["parity_only"] is True
        assert outcome["corruptions_launched"] is False
    if not fault:
        assert len(commands) == 2
        assert commands[0][2] == "--gpu-preflight-output"
        assert commands[1][1:3] == ["features", "parity"]
        assert len(cuda_guards) == 4
        assert json.loads((attempt / "seal-before.json").read_text())["status"] == (
            "sealed"
        )
        assert json.loads((attempt / "seal-after.json").read_text())["status"] == (
            "sealed"
        )
        record = json.loads((attempt / "attempt.json").read_text())
        if mode == "parity-only":
            assert record["kind"] == "allocation_local_runtime_parity"
            assert record["parity_only"] is True
            assert record["corruptions_launched"] is False
            assert "cache_acceptance" not in record
            assert "original_gallery_links" not in record
            assert sorted(path.name for path in destination.iterdir()) == [
                "parity.json"
            ]
        else:
            assert record["kind"] == "allocation_local_corruption_parity"
            assert "parity_only" not in record
    if fault == "seal":
        assert (
            json.loads((attempt / "seal-after.json").read_text())["error_message"]
            == "synthetic seal failure"
        )


@pytest.mark.parametrize("mode", ["corruptions", "parity-only"])
def test_runtime_gate_adds_only_the_bound_parity_target(mode):
    gate = load("scripts/operations/week5_corruption_runtime_gate.py")
    assert (
        hashlib.sha256(Path(gate.PARITY_ENTRYPOINT).read_bytes()).hexdigest()
        == gate.PARITY_SHA256
    )
    command = [
        ".venv/bin/python",
        gate.PARITY_ENTRYPOINT,
        mode,
        "--inputs",
        "/fixture/packet.json",
        "--inputs-sha256",
        "a" * 64,
        "--revision",
        "execution-r2",
        "--expected-release",
        gate.RELEASE,
        "--remaining-peak-bytes",
        "202000000000",
    ]
    gate.check_command(command)
    for changed in [
        command[:1] + ["/other/prelude.py"] + command[2:],
        command[:2] + ["timing"] + command[3:],
        command + ["--inputs", "/other/packet.json"],
        command + ["--help"],
    ]:
        with pytest.raises(ValueError):
            gate.check_command(changed)
