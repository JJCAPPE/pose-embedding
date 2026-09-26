from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import torch
from torch import nn

import pose_embed.models.motionbert as motionbert
from pose_embed.models.action_head import pool_action_features
from pose_embed.provenance import sha256_file


class TinyEncoder(nn.Module):
    def __init__(self, **_):
        super().__init__()
        self.linear = nn.Linear(3, 4)


@pytest.fixture
def assets(tmp_path, monkeypatch):
    upstream = tmp_path / ".cache/upstreams/MotionBERT"
    config = upstream / "configs/pretrain/MB_pretrain.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "dim_feat: 4\ndim_rep: 4\ndepth: 1\nnum_heads: 1\nmlp_ratio: 2\n"
        "num_joints: 17\nmaxlen: 100\natt_fuse: true\n"
    )
    (upstream / "LICENSE").write_text("synthetic license fixture")
    implementation = upstream / "lib/model/DSTformer.py"
    implementation.parent.mkdir(parents=True)
    implementation.write_text("# synthetic model fixture")
    manifest = tmp_path / "upstreams.toml"
    manifest.write_text(
        'cache_directory = ".cache/upstreams"\n[[upstream]]\nname = "MotionBERT"\n'
        'commit = "pinned"\nlicense = "Apache-2.0"\nlicense_files = ["LICENSE"]\n'
        "reference_only = false\n"
    )
    checkpoint_manifest = tmp_path / "checkpoint.json"
    data_root = tmp_path / "data"
    data_root.mkdir()
    checkpoint = data_root / "encoder.bin"
    state = {
        f"module.{key}": value for key, value in TinyEncoder().state_dict().items()
    }

    def write_checkpoint(values):
        torch.save({"model_pos": values}, checkpoint)
        checkpoint_manifest.write_text(
            json.dumps(
                {
                    "filename": "encoder.bin",
                    "bytes": checkpoint.stat().st_size,
                    "sha256": sha256_file(checkpoint),
                    "architecture_config_id": f"sha256: {sha256_file(config)}",
                }
            )
        )

    write_checkpoint(state)

    def fake_git(arguments, **_):
        if "rev-parse" in arguments:
            return SimpleNamespace(returncode=0, stdout="pinned\n")
        if "status" in arguments:
            return SimpleNamespace(returncode=0, stdout="")
        return SimpleNamespace(
            returncode=0,
            stdout=b"LICENSE\0lib/model/DSTformer.py\0configs/pretrain/MB_pretrain.yaml\0",
        )

    monkeypatch.setattr(motionbert, "_REPOSITORY", tmp_path)
    monkeypatch.setattr(motionbert, "_UPSTREAM_MANIFEST", manifest)
    monkeypatch.setattr(motionbert, "_CHECKPOINT_MANIFEST", checkpoint_manifest)
    monkeypatch.setattr(motionbert.subprocess, "run", fake_git)
    monkeypatch.setattr(motionbert, "_encoder_class", lambda root: TinyEncoder)
    return data_root, state, write_checkpoint, checkpoint


def test_loader_freezes_eval_and_verifies_exact_state(assets) -> None:
    data_root, state, _, _ = assets
    model, metadata = motionbert.load_frozen_encoder(data_root)

    assert not model.training
    assert all(not value.requires_grad for value in model.parameters())
    assert metadata["state_dict_entries"] == 2
    assert metadata["trainable_parameter_count"] == 0
    assert len(metadata["upstream_sha256"]) == 64
    assert len(metadata["license_sha256"]) == 64
    for key, value in model.state_dict().items():
        torch.testing.assert_close(value, state[f"module.{key}"], rtol=0, atol=0)
        assert value.dtype == torch.float32


@pytest.mark.parametrize(
    "mutation", ["missing", "shape", "unexpected", "duplicate", "nonfinite"]
)
def test_loader_rejects_partial_or_invalid_state(assets, mutation) -> None:
    data_root, state, write_checkpoint, _ = assets
    if mutation == "missing":
        del state["module.linear.bias"]
    elif mutation == "shape":
        state["module.linear.bias"] = torch.zeros(5)
    elif mutation == "unexpected":
        state["module.unexpected"] = torch.zeros(1)
    elif mutation == "duplicate":
        state["linear.bias"] = state["module.linear.bias"]
    else:
        state["module.linear.bias"][0] = float("nan")
    write_checkpoint(state)
    with pytest.raises((ValueError, RuntimeError)):
        motionbert.load_frozen_encoder(data_root)


