"""Software-only external controller checks; never access SCC or licensed roots."""

import ast
import importlib.util
import json
import os
import subprocess
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
@pytest.mark.parametrize("revision", ["execution-r1", "execution-r2"])
def test_controller_holds_locks_retains_failures_and_keeps_parent_cuda_free(
    controller, tmp_path, monkeypatch, fault, revision
):
    root = tmp_path.resolve()
    release = controller.RELEASE if revision == "execution-r1" else "2" * 40
    diag = diagnostic(controller, root)
    for name, value in {
        "JOB_ID": "123",
        "NSLOTS": "4",
        "TMPDIR": str(root),
        "POSE_EMBED_MANIFEST_SET": str(
            root / "study-v3/revisions" / revision / "manifests/manifest-set.json"
        ),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(controller, "canonical_artifact_root", lambda: root)
    monkeypatch.setattr(controller, "require_clean_repository", lambda: release)
    if revision == "execution-r2":
        sources = controller.execution_binding(release, revision)
        save(
            diag,
            controller.read(diag)
            | {
                "source_release": release,
                "execution_revision": revision,
                "execution_sources_sha256": sources,
                "script_sha256": sources[controller.EXECUTION_SOURCES[1]],
            },
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
            output = Path(command[command.index("--gpu-preflight-output") + 1])
            save(
                output,
                {
                    "status": "failed" if fault == "probe_failed" else "passed",
                    "controller_sha256": controller.sha256_file(controller.__file__),
                    "source_release": release,
                    "execution_revision": revision,
                    "free_bytes": 32 * 2**30,
                    "total_bytes": 48 * 2**30,
                },
            )
            return
        if command[0] == "bash":
            assert command == ["bash", "scripts/study_v3.qsub", "caches"]
            assert environment["POSE_EMBED_V3_ATTEMPT"].endswith(attempt.name)
            assert (
                str(Path("study-v3/revisions") / revision)
                in environment["POSE_EMBED_V3_ATTEMPT"]
            )
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
            "--expected-release",
            release,
            "--revision",
            revision,
        ],
    )
    if fault:
        with pytest.raises((ValueError, RuntimeError)):
            controller.main()
    else:
        controller.main()
    attempt = next((root / "study-v3/operations").glob("*-123-caches"))
    record = controller.read(attempt / "attempt.json")
    assert record["release_sha"] == release and record["execution_revision"] == revision
    assert record["execution_sources_sha256"] == controller.execution_binding(
        release, revision
    )
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


@pytest.mark.parametrize(
    "fault", [None, "old_release", "old_revision", "helper", "script"]
)
def test_successor_requires_fresh_diagnostic_for_its_exact_release(
    controller, tmp_path, monkeypatch, fault
):
    root, release = tmp_path.resolve(), "2" * 40
    monkeypatch.setattr(controller, "require_clean_repository", lambda: release)
    sources = controller.execution_binding(release, "execution-r2")
    path = diagnostic(controller, root)
    record = controller.read(path) | {
        "source_release": release,
        "execution_revision": "execution-r2",
        "execution_sources_sha256": sources.copy(),
        "script_sha256": sources[controller.EXECUTION_SOURCES[1]],
    }
    if fault == "old_release":
        record["source_release"] = controller.RELEASE
    if fault == "old_revision":
        record["execution_revision"] = "execution-r1"
    if fault == "helper":
        record["execution_sources_sha256"]["scripts/run_v3_execution.py"] = "a" * 64
    if fault == "script":
        record["script_sha256"] = controller.DIAGNOSTIC_SHA256
    save(path, record)
    kwargs = {
        "expected_release": release,
        "revision": "execution-r2",
        "source_hashes": sources,
    }
    if fault:
        with pytest.raises(ValueError, match="diagnostic has not passed"):
            controller.validate_diagnostic(
                root, path, controller.sha256_file(path), **kwargs
            )
    else:
        controller.validate_diagnostic(
            root, path, controller.sha256_file(path), **kwargs
        )


@pytest.mark.parametrize(
    "release,revision",
    [
        ("short", "execution-r2"),
        ("2" * 40, "execution-r1"),
        ("731938a157be575ee433d6939876f8ca0b95e459", "execution-r2"),
    ],
)
def test_release_revision_pair_cannot_silently_relabel_historical_inputs(
    controller, monkeypatch, release, revision
):
    monkeypatch.setattr(controller, "require_clean_repository", lambda: release)
    with pytest.raises(ValueError, match="clean full release"):
        controller.execution_binding(release, revision)


def test_successor_controller_must_match_tracked_bytes(controller, monkeypatch):
    release = "2" * 40
    monkeypatch.setattr(controller, "require_clean_repository", lambda: release)
    original = controller.sha256_file
    monkeypatch.setattr(
        controller,
        "sha256_file",
        lambda path: "a" * 64 if path == controller.__file__ else original(path),
    )
    with pytest.raises(ValueError, match="tracked release"):
        controller.execution_binding(release, "execution-r2")


@pytest.mark.parametrize(
    "explicit,wrong", [(False, False), (True, False), (True, True)]
)
def test_gpu_qsub_binds_expected_release_before_environment_setup(
    tmp_path, explicit, wrong
):
    wrapper = Path.cwd() / "scripts/operations/week5_gpu.qsub"
    binary = tmp_path / "bin"
    binary.mkdir()
    python = tmp_path / ".venv/bin/python3.11"
    python.parent.mkdir(parents=True)
    files = {
        binary / "git": (
            '#!/bin/sh\nif [ "$1" = rev-parse ]; then '
            'printf "%s\\n" "$FIXTURE_RELEASE"; fi\n'
        ),
        binary / "uv": '#!/bin/sh\ntouch "$FIXTURE_SETUP"\n',
        python: '#!/bin/sh\nprintf "%s\\n" "$@"\n',
    }
    for path, text in files.items():
        path.write_text(text)
        path.chmod(0o755)
    release = "2" * 40 if explicit else "731938a157be575ee433d6939876f8ca0b95e459"
    environment = os.environ | {
        "PATH": str(binary) + os.pathsep + os.environ["PATH"],
        "FIXTURE_RELEASE": "3" * 40 if wrong else release,
        "FIXTURE_SETUP": str(tmp_path / "setup"),
        "JOB_ID": "123",
        "NSLOTS": "4",
        "TMPDIR": str(tmp_path),
        "POSE_EMBED_DATA_ROOT": str(tmp_path),
        "POSE_EMBED_ARTIFACT_ROOT": str(tmp_path),
        "POSE_EMBED_MANIFEST_SET": str(tmp_path / "fixture.json"),
    }
    arguments = (["--expected-release", release] if explicit else []) + [
        "controller.py",
        "caches",
    ]
    result = subprocess.run(
        ["bash", str(wrapper), *arguments],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if wrong:
        assert result.returncode == 2 and not (tmp_path / "setup").exists()
    else:
        assert result.returncode == 0 and (tmp_path / "setup").exists()
        assert result.stdout.splitlines() == ["controller.py", "caches"] + (
            ["--expected-release", release] if explicit else []
        )
