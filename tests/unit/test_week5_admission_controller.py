"""Operational fixture checks; never scientific admission or SCC execution."""

import importlib.util
import json
import os
import signal
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest


def load(path):
    spec = importlib.util.spec_from_file_location("operational_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def wrapper():
    return load(
        os.environ.get(
            "POSE_EMBED_TEST_ADMISSION_WRAPPER",
            str(Path.cwd() / "scripts/operations/week5_admission_controller.py"),
        )
    )


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def allocation():
    return (
        '<job_info><queue_info><job_list state="running">'
        "<JB_job_number>123</JB_job_number><state>r</state>"
        "<queue_name>cpu@scc-fixture</queue_name><slots>4</slots>"
        "</job_list></queue_info></job_info>",
        "hard resource_list: mem_per_core=8G,h_rt=12:00:00\n",
    )


@pytest.mark.parametrize(
    "fault", [None, "host", "slots", "state", "memory", "wall", "gpu"]
)
def test_requires_exact_live_cpu_allocation(wrapper, fault):
    xml, text = allocation()
    if fault == "host":
        xml = xml.replace("scc-fixture", "different-host")
    elif fault == "slots":
        xml = xml.replace("<slots>4", "<slots>8")
    elif fault == "state":
        xml = xml.replace("<state>r", "<state>s")
    elif fault == "memory":
        text = text.replace("8G", "4G")
    elif fault == "wall":
        text = text.replace("12:00:00", "48:00:00")
    elif fault == "gpu":
        text = text.replace("mem_per_core", "gpus=1,mem_per_core")
    if fault:
        with pytest.raises(ValueError):
            wrapper.validate_cpu_allocation(
                xml, text, job_id="123", hostname="scc-fixture"
            )
    else:
        wrapper.validate_cpu_allocation(xml, text, job_id="123", hostname="scc-fixture")


def inputs(wrapper, root, monkeypatch):
    assembler = save(root / "fixture-assembler.py", {"fixture_only": True})
    monkeypatch.setattr(wrapper, "ASSEMBLER_SHA256", wrapper.sha256_file(assembler))
    value = {"release_sha": wrapper.RELEASE, "operations": {}, "seal_evidence": []}
    for key in wrapper.PARAMETER_FILES:
        value[key] = str(save(root / f"{key}.json", {"remaining_peak_bytes": 10}))
    source = save(root / "source-inputs.json", value)
    return assembler, source


def test_inputs_are_bound_and_no_null_storage_forecast_is_accepted(
    wrapper, tmp_path, monkeypatch
):
    root = tmp_path.resolve()
    assembler, source = inputs(wrapper, root, monkeypatch)
    digest = wrapper.sha256_file(source)
    records = wrapper.input_bindings(root, source, assembler, digest, 10)
    wrapper.verify_bindings(root, records)
    save(root / "capacity_measurements.json", {"remaining_peak_bytes": None})
    with pytest.raises(ValueError, match="concrete"):
        wrapper.input_bindings(root, source, assembler, digest, 10)
    with pytest.raises(ValueError, match="changed"):
        wrapper.verify_bindings(root, records)
    with pytest.raises(ValueError, match="reviewed SHA"):
        wrapper.input_bindings(root, source, assembler, "0" * 64, 10)


def test_candidate_path_is_new_and_command_only_runs_assembler(wrapper, tmp_path):
    root = tmp_path.resolve()
    attempt = root / "study-v3/operations/fixture-123-admission"
    output = wrapper.candidate_directory(root, attempt)
    assert output.is_relative_to(root / wrapper.REVISION)
    command = wrapper.assembler_command(
        root / "assembler.py", root / "inputs.json", output, "fixture"
    )
    assert command[0] == ".venv/bin/python3.11"
    assert "authorize-selection" not in command
    output.mkdir(parents=True)
    with pytest.raises(ValueError, match="already exists"):
        wrapper.candidate_directory(root, attempt)


@pytest.mark.parametrize("revision", ["execution-r1", "execution-r2"])
@pytest.mark.parametrize("fault", [None, "child_failure", "input_change", "signal"])
def test_wrapper_preserves_attempts_locks_seals_and_never_publishes(
    wrapper, tmp_path, monkeypatch, fault, revision
):
    # Scientific validator seams are replaced only here; the fake child emits
    # an explicitly fixture-only candidate inside this temporary test root.
    root = tmp_path.resolve()
    assembler, source = inputs(wrapper, root, monkeypatch)
    release = wrapper.RELEASE if revision == "execution-r1" else "a" * 40
    value = wrapper.read(source)
    value.update(release_sha=release)
    if revision == "execution-r2":
        value["execution_revision"] = revision
    save(source, value)
    source_hashes = (
        {path: wrapper.sha256_file(path) for path in wrapper.EXECUTION_SOURCES}
        if revision == "execution-r2"
        else {}
    )
    if source_hashes:
        source_hashes[wrapper.EXECUTION_SOURCES[1]] = wrapper.sha256_file(assembler)
    monkeypatch.setattr(wrapper, "execution_binding", lambda *_: source_hashes)
    canonical = (
        root / "study-v3/revisions" / revision / "locks/selection-authorization.v3.json"
    )
    protocol = SimpleNamespace(
        test_access=SimpleNamespace(
            selection_authorization_relative_path=str(canonical.relative_to(root)),
        )
    )
    monkeypatch.setenv("JOB_ID", "123")
    monkeypatch.setenv("NSLOTS", "4")
    monkeypatch.setenv("TMPDIR", str(root))
    monkeypatch.setattr(wrapper, "canonical_artifact_root", lambda: root)
    monkeypatch.setattr(wrapper, "require_clean_repository", lambda: wrapper.RELEASE)
    monkeypatch.setattr(wrapper, "load_protocol", lambda _: protocol)
    monkeypatch.setattr(wrapper, "require_v3_design", lambda _: None)
    monkeypatch.setattr(wrapper, "protocol_digest", lambda _: "a" * 64)
    monkeypatch.setattr(
        wrapper,
        "current_code_hashes",
        lambda: SimpleNamespace(model_dump=lambda: {"fixture": "b" * 64}),
    )
    guard = []

    @contextmanager
    def dataset_guard():
        guard.append("held")
        try:
            yield
        finally:
            guard.clear()

    monkeypatch.setattr(wrapper, "dataset_access", dataset_guard)
    xml, detail = allocation()
    monkeypatch.setattr(wrapper.socket, "gethostname", lambda: "scc-fixture")
    monkeypatch.setattr(
        wrapper.subprocess,
        "check_output",
        lambda argv, **kwargs: xml if argv == ["qstat", "-xml"] else detail,
    )
    signals = {}
    monkeypatch.setattr(
        wrapper.signal, "signal", lambda name, handler: signals.update({name: handler})
    )
    operations = SimpleNamespace(
        require_dataset_unopened=lambda **_: None,
        resource_snapshot=lambda *args: {
            "storage_passed": True,
            "host_memory_passed": True,
        },
        interrupted=lambda signum, frame: None,
    )

    def run(command, attempt, index, *args):
        assert guard == ["held"]
        with (
            (root / "study-v3/operations/execution-r1.operation.lock").open(
                "a"
            ) as competing,
            pytest.raises(BlockingIOError),
        ):
            wrapper.fcntl.flock(
                competing, wrapper.fcntl.LOCK_EX | wrapper.fcntl.LOCK_NB
            )
        if index != 2:
            return
        assert command == wrapper.assembler_command(
            assembler,
            attempt / "inputs.json",
            Path(command[command.index("--output-dir") + 1]),
            "fixture",
            expected_release=release,
            revision=revision,
        )
        if fault == "child_failure":
            raise RuntimeError("fixture child failed")
        if fault == "signal":
            raise SystemExit(143)
        output = Path(command[command.index("--output-dir") + 1])
        candidate = save(
            output / "selection-authorization.candidate.json",
            {"scientific_use_allowed": False, "fixture_only": True},
        )
        save(
            output / "assembly-outcome.json",
            {
                "status": "passed",
                "canonical_authorization_written": False,
                "candidate": wrapper.binding(root, candidate),
                "complete_authorization_validation_seconds": 1,
            },
        )
        if fault == "input_change":
            source.write_text("changed after child read")

    operations.run_command = run
    monkeypatch.setattr(
        wrapper.importlib.util,
        "spec_from_file_location",
        lambda *args: SimpleNamespace(
            loader=SimpleNamespace(exec_module=lambda _: None)
        ),
    )
    monkeypatch.setattr(
        wrapper.importlib.util, "module_from_spec", lambda _: operations
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wrapper",
            "--assembler",
            str(assembler),
            "--inputs",
            str(source),
            "--inputs-sha256",
            wrapper.sha256_file(source),
            "--remaining-peak-bytes",
            "10",
            "--recorded-by",
            "fixture",
            "--expected-release",
            release,
            "--revision",
            revision,
        ],
    )
    if fault:
        with pytest.raises((RuntimeError, ValueError, SystemExit)):
            wrapper.main()
    else:
        wrapper.main()
    attempt = next((root / "study-v3/operations").glob("*-123-admission"))
    assert wrapper.read(attempt / "outcome.json")["status"] == (
        "failed" if fault else "passed"
    )
    assert wrapper.read(attempt / "seal-before.json")["status"] == "sealed"
    assert wrapper.read(attempt / "seal-after.json")["status"] == "sealed"
    assert (attempt / "inputs.json").is_file()
    assert not canonical.exists()
    assert set(signals) == {signal.SIGTERM, signal.SIGHUP}
    assert guard == []


