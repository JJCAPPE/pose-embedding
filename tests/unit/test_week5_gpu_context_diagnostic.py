"""Software-only diagnostic checks; no SCC, real dataset or GPU calls."""

import ast
import importlib.util
import io
import os
import signal
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def diagnostic():
    tracked = Path.cwd() / "scripts/operations/week5_gpu_context_diagnostic.py"
    path = os.environ.get("POSE_EMBED_TEST_GPU_DIAGNOSTIC", str(tracked))
    spec = importlib.util.spec_from_file_location("context_diagnostic_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def allocation():
    return {
        "qstat_xml": {
            "stdout": '<job_info><queue_info><job_list state="running">'
            "<JB_job_number>123</JB_job_number><state>r</state>"
            "<queue_name>gpu@scc-fixture</queue_name><slots>4</slots>"
            "</job_list></queue_info></job_info>"
        },
        "qstat_job": {
            "stdout": "hard resource_list: gpus=1,gpu_type=L40S,"
            "mem_per_core=8G,gpu_memory=16G\n"
        },
        "gpus": {
            "stdout": "0, GPU-fixture, NVIDIA L40S, Exclusive_Process, 45000, 46068\n"
        },
        "processes": {"stdout": ""},
    }


@pytest.mark.parametrize("visible", ["0", "GPU-fixture"])
def test_accepts_scheduler_index_or_uuid(diagnostic, visible):
    assert (
        diagnostic.validate_allocation(
            allocation(), job_id="123", hostname="scc-fixture.bu.edu", visible=visible
        )["uuid"]
        == "GPU-fixture"
    )


@pytest.mark.parametrize(
    "fault",
    ["host", "slots", "state", "mode", "memory", "gpus", "type", "visible", "job"],
)
def test_rejects_unverified_allocation(diagnostic, fault):
    record = allocation()
    changes = {
        "host": ("qstat_xml", "scc-fixture", "other-host"),
        "slots": ("qstat_xml", "<slots>4", "<slots>8"),
        "state": ("qstat_xml", "<state>r", "<state>s"),
        "mode": ("gpus", "Exclusive_Process", "Default"),
        "memory": ("gpus", "45000", "16000"),
        "gpus": ("qstat_job", "gpus=1", "gpus=0"),
        "type": ("qstat_job", "L40S", "A100"),
        "job": ("qstat_xml", "123", "124"),
    }
    if fault != "visible":
        key, old, new = changes[fault]
        record[key]["stdout"] = record[key]["stdout"].replace(old, new)
    with pytest.raises(ValueError):
        diagnostic.validate_allocation(
            record,
            job_id="123",
            hostname="scc-fixture",
            visible="0,1" if fault == "visible" else "0",
        )


@pytest.mark.parametrize(
    "message,expected",
    [
        ("CUDA error: CUDA-capable device(s) is/are busy or unavailable", True),
        ("device is busy", True),
        ("CUDA out of memory", False),
        ("No module named torch", False),
    ],
)
def test_only_contention_is_a_reproduction(diagnostic, message, expected):
    result = {"status": "failed", "error_message": message}
    assert diagnostic.busy_rejection(result, 1) == expected
    assert not diagnostic.busy_rejection(result, 0)


def test_coordinator_has_no_cuda_initializing_calls(diagnostic, monkeypatch):
    monkeypatch.setattr(diagnostic.torch.cuda, "is_initialized", lambda: True)
    with pytest.raises(ValueError, match="never initialize"):
        diagnostic.require_cpu_parent()
    tree = ast.parse(Path(diagnostic.__file__).read_text())
    for function in [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name != "worker"
    ]:
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and ast.unparse(node.func).startswith("torch.cuda.")
            ):
                assert node.func.attr == "is_initialized"


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"storage_passed": False, "host_memory_passed": True},
        {"storage_passed": True, "host_memory_passed": False},
    ],
)
def test_resource_failures_are_preserved_and_stop(
    diagnostic, monkeypatch, tmp_path, record
):
    monkeypatch.setattr(diagnostic, "require_cpu_parent", lambda: None)
    operations = SimpleNamespace(resource_snapshot=lambda *args, **kwargs: record)
    with pytest.raises(ValueError, match="reserve or host RAM"):
        diagnostic.resource_record(tmp_path, "before", operations, tmp_path)
    assert diagnostic.read(tmp_path / "resources/before.json") == record


def test_seal_is_checked_and_retained_after_body_failure(
    diagnostic, monkeypatch, tmp_path
):
    calls = []
    monkeypatch.setattr(diagnostic, "dataset_access", nullcontext)
    operations = SimpleNamespace(
        require_dataset_unopened=lambda **kwargs: calls.append(kwargs)
    )
    with (
        pytest.raises(RuntimeError, match="synthetic failure"),
        diagnostic.sealed_interval(tmp_path, operations),
    ):
        raise RuntimeError("synthetic failure")
    assert len(calls) == 2
    assert diagnostic.read(tmp_path / "seal-after.json")["status"] == "sealed"


def test_probe_cleans_owned_group_after_monitor_failure(
    diagnostic, monkeypatch, tmp_path
):
    process = SimpleNamespace(pid=42, stdin=io.StringIO())
    stopped = []
    monkeypatch.setattr(diagnostic, "launch", lambda *args, **kwargs: process)
    monkeypatch.setattr(
        diagnostic,
        "resource_record",
        lambda *args: (_ for _ in ()).throw(RuntimeError("quota")),
    )
    with pytest.raises(RuntimeError, match="quota"):
        diagnostic.run_probe(
            tmp_path,
            "held-probe",
            SimpleNamespace(stop_process=stopped.append),
            tmp_path,
        )
    assert stopped == [process] and process.stdin.closed