def test_asset_verification_rejects_changed_checkpoint_bytes(assets) -> None:
    data_root, _, _, checkpoint = assets
    payload = bytearray(checkpoint.read_bytes())
    payload[-1] ^= 1
    checkpoint.write_bytes(payload)
    with pytest.raises(ValueError, match="SHA-256 differs"):
        motionbert.verify_motionbert_assets(data_root)


def test_asset_verification_rejects_changed_checkout(assets, monkeypatch) -> None:
    data_root, _, _, _ = assets
    monkeypatch.setattr(
        motionbert.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="wrong\n"),
    )
    with pytest.raises(ValueError, match="checkout is missing or changed"):
        motionbert.verify_motionbert_assets(data_root)


def test_shared_pool_is_pre_projection_and_unnormalized() -> None:
    values = torch.arange(2 * 3 * 4 * 5 * 6, dtype=torch.float32).reshape(2, 3, 4, 5, 6)
    expected = torch.stack(
        [
            torch.stack(
                [values[n, :, :, j, c].mean() for j in range(5) for c in range(6)]
            )
            for n in range(2)
        ]
    )
    torch.testing.assert_close(pool_action_features(values), expected)
    assert not torch.allclose(pool_action_features(values).norm(dim=-1), torch.ones(2))


def test_determinism_setup_rejects_cuda_initialized_without_workspace(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: True)
    with pytest.raises(RuntimeError, match="before initializing CUDA"):
        motionbert.configure_deterministic_inference()


def test_determinism_setup_fixes_backend_flags(monkeypatch) -> None:
    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    calls = []
    monkeypatch.setattr(
        torch, "use_deterministic_algorithms", lambda enabled: calls.append(enabled)
    )
    monkeypatch.setattr(
        torch, "set_float32_matmul_precision", lambda value: calls.append(value)
    )
    monkeypatch.setattr(torch.backends.cudnn, "benchmark", True)
    monkeypatch.setattr(torch.backends.cudnn, "deterministic", False)
    monkeypatch.setattr(torch.backends.cuda.matmul, "allow_tf32", True)
    monkeypatch.setattr(torch.backends.cudnn, "allow_tf32", True)

    motionbert.configure_deterministic_inference()

    assert calls == [True, "highest"]
    assert motionbert.os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
    assert not torch.backends.cudnn.benchmark
    assert torch.backends.cudnn.deterministic
    assert not torch.backends.cuda.matmul.allow_tf32
    assert not torch.backends.cudnn.allow_tf32


def test_determinism_setup_rejects_different_workspace(monkeypatch) -> None:
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    with pytest.raises(ValueError, match=":4096:8"):
        motionbert.configure_deterministic_inference()


def test_inference_environment_cpu_is_serializable_and_avoids_cuda(monkeypatch) -> None:
    def reject_cuda(*args):
        raise AssertionError("CPU evidence must not inspect a CUDA device")

    monkeypatch.setattr(torch.cuda, "get_device_properties", reject_cuda)
    result = motionbert.inference_environment("cpu")
    assert result["device_type"] == "cpu"
    assert result["device_index"] is None
    assert result["cuda_device_uuid"] is None
    assert result["dtype"] == "float32"
    assert result["batch_size"] == 32
    json.dumps(result, allow_nan=False)


def test_inference_environment_records_physical_cuda_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        torch.cuda,
        "get_device_properties",
        lambda device: SimpleNamespace(name="fake GPU", uuid="GPU-test-identity"),
    )
    monkeypatch.setattr(torch.cuda, "current_device", lambda: 1)
    result = motionbert.inference_environment("cuda")
    assert result["device_type"] == "cuda"
    assert result["device_index"] == 1
    assert result["cuda_device_name"] == "fake GPU"
    assert result["cuda_device_uuid"] == "GPU-test-identity"