def test_frozen_monitor_signal_kills_real_fixture_child_and_keeps_evidence(
    tmp_path, monkeypatch
):
    operations = load(Path.cwd() / "scripts/run_v3_execution.py")
    processes = []
    original = subprocess.Popen

    def launch(*args, **kwargs):
        assert kwargs["start_new_session"] is True
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    def snapshot(*args, **kwargs):
        if kwargs.get("process_group") is not None:
            operations.interrupted(signal.SIGTERM, None)
        return {"storage_passed": True, "host_memory_passed": True}

    monkeypatch.setattr(operations.subprocess, "Popen", launch)
    monkeypatch.setattr(operations, "resource_snapshot", snapshot)
    with pytest.raises(SystemExit):
        operations.run_command(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            tmp_path,
            0,
            tmp_path,
            10,
            dict(os.environ),
        )
    assert len(processes) == 1 and processes[0].poll() is not None
    assert (tmp_path / "command-000.log").is_file()
    outcome = json.loads((tmp_path / "commands/000-outcome.json").read_text())
    assert outcome["status"] == "failed" and outcome["error_type"] == "SystemExit"


def test_wrapper_holds_gpu_diagnostic_and_probe_bindings(
    wrapper, tmp_path, monkeypatch
):
    root = tmp_path.resolve()
    assembler, source = inputs(wrapper, root, monkeypatch)
    operation = root / "study-v3/operations/fixture-123-caches"
    diagnostic = root / "study-v3/operations/fixture-122-gpu-diagnostic"
    observed = save(diagnostic / "held-probe-outcome.json", {"fixture": True})
    receipt = save(
        diagnostic / "summary.json",
        {"evidence": {observed.name: wrapper.sha256_file(observed)}},
    )
    save(operation / "diagnostic-binding.json", wrapper.binding(root, receipt))
    for name in ("attempt.json", "outcome.json"):
        save(operation / name, {"fixture": True})
    preflight = save(operation / "gpu-preflights/000.json", {"fixture": True})
    save(
        operation / "commands/000.json",
        {"argv": ["fixture-controller", "--gpu-preflight-output", str(preflight)]},
    )
    accounting = operation / "qacct.txt"
    accounting.write_text("fixture")
    value = wrapper.read(source)
    value["operations"] = {
        "caches": {"directory": str(operation), "scheduler_accounting": str(accounting)}
    }
    save(source, value)
    records = wrapper.input_bindings(
        root, source, assembler, wrapper.sha256_file(source), 10
    )
    assert wrapper.binding(root, observed) in records
    assert wrapper.binding(root, preflight) in records
    preflight.unlink()
    with pytest.raises(ValueError, match="existing canonical-root"):
        wrapper.input_bindings(root, source, assembler, wrapper.sha256_file(source), 10)
    observed.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        wrapper.verify_bindings(root, records)