@pytest.mark.parametrize(
    "fault", [None, "occupied", "not_busy", "sequential", "seal_after"]
)
@pytest.mark.parametrize("revision", ["execution-r1", "execution-r2"])
def test_complete_coordinator_lifecycle_retains_honest_outcome(
    diagnostic, monkeypatch, tmp_path, fault, revision
):
    root = tmp_path.resolve()
    release = diagnostic.RELEASE if revision == "execution-r1" else "2" * 40
    output = root / "study-v3/operations/fixture-only-diagnostic"
    monkeypatch.setenv("JOB_ID", "123")
    monkeypatch.setenv("NSLOTS", "4")
    monkeypatch.setenv("TMPDIR", str(root))
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            diagnostic.__file__,
            "--output-dir",
            str(output),
            "--expected-release",
            release,
            "--revision",
            revision,
        ],
    )
    monkeypatch.setattr(diagnostic, "canonical_artifact_root", lambda: root)
    monkeypatch.setattr(diagnostic, "require_clean_repository", lambda: release)
    monkeypatch.setattr(diagnostic.socket, "gethostname", lambda: "scc-fixture")
    monkeypatch.setattr(diagnostic.signal, "signal", lambda *args: None)
    monkeypatch.setattr(diagnostic, "dataset_access", nullcontext)
    monkeypatch.setattr(diagnostic.torch.cuda, "is_initialized", lambda: False)
    stopped, seals, roles = [], [], []

    def seal(**kwargs):
        seals.append(kwargs)
        if fault == "seal_after" and len(seals) == 2:
            raise ValueError("seal changed")

    operations = SimpleNamespace(
        require_dataset_unopened=seal,
        interrupted=None,
        stop_process=stopped.append,
        resource_snapshot=lambda *args, **kwargs: {
            "storage_passed": True,
            "host_memory_passed": True,
        },
    )
    monkeypatch.setattr(
        diagnostic.importlib.util, "module_from_spec", lambda spec: operations
    )
    monkeypatch.setattr(
        diagnostic.importlib.util,
        "spec_from_file_location",
        lambda *args: SimpleNamespace(
            loader=SimpleNamespace(exec_module=lambda module: None)
        ),
    )

    def observe(command, **kwargs):
        record = allocation()
        if command == diagnostic.PROCESS_QUERY:
            if (fault == "occupied" and not roles) or (
                "holder" in roles and not holder.exited
            ):
                record["processes"]["stdout"] = "42, GPU-fixture, python, 426\n"
            name = "processes"
        else:
            name = (
                "gpus"
                if command == diagnostic.GPU_QUERY
                else "qstat_xml"
                if command == ["qstat", "-xml"]
                else "qstat_job"
            )
        return SimpleNamespace(returncode=0, stdout=record[name]["stdout"], stderr="")

    monkeypatch.setattr(diagnostic.subprocess, "run", observe)

    class FakeProcess:
        pid = 42
        exited = False

        def __init__(self, role):
            self.role = role
            self.stdin = io.StringIO()

        def poll(self):
            return 0 if self.exited else None

        def wait(self, timeout):
            self.exited = True
            if self.role == "holder":
                assert self.stdin.getvalue() == "release\n"
            failed = self.role == "held-probe" or (
                fault == "sequential" and self.role == "sequential-1"
            )
            result = {
                "pid": self.pid,
                "script_sha256": diagnostic.sha256_file(diagnostic.__file__),
                "status": "failed" if failed else "passed",
                "device_name": "NVIDIA L40S",
                "error_message": "out of memory"
                if fault == "not_busy"
                else "device is busy",
            }
            diagnostic.write_immutable_json(
                output / f"{self.role}-outcome.json", result
            )
            return 1 if failed else 0

    holder = FakeProcess("holder")

    def launch(path, role, **kwargs):
        assert kwargs == {"expected_release": release, "revision": revision}
        roles.append(role)
        process = holder if role == "holder" else FakeProcess(role)
        if role == "holder":
            diagnostic.write_immutable_json(
                output / "holder-ready.json",
                {
                    "pid": 42,
                    "script_sha256": diagnostic.sha256_file(diagnostic.__file__),
                    "cuda_initialized": True,
                },
            )
        return process

    monkeypatch.setattr(diagnostic, "launch", launch)
    if fault:
        with pytest.raises(ValueError):
            diagnostic.main()
    else:
        diagnostic.main()
    result = diagnostic.read(output / "summary.json")
    assert (
        result["source_release"] == release and result["execution_revision"] == revision
    )
    assert result["execution_sources_sha256"] == diagnostic.execution_binding(
        release, revision
    )
    assert result["status"] == ("failed" if fault else "passed")
    assert result["scientific_use_allowed"] is False
    assert result["parent_cuda_initialized"] is False
    assert len(seals) == 2
    assert result["evidence"]["seal-after.json"] == diagnostic.sha256_file(
        output / "seal-after.json"
    )
    if not fault:
        assert roles == ["holder", "held-probe", "sequential-1", "sequential-2"]
        assert (
            result["sequential_probe_count"] == 2
            and result["held_context_probe_rejected"]
        )
        assert len(stopped) == 4
    if fault == "occupied":
        assert not stopped and not roles


def test_frozen_cleanup_terminates_only_owned_child_group(diagnostic, tmp_path):
    spec = importlib.util.spec_from_file_location(
        "frozen_cleanup_fixture", Path.cwd() / "scripts/run_v3_execution.py"
    )
    operations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operations)
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"], start_new_session=True
    )
    try:
        operations.stop_process(child)
        assert child.poll() == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
