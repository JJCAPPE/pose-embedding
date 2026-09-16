from __future__ import annotations

from pathlib import Path

import torch

import pose_embed.gpu_profile as gpu_profile
from pose_embed.cli import main
from pose_embed.gpu_profile import _profile_contract, _profile_decision


def test_gpu_profile_contract_matches_locked_protocol() -> None:
    contract = _profile_contract()

    assert contract["batch_sizes"] == (32, 64)
    assert contract["people"] == 2
    assert contract["frames"] == 100
    assert contract["joints"] == 17
    assert contract["channels"] == 3
    assert contract["representation_dimension"] == 512
    assert contract["protocol_sha256"] == (
        "12cf4d9a322f5bd5ea76fb2d9ffc070a6a2681fe8474a05cff1f62b6e43368e2"
    )


def test_gpu_profile_decision_requires_complete_evidence() -> None:
    batches = [{"status": "success"}, {"status": "success"}]

    decision = _profile_decision(batches, evidence_complete=False)

    assert decision["status"] == "profile_evidence_incomplete"
    assert decision["physical_batch_size"] == 32
    assert decision["week_1_gate_supported"] is False


def test_gpu_profile_decision_retains_32_after_encoder_profile() -> None:
    batches = [{"status": "success"}, {"status": "success"}]

    decision = _profile_decision(batches, evidence_complete=True)

    assert decision["status"] == (
        "retain_physical_batch_32_pending_core_method_profile"
    )
    assert decision["physical_batch_size"] == 32
    assert decision["week_1_gate_supported"] is True


def test_scheduler_profile_does_not_require_an_sge_project(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def record_command(*arguments: str) -> dict[str, object]:
        calls.append(arguments)
        return {"returncode": 0, "stdout": "evidence", "stderr": ""}

    monkeypatch.setenv("JOB_ID", "123")
    monkeypatch.setenv("QUEUE", "v100")
    monkeypatch.delenv("PROJECT", raising=False)
    monkeypatch.setattr(gpu_profile, "_command", record_command)

    profile = gpu_profile._scheduler_profile()

    assert "project" not in profile
    assert not any(arguments[:2] == ("qconf", "-sprj") for arguments in calls)


def test_gpu_job_exports_only_required_profile_roots() -> None:
    job_script = (
        Path(__file__).resolve().parents[2] / "scripts" / "profile_motionbert_gpu.qsub"
    ).read_text(encoding="utf-8")

    assert "#$ -v POSE_EMBED_DATA_ROOT,POSE_EMBED_ARTIFACT_ROOT" in job_script
    assert "#$ -V" not in job_script


def test_gpu_profile_refuses_a_non_cuda_host(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    artifact_root = tmp_path / "artifacts"
    output = artifact_root / "profiles" / "motionbert.json"
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    status = main(["profile", "gpu", "--output", str(output)])

    assert status == 2
    assert "CUDA GPU is required" in capsys.readouterr().err
    assert not output.exists()


def test_gpu_profile_requires_one_scheduler_assigned_device(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setenv("JOB_ID", "123")
    monkeypatch.setenv("QUEUE", "v100")
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)

    status = main(["profile", "gpu", "--output", "unused.json"])

    assert status == 2
    assert "exactly one scheduler-assigned GPU" in capsys.readouterr().err
