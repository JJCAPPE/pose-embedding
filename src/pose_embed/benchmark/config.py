"""Versioned development benchmark and complete method coverage contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
INPUT_PROTOCOL_SHA256 = (
    "c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f"
)
METHOD_IDS = (
    "contrastive",
    "contextual",
    "triplet",
    "multi_similarity",
    "multi_similarity_miner",
    "proxy_anchor",
    "proxy_nca",
    "roadmap",
    "nt_xent",
    "fast_ap",
    "smooth_ap",
    "normalized_softmax",
    "proxy_nca_pp",
    "supcon",
    "drml",
    "diml",
    "diva",
    "ibc",
    "s2sd",
    "proxy_nca_metrix",
    "proxy_anchor_metrix",
    "multi_similarity_metrix",
    "hist",
    "mhgl",
    "proxy_anchor_avsl",
    "contextual_1536",
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class MethodSpec(StrictModel):
    method_id: str
    name: str = Field(min_length=1)
    family: Literal["embedding_loss", "architecture"]
    embedding_dimension: StrictInt = Field(gt=0)
    source_url: str = Field(pattern=r"^https://")
    implementation: str = Field(min_length=1)
    status: Literal["implemented", "blocked"]
    blocker: str | None
    parameters: dict[str, str | float | int | bool | list[StrictInt]]

    @model_validator(mode="after")
    def status_has_evidence(self) -> MethodSpec:
        if self.method_id not in METHOD_IDS:
            raise ValueError("unknown method identity")
        if (self.status == "blocked") != bool(self.blocker):
            raise ValueError(
                "blocked methods require a blocker; implemented ones cannot"
            )
        expected = (
            1536 if self.method_id in {"proxy_anchor_avsl", "contextual_1536"} else 512
        )
        if self.embedding_dimension != expected:
            raise ValueError("method embedding dimension differs from its comparison")
        return self


class MethodRegistry(StrictModel):
    schema_version: Literal[2]
    protocol_id: Literal["motion-retrieval-v2"]
    methods: tuple[MethodSpec, ...]

    @model_validator(mode="after")
    def roster_is_complete(self) -> MethodRegistry:
        ids = tuple(method.method_id for method in self.methods)
        if len(ids) != len(set(ids)) or set(ids) != set(METHOD_IDS):
            raise ValueError(
                "method registry must contain all 26 identities exactly once"
            )
        return self


class BenchmarkTraining(StrictModel):
    seeds: tuple[StrictInt, ...]
    classes_per_batch: StrictInt = Field(gt=1)
    samples_per_class: StrictInt = Field(ge=4)
    embedding_dimension: Literal[512]
    optimizer: Literal["adamw"] = "adamw"
    encoder_mode: Literal["frozen", "finetune"] = "frozen"
    learning_rate: float = Field(gt=0)
    weight_decay: float = Field(ge=0)
    steps: StrictInt = Field(gt=0)
    validation_every: StrictInt = Field(gt=0)

    @property
    def physical_batch_size(self) -> int:
        return self.classes_per_batch * self.samples_per_class

    @model_validator(mode="after")
    def paired_training_is_valid(self) -> BenchmarkTraining:
        if len(self.seeds) != 6 or len(set(self.seeds)) != 6:
            raise ValueError("v2 requires six distinct paired seeds")
        if any(seed < 0 for seed in self.seeds):
            raise ValueError("seeds must be nonnegative")
        if self.samples_per_class % 2:
            raise ValueError("contextual batches require an even samples_per_class")
        if self.validation_every > self.steps:
            raise ValueError("validation interval must not exceed training steps")
        return self


class BenchmarkMetrics(StrictModel):
    recall_k: tuple[StrictInt, ...]

    @model_validator(mode="after")
    def ranks_are_ordered(self) -> BenchmarkMetrics:
        if (
            not self.recall_k
            or self.recall_k[0] != 1
            or tuple(sorted(set(self.recall_k))) != self.recall_k
        ):
            raise ValueError(
                "recall ranks must be sorted, unique, positive, and include 1"
            )
        return self


class BenchmarkConfig(StrictModel):
    schema_version: Literal[2]
    protocol_id: Literal["motion-retrieval-v2"]
    phase: Literal["development"]
    input_protocol: str
    input_protocol_sha256: Literal[INPUT_PROTOCOL_SHA256]
    methods_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    priority_methods: tuple[str, ...]
    final_methods: tuple[str, ...]
    training: BenchmarkTraining
    metrics: BenchmarkMetrics
    selection_metric: Literal["r_at_1"]

    @model_validator(mode="after")
    def coverage_and_input_are_explicit(self) -> BenchmarkConfig:
        path = PurePosixPath(self.input_protocol)
        if path.is_absolute() or ".." in path.parts or str(path) != self.input_protocol:
            raise ValueError(
                "input_protocol must be a normalized repository-relative path"
            )
        if self.priority_methods != ("contrastive", "contextual"):
            raise ValueError("development priority must be contrastive then contextual")
        if len(self.final_methods) != len(set(self.final_methods)) or set(
            self.final_methods
        ) != set(METHOD_IDS):
            raise ValueError("final_methods must preserve the complete 26-method suite")
        return self


def load_methods() -> dict[str, MethodSpec]:
    """Load the complete roster without treating blocked methods as runnable."""
    path = REPOSITORY_ROOT / "configs/benchmark-methods.v2.json"
    registry = MethodRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    return {method.method_id: method for method in registry.methods}


def load_benchmark(path: str | Path | None = None) -> BenchmarkConfig:
    """Validate the v2 development configuration and its immutable input bindings."""
    from pose_embed.config import load_protocol
    from pose_embed.protocol import protocol_digest

    source = (
        Path(path)
        if path is not None
        else REPOSITORY_ROOT / "configs/benchmark.v2.yaml"
    )
    config = BenchmarkConfig.model_validate(yaml.safe_load(source.read_text()))
    registry_path = REPOSITORY_ROOT / "configs/benchmark-methods.v2.json"
    methods = load_methods()
    if hashlib.sha256(registry_path.read_bytes()).hexdigest() != config.methods_sha256:
        raise ValueError("method registry hash differs from benchmark configuration")
    for method_id in ("contextual", "contextual_1536"):
        if methods[method_id].parameters["k"] != config.training.samples_per_class:
            raise ValueError("contextual neighborhood must equal samples_per_class")
    protocol = load_protocol(REPOSITORY_ROOT / config.input_protocol)
    if protocol_digest(protocol) != config.input_protocol_sha256:
        raise ValueError("input protocol hash differs from benchmark configuration")
    return config


def benchmark_digest(config: BenchmarkConfig) -> str:
    """Hash scientific settings and the bound registry independently of YAML layout."""
    payload = json.dumps(
        config.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
