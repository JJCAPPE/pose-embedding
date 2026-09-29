"""Exercise real source/cache validation with a tiny synthetic encoder boundary."""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest
import torch

from pose_embed.artifacts import sidecar_path_for, validate_feature_artifact
from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.development import (
    GALLERY_FILENAME,
    REPORT_FILENAME,
    generate_development_episode,
)
from pose_embed.data.inventory import inspect_ntu_aggregate, write_manifest_bundle
from pose_embed.models.motionbert import (
    configure_deterministic_inference,
    inference_environment,
)
from pose_embed.motionbert_features import (
    extract_motionbert_features,
    validate_selected_manifest,
)
from pose_embed.motionbert_inputs import (
    build_motionbert_bindings,
    load_motionbert_inputs,
)
from pose_embed.provenance import sha256_file
from tests.unit.test_ntu_inventory import (
    _annotation,
    _complete_annotations,
    _synthetic_protocol,
    _write_source_files,
)


class _TinyEncoder(torch.nn.Module):
    def get_representation(self, poses: torch.Tensor) -> torch.Tensor:
        assert not self.training
        assert not torch.is_grad_enabled()
        assert poses.dtype == torch.float32
        assert poses.shape[1:] == (100, 17, 3)
        assert len(poses) <= 64
        return (poses[..., :1] + 1).expand(-1, -1, -1, 512)


@dataclass
class _CacheContext:
    protocol: ProtocolConfig
    protocol_path: Path
    root: Path
    bundle: Path
    parity: Path
    code: Path

    @property
    def manifest(self) -> Path:
        return self.bundle.parent / "development-train.jsonl"

    def extract(self, name: str = "cache.npz") -> Path:
        output = self.root / name
        extract_motionbert_features(
            self.root / self.protocol.dataset.source_contract.aggregate_relative_path,
            output,
            protocol_path=self.protocol_path,
            manifest_path=self.manifest,
            manifest_set_path=self.bundle,
            parity_evidence_path=self.parity,
            role="training",
            split="development_train",
            device="cpu",
        )
        return output

    def validate(self, cache: Path) -> None:
        validate_feature_artifact(
            cache, protocol=self.protocol, manifest_path=self.manifest
        )


@pytest.fixture
def cache_context(
    tmp_path: Path, protocol_path: Path, monkeypatch: pytest.MonkeyPatch
) -> _CacheContext:
    annotations = _complete_annotations(protocol_path)
    for action in load_protocol(protocol_path).dataset.development_validation_actions:
        annotations.append(_annotation(f"S003C001P010R001A{action:03d}"))
    metadata = _write_source_files(tmp_path, annotations)
    protocol = _synthetic_protocol(protocol_path, metadata)
    inventory = inspect_ntu_aggregate(tmp_path, metadata, protocol)
    bundle_dir = tmp_path / "release"
    write_manifest_bundle(inventory, protocol, bundle_dir)
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    from pose_embed.dataset_seal import register_artifact_roots

    register_artifact_roots([])
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.load_protocol", lambda _: protocol
    )
    monkeypatch.setattr("pose_embed.data.development.load_protocol", lambda _: protocol)
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.require_clean_repository", lambda: "a" * 40
    )
    monkeypatch.setattr("pose_embed.provenance._git_sha", lambda _: "a" * 40)
    monkeypatch.setattr("pose_embed.provenance._git_dirty", lambda _: False)
    repository = tmp_path / "code"
    repository.mkdir()
    code = repository / "extractor.py"
    code.write_text("# immutable synthetic encoder test boundary\n")
    (repository / "uv.lock").write_text("synthetic locked dependencies\n")
    for module in ("motionbert_inputs", "motionbert_features"):
        monkeypatch.setattr(f"pose_embed.{module}.REPOSITORY", repository)
        monkeypatch.setattr(f"pose_embed.{module}.MOTIONBERT_CODE_PATHS", (code.name,))
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"synthetic checkpoint")
    config = tmp_path / "encoder.yaml"
    config.write_text("synthetic: true\n")
    assets = {
        "checkpoint_path": str(checkpoint),
        "config_path": str(config),
        "upstream_sha256": "b" * 64,
        "checkpoint_sha256": sha256_file(checkpoint),
        "config_sha256": sha256_file(config),
        "license_sha256": "c" * 64,
        "upstream_commit": "d" * 40,
    }
    monkeypatch.setattr(
        "pose_embed.models.motionbert.verify_motionbert_assets", lambda _: assets
    )
    monkeypatch.setattr(
        "pose_embed.models.motionbert.load_frozen_encoder",
        lambda _, device: (_TinyEncoder().eval(), assets),
    )

    # Numerical parity is tested in its own suite. Here its boundary requires
    # an immutable passing report with every actual source/code/asset binding.
    configure_deterministic_inference()
    environment = inference_environment("cpu")

    def validate_parity(path: Path, bindings: dict[str, str]) -> dict[str, Any]:
        report = json.loads(path.read_text())
        if report != {"passed": True, "bindings": bindings, "environment": environment}:
            raise ValueError("synthetic parity boundary rejected its report")
        return report

    parity_module = ModuleType("pose_embed.motionbert_parity")
    parity_module.validate_parity_report = validate_parity  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pose_embed.motionbert_parity", parity_module)
    bundle = bundle_dir / "manifest-set.json"
    inputs = load_motionbert_inputs(protocol_path, bundle)
    parity = tmp_path / "parity.json"
    parity.write_text(
        json.dumps(
            {
                "passed": True,
                "bindings": build_motionbert_bindings(inputs, assets),
                "environment": environment,
            }
        )
    )
    return _CacheContext(protocol, protocol_path, tmp_path, bundle, parity, code)


