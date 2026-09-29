from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


def _heredoc(script: Path, marker: str) -> str:
    match = re.search(
        r"<<'" + marker + r"'\n(.*?)\n" + marker + r"\n", script.read_text(), re.DOTALL
    )
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize(
    "script,args", [("prepare_v3.qsub", []), ("study_v3.qsub", ["caches"])]
)
def test_v3_launchers_refuse_login_node_execution(
    repository_root, tmp_path, script, args
):
    environment = {key: value for key, value in os.environ.items() if key != "JOB_ID"}
    environment.update(
        {
            "POSE_EMBED_DATA_ROOT": str(tmp_path / "data"),
            "POSE_EMBED_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
            "POSE_EMBED_MANIFEST_SET": str(tmp_path / "manifests.json"),
        }
    )
    result = subprocess.run(
        ["bash", str(repository_root / "scripts" / script), *args],
        env=environment,
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode != 0
    assert "Submit through Grid Engine" in result.stderr
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "args", [["selection"], ["pilot", "multi_similarity"], ["caches", "extra"]]
)
def test_v3_launchers_reject_unsupported_stages_before_preflight(
    repository_root, tmp_path, args
):
    result = subprocess.run(
        ["bash", str(repository_root / "scripts/study_v3.qsub"), *args],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert not list(tmp_path.iterdir())


def _executable(path: Path, script: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + script)
    path.chmod(0o755)


def test_pilot_launcher_runs_fixture_then_existing_config_without_overwrite(
    repository_root, tmp_path
):
    """Run the shell control flow with fake infrastructure, never Python/CUDA."""
    commands = tmp_path / "commands.txt"
    tools = tmp_path / "bin"
    common = 'printf "%s\\n" "$(basename "$0") $*" >> "$LAUNCH_TEST_COMMANDS"\n'
    _executable(
        tools / "git", 'if [[ "$1" == rev-parse ]]; then printf "test-release\\n"; fi\n'
    )
    _executable(tools / "date", 'printf "20261005T000000Z\\n"\n')
    _executable(tools / "uv", common)
    _executable(tools / "nvidia-smi", 'printf "NVIDIA L40S\\n"\n')
    _executable(
        tools / "pquota", 'printf "%s 1000 0 700 0\\n" "$POSE_EMBED_ARTIFACT_ROOT"\n'
    )
    _executable(
        tmp_path / ".venv/bin/python",
        common + 'if [[ "$1" == - ]]; then cat > /dev/null; fi\n',
    )
    _executable(
        tmp_path / ".venv/bin/pose-embed",
        common + 'while [[ $# -gt 1 ]]; do if [[ "$1" == --config ]]; then '
        'test -f "$2"; fi; shift; done\n',
    )
    (tmp_path / "configs").symlink_to(
        repository_root / "configs", target_is_directory=True
    )
    artifacts = tmp_path / "artifacts"
    lock = artifacts / "study-v3/locks/protocol.v3.json"
    lock.parent.mkdir(parents=True)
    lock.write_text("{}")
    environment = {
        **os.environ,
        "PATH": str(tools) + os.pathsep + os.environ["PATH"],
        "JOB_ID": "12345",
        "TMPDIR": str(tmp_path),
        "NSLOTS": "4",
        "POSE_EMBED_DATA_ROOT": str(tmp_path / "data"),
        "POSE_EMBED_ARTIFACT_ROOT": str(artifacts),
        "POSE_EMBED_MANIFEST_SET": str(tmp_path / "manifests/manifest-set.json"),
        "POSE_EMBED_V3_CACHES": str(tmp_path / "caches"),
        "LAUNCH_TEST_COMMANDS": str(commands),
    }
    invocation = [
        "bash",
        str(repository_root / "scripts/study_v3.qsub"),
        "pilot",
        "contextual",
    ]
    result = subprocess.run(
        invocation,
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    lines = commands.read_text().splitlines()
    fixture = next(
        index for index, line in enumerate(lines) if "learnable-fixture.json" in line
    )
    train = next(
        index
        for index, line in enumerate(lines)
        if "train --stage engineering_pilot" in line
    )
    assert fixture < train
    assert "configs/experiments/v3/contextual-lr3e-4-seed7.yaml" in lines[train]
    exit_record = (
        artifacts / "study-v3/attempts/20261005T000000Z-12345/scheduler-exit.txt"
    )
    assert exit_record.read_text() == "exit_status=0\n"
    result = subprocess.run(
        invocation,
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert exit_record.read_text() == "exit_status=0\n"


@pytest.mark.parametrize(
    "filename,marker", [("prepare_v3.qsub", "PYQUOTA"), ("study_v3.qsub", "PY")]
)
def test_launcher_quota_preflight_uses_real_parser_and_reserve(
    repository_root, tmp_path, monkeypatch, filename, marker
):
    import pose_embed.config
    import pose_embed.dataset_seal
    import pose_embed.models.motionbert
    import pose_embed.protocol_v3

    quota = tmp_path / "quota.txt"
    code = _heredoc(repository_root / "scripts" / filename, marker)
    monkeypatch.setattr(sys, "argv", ["-", str(quota)])
    monkeypatch.setattr(
        pose_embed.dataset_seal, "canonical_artifact_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        pose_embed.dataset_seal, "require_dataset_unopened", lambda **kwargs: None
    )
    monkeypatch.setattr(pose_embed.config, "load_protocol", lambda _: None)
    monkeypatch.setattr(pose_embed.protocol_v3, "require_v3_design", lambda _: None)
    monkeypatch.setattr(
        pose_embed.models.motionbert, "configure_deterministic_inference", lambda: None
    )
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda _: "NVIDIA L40S")
    monkeypatch.setattr(shutil, "disk_usage", lambda _: SimpleNamespace(free=10**12))
    quota.write_text(f"{tmp_path} 1000 0 700 0\n")
    exec(compile(code, str(repository_root / "scripts" / filename), "exec"), {})
    quota.write_text(f"{tmp_path} 1000 0 800 0\n")
    with pytest.raises(ValueError, match="storage reserve"):
        exec(compile(code, str(repository_root / "scripts" / filename), "exec"), {})
