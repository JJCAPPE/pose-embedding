"""Immutable v3 fallback evidence from streamed clean development-training poses."""

from __future__ import annotations

import hashlib
import json
import math
import platform
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pose_embed.corruptions.pose import torso_scale_v3
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.provenance import write_immutable_json


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _training_ids(sample_ids: Sequence[str]) -> None:
    if not sample_ids or len(set(sample_ids)) != len(sample_ids):
        raise ValueError("fallback sample IDs must be nonempty and unique")
    for sample_id in sample_ids:
        parsed = parse_ntu_sample_id(sample_id)
        if parsed.sample_id != sample_id or parsed.action % 6 in {1, 2}:
            raise ValueError("fallback accepts only canonical 80-action devtrain IDs")


class TorsoFallbackEvidenceV3(BaseModel):
    """Raw-file hashing binds this complete record into the scientific protocol."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    schema_version: int = Field(ge=3, le=3)
    split: str = Field(pattern=r"^development_train$")
    statistic: str = Field(pattern=r"^lower_median_of_valid_sample_lower_medians$")
    source_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preprocessing_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_count: int = Field(gt=0)
    sample_ids_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    contributing_sample_ids: list[str]
    contributing_count: int = Field(gt=0)
    contributing_ids_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_scales: list[float]
    sample_scales_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fallback_required_count: int = Field(ge=0)
    fallback_scale: float = Field(gt=0)
    runtime: dict[str, str]

    @model_validator(mode="after")
    def verify_statistics(self) -> TorsoFallbackEvidenceV3:
        _training_ids(self.contributing_sample_ids)
        if (
            len(self.contributing_sample_ids) != self.contributing_count
            or len(self.sample_scales) != self.contributing_count
            or self.contributing_count + self.fallback_required_count
            != self.sample_count
        ):
            raise ValueError("fallback contribution counts do not reconcile")
        if any(not math.isfinite(value) or value <= 0 for value in self.sample_scales):
            raise ValueError("sample torso scales must be positive and finite")
        if self.contributing_ids_sha256 != _digest(self.contributing_sample_ids):
            raise ValueError("fallback contributing ID hash mismatch")
        if self.sample_scales_sha256 != _digest(self.sample_scales):
            raise ValueError("fallback sample scales hash mismatch")
        median = sorted(self.sample_scales)[(self.contributing_count - 1) // 2]
        if self.fallback_scale != median:
            raise ValueError("fallback is not the lower median sample scale")
        if not self.runtime.get("python") or not self.runtime.get("torch"):
            raise ValueError(
                "fallback evidence must identify Python and Torch runtimes"
            )
        return self


def collect_torso_fallback_v3(
    samples: Iterable[tuple[str, torch.Tensor]],
    *,
    expected_sample_ids: Sequence[str],
    source_inventory_sha256: str,
    source_manifest_sha256: str,
    preprocessing_sha256: str,
    runtime: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Consume each authorized sample once without retaining pose arrays.

    The caller verifies the source files and complete development-training
    manifest before loading. The full protocol cannot be part of the supplied
    preprocessing hash because that protocol will bind this evidence file.
    """
    expected = list(expected_sample_ids)
    _training_ids(expected)
    contributors: list[str] = []
    scales: list[float] = []
    count = 0
    for sample_id, poses in samples:
        if count >= len(expected) or sample_id != expected[count]:
            raise ValueError("fallback input IDs differ from ordered devtrain manifest")
        scale = torso_scale_v3(poses)
        if scale is not None:
            contributors.append(sample_id)
            scales.append(scale)
        count += 1
    if count != len(expected):
        raise ValueError("fallback input is missing development-training samples")
    if not scales:
        raise ValueError("development training has no positive torso fallback")
    record = TorsoFallbackEvidenceV3(
        schema_version=3,
        split="development_train",
        statistic="lower_median_of_valid_sample_lower_medians",
        source_inventory_sha256=source_inventory_sha256,
        source_manifest_sha256=source_manifest_sha256,
        preprocessing_sha256=preprocessing_sha256,
        sample_count=count,
        sample_ids_sha256=_digest(expected),
        contributing_sample_ids=contributors,
        contributing_count=len(contributors),
        contributing_ids_sha256=_digest(contributors),
        sample_scales=scales,
        sample_scales_sha256=_digest(scales),
        fallback_required_count=count - len(contributors),
        fallback_scale=sorted(scales)[(len(scales) - 1) // 2],
        runtime=runtime
        or {"python": platform.python_version(), "torch": str(torch.__version__)},
    )
    return record.model_dump(mode="json")


def validate_torso_fallback_v3(
    record: object,
    *,
    expected_sample_ids: Sequence[str] | None = None,
    source_inventory_sha256: str | None = None,
    source_manifest_sha256: str | None = None,
    preprocessing_sha256: str | None = None,
) -> float:
    """Recompute evidence statistics and optionally enforce its source binding."""
    validated = TorsoFallbackEvidenceV3.model_validate(record)
    if expected_sample_ids is not None:
        expected = list(expected_sample_ids)
        _training_ids(expected)
        contributors = set(validated.contributing_sample_ids)
        if (
            len(expected) != validated.sample_count
            or _digest(expected) != validated.sample_ids_sha256
            or [sample_id for sample_id in expected if sample_id in contributors]
            != validated.contributing_sample_ids
        ):
            raise ValueError("fallback evidence differs from development-training IDs")
    for field, expected_hash in (
        ("source_inventory_sha256", source_inventory_sha256),
        ("source_manifest_sha256", source_manifest_sha256),
        ("preprocessing_sha256", preprocessing_sha256),
    ):
        if expected_hash is not None and getattr(validated, field) != expected_hash:
            raise ValueError(f"fallback evidence {field} mismatch")
    return validated.fallback_scale


def write_torso_fallback_v3(path: str | Path, record: object) -> None:
    """Validate and atomically write once; existing evidence is never replaced."""
    validated = TorsoFallbackEvidenceV3.model_validate(record)
    write_immutable_json(path, validated.model_dump(mode="json"))