def _change_sidecar(cache: Path, edit: Any) -> None:
    path = sidecar_path_for(cache)
    payload = json.loads(path.read_text())
    edit(payload)
    path.write_text(json.dumps(payload))


def test_motionbert_extraction_roundtrip_is_deterministic_and_unnormalized(
    cache_context: _CacheContext,
) -> None:
    first = cache_context.extract()
    second = cache_context.extract("repeat.npz")
    cache_context.validate(first)
    cache_context.validate(second)
    assert sha256_file(first) == sha256_file(second)
    with np.load(first, allow_pickle=False) as archive:
        assert archive["features"].shape == (80, 8704)
        assert archive["features"].dtype == np.float32
        np.testing.assert_array_equal(archive["features"], np.ones((80, 8704)))
        assert np.linalg.norm(archive["features"][0]) > 1
    with pytest.raises(ValueError, match="overwrite"):
        cache_context.extract()


def test_extraction_does_not_authorize_a_cache_that_fails_final_validation(
    cache_context: _CacheContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(*args: Any, **kwargs: Any) -> None:
        raise ValueError("prepublication validation failed")

    monkeypatch.setattr(
        "pose_embed.motionbert_features.validate_motionbert_cache", reject
    )
    with pytest.raises(ValueError, match="prepublication"):
        cache_context.extract()
    cache = cache_context.root / "cache.npz"
    assert cache.is_file()
    assert not sidecar_path_for(cache).exists()
    with pytest.raises(ValueError, match="overwrite"):
        cache_context.extract()


@pytest.mark.parametrize(
    "binding",
    [
        "source_inventory_sha256",
        "code_sha256",
        "checkpoint_sha256",
        "dependency_lock_sha256",
    ],
)
def test_motionbert_rejects_missing_or_changed_bindings(
    cache_context: _CacheContext, binding: str
) -> None:
    cache = cache_context.extract()
    _change_sidecar(
        cache, lambda row: row["provenance"]["motionbert"]["bindings"].pop(binding)
    )
    with pytest.raises(ValueError, match="bindings changed"):
        cache_context.validate(cache)


@pytest.mark.parametrize(
    "input_name",
    [
        "parity.json",
        "extractor.py",
        "source-inventory.jsonl",
        "ntu120_hrnet.pkl",
        "missing.txt",
    ],
)
def test_motionbert_rejects_missing_provenance_inputs(
    cache_context: _CacheContext, input_name: str
) -> None:
    cache = cache_context.extract()

    def remove_input(row: dict[str, Any]) -> None:
        inputs = row["provenance"]["inputs"]
        key = next(path for path in inputs if Path(path).name == input_name)
        del inputs[key]

    _change_sidecar(cache, remove_input)
    with pytest.raises(
        ValueError, match="provenance input changed|physical source hash is missing"
    ):
        cache_context.validate(cache)


@pytest.mark.parametrize(
    "changed", ["code", "parity", "inventory", "npz", "dirty", "unbound_sidecar"]
)
def test_motionbert_rejects_tampered_evidence(
    cache_context: _CacheContext, changed: str
) -> None:
    cache = cache_context.extract()
    if changed == "code":
        cache_context.code.write_text("# changed implementation\n")
    elif changed == "parity":
        cache_context.parity.write_text("{}")
    elif changed == "inventory":
        inventory = cache_context.bundle.parent / "source-inventory.jsonl"
        inventory.write_text(inventory.read_text() + "\n")
    elif changed == "npz":
        with cache.open("ab") as stream:
            stream.write(b"tampered")
    elif changed == "dirty":
        _change_sidecar(cache, lambda row: row["provenance"].update(git_dirty=True))
    else:
        _change_sidecar(cache, lambda row: row["provenance"].pop("motionbert"))
    with pytest.raises(ValueError):
        cache_context.validate(cache)


@pytest.mark.parametrize("git_sha", [None, 123, "not-a-commit", "A" * 40, "a" * 39])
def test_motionbert_rejects_invalid_commit_provenance(
    cache_context: _CacheContext, git_sha: object
) -> None:
    cache = cache_context.extract()
    _change_sidecar(cache, lambda row: row["provenance"].update(git_sha=git_sha))
    with pytest.raises(ValueError, match="clean-code provenance"):
        cache_context.validate(cache)


@pytest.mark.parametrize(
    "configuration",
    [None, [], {"batch_size": 64}, {"dtype": "float16"}, {"condition": "jitter:0.01"}],
)
def test_motionbert_rejects_changed_extraction_configuration(
    cache_context: _CacheContext, configuration: object
) -> None:
    cache = cache_context.extract()

    def replace_configuration(row: dict[str, Any]) -> None:
        if isinstance(configuration, dict):
            row["provenance"]["configuration"].update(configuration)
        else:
            row["provenance"]["configuration"] = configuration

    _change_sidecar(cache, replace_configuration)
    with pytest.raises(ValueError, match="configuration mismatch"):
        cache_context.validate(cache)


@pytest.mark.parametrize("data_root", [None, "relative", "/wrong-data-root"])
def test_motionbert_cache_rejects_wrong_data_environment(
    cache_context: _CacheContext, monkeypatch: pytest.MonkeyPatch, data_root: str | None
) -> None:
    cache = cache_context.extract()
    if data_root is None:
        monkeypatch.delenv("POSE_EMBED_DATA_ROOT")
    else:
        monkeypatch.setenv("POSE_EMBED_DATA_ROOT", data_root)
    with pytest.raises(ValueError):
        cache_context.validate(cache)


@pytest.mark.parametrize("artifact_root", [None, "relative", "/wrong-artifact-root"])
def test_motionbert_cache_rejects_wrong_artifact_environment(
    cache_context: _CacheContext,
    monkeypatch: pytest.MonkeyPatch,
    artifact_root: str | None,
) -> None:
    cache = cache_context.extract()
    if artifact_root is None:
        monkeypatch.delenv("POSE_EMBED_ARTIFACT_ROOT")
    else:
        monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", artifact_root)
    with pytest.raises(ValueError, match="POSE_EMBED_ARTIFACT_ROOT"):
        cache_context.validate(cache)


@pytest.mark.parametrize(
    "target", ["artifact", "manifest_set", "parity_report", "development_episode"]
)
def test_motionbert_evidence_must_remain_inside_artifact_root(
    cache_context: _CacheContext, target: str
) -> None:
    cache = cache_context.extract()
    outside = cache_context.root.parent / (cache_context.root.name + "-outside")
    outside.mkdir()
    if target == "artifact":
        moved = outside / cache.name
        shutil.copyfile(cache, moved)
        shutil.copyfile(sidecar_path_for(cache), sidecar_path_for(moved))
        cache = moved
    else:
        paths = {
            "manifest_set": cache_context.bundle,
            "parity_report": cache_context.parity,
        }
        if target in paths:
            source = paths[target]
            destination = outside / source.name
            shutil.copyfile(source, destination)
        else:
            destination = outside / REPORT_FILENAME
            destination.write_text("{}")
        _change_sidecar(
            cache,
            lambda row: row["provenance"]["motionbert"]["paths"].update(
                {target: str(destination)}
            ),
        )
    with pytest.raises(ValueError, match="inside POSE_EMBED_ARTIFACT_ROOT"):
        cache_context.validate(cache)


def test_development_extraction_requires_report_from_its_verified_bundle(
    cache_context: _CacheContext,
) -> None:
    manifest = cache_context.bundle.parent / "development-validation.jsonl"
    episode_dir = cache_context.root / "episode"
    generate_development_episode(manifest, episode_dir, cache_context.protocol_path)
    inputs = load_motionbert_inputs(cache_context.protocol_path, cache_context.bundle)
    with pytest.raises(ValueError):
        validate_selected_manifest(
            inputs.manifests,
            cache_context.protocol,
            episode_dir / GALLERY_FILENAME,
            role="gallery_clean",
            split="development_validation",
            episode_path=episode_dir / REPORT_FILENAME,
            source_inventory_sha256="0" * 64,
        )


def test_development_cache_requires_its_unchanged_episode(
    cache_context: _CacheContext,
) -> None:
    source = cache_context.bundle.parent / "development-validation.jsonl"
    episode_dir = cache_context.root / "episode"
    generate_development_episode(source, episode_dir, cache_context.protocol_path)
    manifest = episode_dir / GALLERY_FILENAME
    output = cache_context.root / "gallery.npz"
    extract_motionbert_features(
        cache_context.root / "ntu120_hrnet.pkl",
        output,
        protocol_path=cache_context.protocol_path,
        manifest_path=manifest,
        manifest_set_path=cache_context.bundle,
        parity_evidence_path=cache_context.parity,
        role="gallery_clean",
        split="development_validation",
        device="cpu",
        episode_path=episode_dir / REPORT_FILENAME,
    )
    sidecar = validate_feature_artifact(
        output, protocol=cache_context.protocol, manifest_path=manifest
    )
    assert sidecar.shape == (20, 8704)
    _change_sidecar(
        output,
        lambda row: row["provenance"]["motionbert"]["paths"].pop("development_episode"),
    )
    with pytest.raises(ValueError, match="fixed episode report"):
        validate_feature_artifact(
            output, protocol=cache_context.protocol, manifest_path=manifest
        )


def test_extraction_rejects_parity_from_another_runtime(
    cache_context: _CacheContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = inference_environment("cpu")
    monkeypatch.setattr(
        "pose_embed.models.motionbert.inference_environment",
        lambda _: original | {"torch": "different-version"},
    )
    with pytest.raises(ValueError, match="environment differs"):
        cache_context.extract()
    assert not (cache_context.root / "cache.npz").exists()


@pytest.mark.parametrize(
    "role,split",
    [("gallery_clean", "development_train"), ("training", "development_validation")],
)
def test_motionbert_extraction_rejects_wrong_roles(
    cache_context: _CacheContext, role: str, split: str
) -> None:
    with pytest.raises(ValueError, match="clean auxiliary"):
        extract_motionbert_features(
            cache_context.root / "ntu120_hrnet.pkl",
            cache_context.root / "wrong-role.npz",
            protocol_path=cache_context.protocol_path,
            manifest_path=cache_context.manifest,
            manifest_set_path=cache_context.bundle,
            parity_evidence_path=cache_context.parity,
            role=role,
            split=split,
            device="cpu",
        )
    assert not (cache_context.root / "wrong-role.npz").exists()
