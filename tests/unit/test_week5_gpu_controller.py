"""Software-only external controller checks; never access SCC or licensed roots."""

import ast
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest


def load(path):
    spec = importlib.util.spec_from_file_location("gpu_controller_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def controller():
    tracked = Path.cwd() / "scripts/operations/week5_gpu_controller.py"
    return load(os.environ.get("POSE_EMBED_TEST_GPU_CONTROLLER", str(tracked)))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def allocation():
    return (
        '<job_info><queue_info><job_list state="running">'
        "<JB_job_number>123</JB_job_number><state>r</state>"
        "<queue_name>gpu@scc-fixture</queue_name><slots>4</slots>"
        "</job_list></queue_info></job_info>",
        "hard resource_list: gpu_compute_capability=7.0,gpu_memory=16G,"
        "gpu_type=L40S,gpus=1,h_rt=43200,mem_per_core=8G,nvlink=FALSE\n",
    )


@pytest.mark.parametrize(
    "fault", [None, "host", "slots", "state", "memory", "wall", "gpus", "type"]
)
def test_scheduler_allocation_matches_actual_scc_format(controller, fault):
    xml, detail = allocation()
    changes = {
        "host": ("scc-fixture", "other-host"),
        "slots": ("<slots>4", "<slots>8"),
        "state": ("<state>r", "<state>s"),
        "memory": ("mem_per_core=8G", "mem_per_core=4G"),
        "wall": ("h_rt=43200", "h_rt=1800"),
        "gpus": ("gpus=1", "gpus=0"),
        "type": ("L40S", "A100"),
    }
    if fault:
        before, after = changes[fault]
        xml, detail = xml.replace(before, after), detail.replace(before, after)
        with pytest.raises(ValueError):
            controller.validate_allocation(
                xml, detail, job_id="123", hostname="scc-fixture"
            )
    else:
        controller.validate_allocation(
            xml, detail, job_id="123", hostname="scc-fixture"
        )


def test_cuda_calls_are_confined_to_short_lived_preflight(controller, monkeypatch):
    monkeypatch.setattr(controller.torch.cuda, "is_initialized", lambda: True)
    with pytest.raises(RuntimeError, match="never initialize"):
        controller.require_cuda_free_parent()
    tree = ast.parse(Path(controller.__file__).read_text())
    for function in [node for node in tree.body if isinstance(node, ast.FunctionDef)]:
        if function.name == "gpu_preflight":
            continue
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and ast.unparse(node.func).startswith("torch.cuda.")
            ):
                assert node.func.attr == "is_initialized"


@pytest.mark.parametrize("mode", ["caches", "pilot", "corruptions", "timing"])
def test_stage_commands_preserve_frozen_invocations(
    controller, tmp_path, monkeypatch, mode
):
    operations = load(Path.cwd() / "scripts/run_v3_execution.py")
    root = tmp_path.resolve()
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(root / "synthetic-data"))
    args = SimpleNamespace(
        mode=mode,
        method="contextual" if mode == "pilot" else None,
        cache_dir=root / "caches",
        pilot_dirs=[root / name for name in controller.METHODS],
    )
    protocol, bundle, output = root / "protocol.json", root / "bundle", root / "output"
    commands = controller.stage_commands(args, operations, protocol, bundle, output)
    if mode in {"caches", "pilot"}:
        assert commands == [
            ["bash", "scripts/study_v3.qsub", mode]
            + (["contextual"] if mode == "pilot" else [])
        ]
    elif mode == "corruptions":
        assert commands == list(
            operations.corruption_commands(
                protocol, bundle, args.cache_dir, args.pilot_dirs, output
            )
        )
        assert len(commands) == 66
    else:
        assert commands == [
            [
                ".venv/bin/python",
                "scripts/time_v3_resident.py",
                "--protocol-config",
                str(protocol),
                "--cache-dir",
                str(args.cache_dir),
                "--manifest-set",
                str(bundle / "manifest-set.json"),
                "--output-dir",
                str(output),
            ]
        ]


