"""The development configuration cannot silently narrow or reopen the suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pose_embed.benchmark.config import (
    METHOD_IDS,
    REPOSITORY_ROOT,
    BenchmarkConfig,
    MethodRegistry,
    benchmark_digest,
    load_benchmark,
    load_methods,
)


def test_complete_suite_and_dimension_matched_rows() -> None:
    config = load_benchmark()
    methods = load_methods()
    assert len(methods) == 26
    assert set(config.final_methods) == set(METHOD_IDS) == set(methods)
    assert config.priority_methods == ("contrastive", "contextual")
    assert config.training.physical_batch_size == 32
    assert methods["contextual_1536"].embedding_dimension == 1536
    assert methods["proxy_anchor_avsl"].embedding_dimension == 1536
    assert methods["proxy_nca_pp"].status == "blocked"


@pytest.mark.parametrize(
    "change",
    [
        {"final_methods": ["contrastive", "contextual"]},
        {"phase": "final"},
        {"selection_metric": "novel_r_at_1"},
        {"input_protocol": "../protocol.yaml"},
        {"priority_methods": ["contextual"]},
        {"input_protocol_sha256": "0" * 64},
        {"unexpected": True},
    ],
)
def test_invalid_contract_is_rejected(change: dict[str, object]) -> None:
    values = load_benchmark().model_dump()
    with pytest.raises(ValidationError):
        BenchmarkConfig.model_validate(values | change)


@pytest.mark.parametrize(
    "change",
    [
        {"seeds": [7, 17, 29]},
        {"seeds": [7, 17, 29, 43, 59, 59]},
        {"samples_per_class": 3},
        {"classes_per_batch": True},
        {"validation_every": 1001},
        {"learning_rate": float("nan")},
    ],
)
def test_invalid_training_is_rejected(change: dict[str, object]) -> None:
    values = load_benchmark().model_dump()
    values["training"].update(change)
    with pytest.raises(ValidationError):
        BenchmarkConfig.model_validate(values)


def test_registry_cannot_omit_or_duplicate_a_required_method() -> None:
    path = REPOSITORY_ROOT / "configs/benchmark-methods.v2.json"
    values = json.loads(path.read_text())
    values["methods"][-1] = values["methods"][0]
    with pytest.raises(ValidationError, match="26 identities"):
        MethodRegistry.model_validate(values)


def test_blocked_method_requires_an_explanation() -> None:
    path = REPOSITORY_ROOT / "configs/benchmark-methods.v2.json"
    values = json.loads(path.read_text())
    blocked = next(row for row in values["methods"] if row["status"] == "blocked")
    blocked["blocker"] = None
    with pytest.raises(ValidationError, match="require a blocker"):
        MethodRegistry.model_validate(values)


def test_hash_binds_all_settings_and_survives_yaml_formatting(tmp_path: Path) -> None:
    config = load_benchmark()
    path = tmp_path / "benchmark.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json"), sort_keys=True))
    assert benchmark_digest(load_benchmark(path)) == benchmark_digest(config)
    values = config.model_dump()
    values["training"]["encoder_mode"] = "finetune"
    assert benchmark_digest(BenchmarkConfig.model_validate(values)) != benchmark_digest(
        config
    )
    values["methods_sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(values))
    with pytest.raises(ValueError, match="registry hash"):
        load_benchmark(path)


def test_contextual_neighborhood_cannot_drift_from_physical_batch(
    tmp_path: Path,
) -> None:
    values = load_benchmark().model_dump(mode="json")
    values["training"]["samples_per_class"] = 6
    path = tmp_path / "benchmark.yaml"
    path.write_text(yaml.safe_dump(values))
    with pytest.raises(ValueError, match="neighborhood"):
        load_benchmark(path)