@pytest.mark.parametrize("fault", [None, "release", "legacy", "short_sha", "self"])
def test_successor_controller_requires_clean_tracked_full_release(
    wrapper, monkeypatch, fault
):
    release = "a" * 40
    monkeypatch.setattr(wrapper, "require_clean_repository", lambda: release)
    if fault == "self":
        monkeypatch.setattr(wrapper, "__file__", "pyproject.toml")
    supplied = {
        "release": "b" * 40,
        "legacy": wrapper.RELEASE,
        "short_sha": "abcdef0",
    }.get(fault, release)
    if fault:
        with pytest.raises(ValueError, match="release"):
            wrapper.execution_binding(supplied, "execution-r2")
    else:
        assert wrapper.execution_binding(supplied, "execution-r2") == {
            path: wrapper.sha256_file(path) for path in wrapper.EXECUTION_SOURCES
        }


@pytest.mark.parametrize(
    "fault", [None, "old_revision", "old_release", "changed_assembler"]
)
def test_successor_inputs_require_same_revision_and_tracked_assembler(
    wrapper, tmp_path, monkeypatch, fault
):
    root = tmp_path.resolve()
    assembler, source = inputs(wrapper, root, monkeypatch)
    value = wrapper.read(source) | {
        "release_sha": "a" * 40,
        "execution_revision": "execution-r2",
    }
    if fault == "old_revision":
        value.pop("execution_revision")
    elif fault == "old_release":
        value["release_sha"] = wrapper.RELEASE
    save(source, value)
    arguments = dict(
        expected_release="a" * 40,
        revision="execution-r2",
        assembler_sha=wrapper.sha256_file(assembler),
    )
    if fault == "changed_assembler":
        assembler.write_text("changed")
    if fault:
        with pytest.raises(ValueError):
            wrapper.input_bindings(
                root, source, assembler, wrapper.sha256_file(source), 10, **arguments
            )
    else:
        records = wrapper.input_bindings(
            root, source, assembler, wrapper.sha256_file(source), 10, **arguments
        )
        wrapper.verify_bindings(root, records)


def test_cpu_qsub_preserves_explicit_revision_and_disables_optimization(tmp_path):
    script = Path("scripts/operations/week5_admission.qsub").resolve()
    python = tmp_path / ".venv/bin/python3.11"
    python.parent.mkdir(parents=True)
    python.write_text(
        "#!/usr/bin/env bash\n"
        "[[ -z ${PYTHONOPTIMIZE+x} && $PYTHONDONTWRITEBYTECODE == 1 ]] || exit 90\n"
        'printf "%s\\n" "$@"\n'
    )
    python.chmod(0o755)
    arguments = [
        "controller.py",
        "--expected-release",
        "a" * 40,
        "--revision",
        "execution-r2",
    ]
    result = subprocess.run(
        ["bash", str(script), *arguments],
        cwd=tmp_path,
        env=dict(
            os.environ,
            JOB_ID="123",
            TMPDIR=str(tmp_path),
            NSLOTS="4",
            PYTHONOPTIMIZE="1",
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.splitlines() == arguments
    assert "#$ -l no_gpu=TRUE" in script.read_text()