def diagnostic(controller, root):
    record = {
        "kind": "exclusive_process_cuda_diagnostic",
        "status": "passed",
        "scientific_use_allowed": False,
        "parent_cuda_initialized": False,
        "sequential_probe_count": 2,
        "held_context_probe_rejected": True,
        "script_sha256": controller.DIAGNOSTIC_SHA256,
        "source_release": controller.RELEASE,
    }
    names = (
        "attempt.json",
        "seal-before.json",
        "seal-after.json",
        "holder-ready.json",
        "holder-outcome.json",
        "held-probe-outcome.json",
        "sequential-1-outcome.json",
        "sequential-2-outcome.json",
        "snapshots/before.json",
        "snapshots/holder-active.json",
    )
    record["evidence"] = {
        name: controller.sha256_file(save(root / name, {"fixture_only": True}))
        for name in names
    }
    return save(root / "diagnostic.json", record)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "hash",
        "status",
        "script",
        "initialized",
        "sequential",
        "missing",
        "tamper",
    ],
)
def test_real_stages_require_reviewed_diagnostic(controller, tmp_path, fault):
    root = tmp_path.resolve()
    path = diagnostic(controller, root)
    if fault in {"missing", "tamper"}:
        target = root / "holder-ready.json"
        if fault == "missing":
            target.unlink()
        else:
            target.write_text("tampered")
    elif fault and fault != "hash":
        value = controller.read(path)
        key = {
            "status": "status",
            "script": "script_sha256",
            "initialized": "parent_cuda_initialized",
            "sequential": "sequential_probe_count",
        }[fault]
        value[key] = {
            "status": "failed",
            "script": "x",
            "initialized": True,
            "sequential": 1,
        }[fault]
        save(path, value)
    digest = "0" * 64 if fault == "hash" else controller.sha256_file(path)
    if fault:
        with pytest.raises(ValueError):
            controller.validate_diagnostic(root, path, digest)
    else:
        assert controller.validate_diagnostic(root, path, digest)["sha256"] == digest


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "scientific_child",
        "parent_initialized",
        "probe_failed",
        "diagnostic_changed",
    ],
)
def test_controller_holds_locks_retains_failures_and_keeps_parent_cuda_free(
    controller, tmp_path, monkeypatch, fault
):
    root = tmp_path.resolve()
    diag = diagnostic(controller, root)
    for name, value in {
        "JOB_ID": "123",
        "NSLOTS": "4",
        "TMPDIR": str(root),
        "POSE_EMBED_MANIFEST_SET": str(root / "bundle/manifest-set.json"),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(controller, "canonical_artifact_root", lambda: root)
    monkeypatch.setattr(
        controller, "require_clean_repository", lambda: controller.RELEASE
    )
    monkeypatch.setattr(controller, "load_protocol", lambda _: object())
    monkeypatch.setattr(controller, "require_v3_design", lambda _: None)
    initialized = [False]
    monkeypatch.setattr(controller.torch.cuda, "is_initialized", lambda: initialized[0])
    held = []

    @contextmanager
    def guard():
        held.append(True)
        try:
            yield
        finally:
            held.clear()

    monkeypatch.setattr(controller, "dataset_access", guard)
    xml, detail = allocation()
    monkeypatch.setattr(controller.socket, "gethostname", lambda: "scc-fixture")
    monkeypatch.setattr(
        controller.subprocess,
        "check_output",
        lambda argv, **_: xml if argv == ["qstat", "-xml"] else detail,
    )
    signals = {}
    monkeypatch.setattr(
        controller.signal, "signal", lambda sig, handler: signals.update({sig: handler})
    )
    calls = []
    operations = SimpleNamespace(
        interrupted=lambda *_: None,
        require_dataset_unopened=lambda **_: None,
        resource_snapshot=lambda *_: {
            "storage_passed": True,
            "host_memory_passed": True,
        },
    )

    def run(command, attempt, index, _root, _peak, environment):
        assert held == [True] and not initialized[0]
        with (
            (root / "study-v3/operations/execution-r1.operation.lock").open(
                "a"
            ) as other,
            pytest.raises(BlockingIOError),
        ):
            controller.fcntl.flock(
                other, controller.fcntl.LOCK_EX | controller.fcntl.LOCK_NB
            )
        calls.append(command)
        if "--gpu-preflight-output" in command:
            output = Path(command[-1])
            save(
                output,
                {
                    "status": "failed" if fault == "probe_failed" else "passed",
                    "controller_sha256": controller.sha256_file(controller.__file__),
                    "free_bytes": 32 * 2**30,
                    "total_bytes": 48 * 2**30,
                },
            )
            return
        if command[0] == "bash":
            assert command == ["bash", "scripts/study_v3.qsub", "caches"]
            assert environment["POSE_EMBED_V3_ATTEMPT"].endswith(attempt.name)
            if fault == "scientific_child":
                raise RuntimeError("synthetic child failure")
            if fault == "parent_initialized":
                initialized[0] = True
            if fault == "diagnostic_changed":
                (root / "holder-ready.json").write_text("tampered")

    operations.run_command = run
    monkeypatch.setattr(
        controller.importlib.util,
        "spec_from_file_location",
        lambda *_: SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None)),
    )
    monkeypatch.setattr(
        controller.importlib.util, "module_from_spec", lambda _: operations
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "controller",
            "caches",
            "--remaining-peak-bytes",
            "10",
            "--recorded-by",
            "fixture",
            "--diagnostic-receipt",
            str(diag),
            "--diagnostic-sha256",
            controller.sha256_file(diag),
        ],
    )
    if fault:
        with pytest.raises((ValueError, RuntimeError)):
            controller.main()
    else:
        controller.main()
    attempt = next((root / "study-v3/operations").glob("*-123-caches"))
    assert controller.read(attempt / "outcome.json")["status"] == (
        "failed" if fault else "passed"
    )
    assert controller.read(attempt / "seal-before.json")["status"] == "sealed"
    assert controller.read(attempt / "seal-after.json")["status"] == (
        "failed" if fault == "parent_initialized" else "sealed"
    )
    assert not (
        root / controller.REVISION / "locks/selection-authorization.v3.json"
    ).exists()
    if fault == "probe_failed":
        assert len(calls) == 1
    else:
        assert len(calls) == 5
    assert not held
