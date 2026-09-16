from __future__ import annotations

from pathlib import Path

import torch

from pose_embed.cli import main


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
