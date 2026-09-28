from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

import pose_embed.motionbert_reproducibility as reproducibility
from pose_embed.motionbert_reproducibility import GIB, extraction_forecast


def _runs():
    return [
        dict(
            wall_time_seconds=3000.0,
            sample_count=95001,
            artifact_bytes=4 * GIB,
            peak_gpu_memory_bytes=3 * GIB,
            peak_host_memory_bytes=8 * GIB,
        )
        for _ in range(2)
    ]


def test_forecast_uses_slower_full_run_and_margins() -> None:
    runs = _runs()
    runs[1]["wall_time_seconds"] = 3500
    forecast = extraction_forecast(runs, full_sample_count=113945, free_bytes=300 * GIB)
    assert forecast["passed"]
    assert forecast["projected_seconds"] == pytest.approx(3500 * 113945 / 95001 * 1.25)
    assert forecast["checks"]["cache_storage"]


@pytest.mark.parametrize(
    "field,value,check",
    [
        ("wall_time_seconds", 15000, "runtime"),
        ("artifact_bytes", 7 * GIB, "cache_storage"),
        ("peak_gpu_memory_bytes", 17 * GIB, "gpu_memory"),
        ("peak_host_memory_bytes", 33 * GIB, "host_memory"),
    ],
)
def test_each_resource_limit_fails_closed(field, value, check) -> None:
    runs = _runs()
    runs[1][field] = value
    forecast = extraction_forecast(runs, full_sample_count=113945, free_bytes=300 * GIB)
    assert not forecast["passed"]
    assert not forecast["checks"][check]


def test_missing_gpu_evidence_or_storage_cannot_pass() -> None:
    runs = _runs()
    assert not extraction_forecast(
        runs, full_sample_count=113945, free_bytes=100 * GIB
    )["passed"]
    runs[0]["peak_gpu_memory_bytes"] = 0
    with pytest.raises(ValueError, match="telemetry"):
        extraction_forecast(runs, full_sample_count=113945, free_bytes=300 * GIB)


@pytest.mark.parametrize(
    "full_count,free_bytes",
    [
        (0, 10),
        (-1, 10),
        (True, 10),
        (113945.5, 10),
        (113945, -1),
        (113945, False),
        (113945, float("inf")),
    ],
)
def test_forecast_rejects_malformed_inventory_or_storage(
    full_count, free_bytes
) -> None:
    with pytest.raises(ValueError, match="forecast requires"):
        extraction_forecast(
            _runs(), full_sample_count=full_count, free_bytes=free_bytes
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_count", True),
        ("sample_count", 1.5),
        ("sample_count", 200000),
        ("artifact_bytes", 4.5),
        ("peak_gpu_memory_bytes", False),
        ("peak_host_memory_bytes", 1.5),
        ("wall_time_seconds", float("nan")),
    ],
)
def test_forecast_rejects_invalid_run_measurements(field, value) -> None:
    runs = _runs()
    runs[0][field] = value
    with pytest.raises(ValueError):
        extraction_forecast(runs, full_sample_count=113945, free_bytes=300 * GIB)


@pytest.fixture
def repeat_pair(tmp_path, monkeypatch):
    # Archive/sidecar validation is covered by artifact-contract tests. These
    # small archives isolate repeatability control and telemetry checks.
    paths = [tmp_path / "first.npz", tmp_path / "second.npz"]
    for path in paths:
        np.savez(path, features=np.ones((2, 3)), labels=[1, 2], sample_ids=["a", "b"])
        path.with_suffix(".npz.manifest.json").write_text("{}")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("fixture")
    stages = dict.fromkeys(
        (
            "source_verification_load",
            "encoder_load_and_parity_validation",
            "preprocessing",
            "transfer",
            "encoder",
            "pooling",
            "serialization",
        ),
        1.0,
    )
    environment = {
        "device_type": "cuda",
        "cuda_device_uuid": "GPU-test",
        "cuda_device_name": "GPU fixture",
        "hostname": "test-host",
    }
    start = datetime.now(UTC) - timedelta(hours=2)
    sidecars = []
    for index, path in enumerate(paths):
        began = start + timedelta(seconds=index * 120)
        sidecars.append(
            SimpleNamespace(
                method="frozen_encoder_cache",
                split="final_train",
                role="training",
                shape=(95001, 8704),
                artifact_sha256="a" * 64,
                sample_order_sha256="b" * 64,
                manifest_sha256="c" * 64,
                provenance={
                    "inference_environment": deepcopy(environment),
                    "process": {"pid": 100 + index, "job_id": "123"},
                    "started_at": began.isoformat(),
                    "ended_at": (began + timedelta(seconds=100)).isoformat(),
                    "extraction": {
                        **_runs()[index],
                        "wall_time_seconds": 100,
                        "artifact_bytes": path.stat().st_size,
                        "stage_seconds": deepcopy(stages),
                    },
                },
            )
        )
    monkeypatch.setattr(
        reproducibility,
        "load_protocol",
        lambda _: SimpleNamespace(
            dataset=SimpleNamespace(expected_source_sample_count=113945)
        ),
    )
    monkeypatch.setattr(
        reproducibility,
        "resolve_scientific_paths",
        lambda _: SimpleNamespace(
            root=tmp_path, test_opening_ledger=tmp_path / "sealed.json"
        ),
    )
    monkeypatch.setattr(reproducibility, "protocol_digest", lambda _: "d" * 64)
    monkeypatch.setattr(
        reproducibility,
        "validate_feature_artifact",
        lambda path, **kwargs: sidecars[paths.index(path)],
    )
    monkeypatch.setattr(
        reproducibility.shutil, "disk_usage", lambda _: SimpleNamespace(free=300 * GIB)
    )

    def verify():
        return reproducibility.verify_repeatability(
            *paths,
            protocol_path="unused",
            manifest_path=manifest,
            output_path=tmp_path / "report.json",
        )

    return paths, sidecars, verify, tmp_path / "report.json"


def test_verified_repeat_pair_publishes_bound_process_evidence(repeat_pair) -> None:
    _, sidecars, verify, output = repeat_pair
    sidecars[0].provenance["extraction"]["stage_seconds"]["cache_verification"] = 1
    report = verify()
    assert report["status"] == "passed"
    assert report["identical_arrays"]
    assert report["processes"] == [s.provenance["process"] for s in sidecars]
    assert output.is_file()


@pytest.mark.parametrize(
    "ledger_name", ["sealed.json", "benchmark-v2/locks/test-opening.json"]
)
def test_repeatability_rejects_opened_test(repeat_pair, ledger_name) -> None:
    _, _, verify, output = repeat_pair
    ledger = output.parent / ledger_name
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="novel test to remain sealed"):
        verify()
    assert not output.exists()


@pytest.mark.parametrize("key,value", [("sample_count", 950010), ("artifact_bytes", 1)])
def test_repeat_telemetry_must_match_validated_cache(repeat_pair, key, value) -> None:
    _, sidecars, verify, output = repeat_pair
    sidecars[0].provenance["extraction"][key] = value
    with pytest.raises(ValueError, match="verified cache count or bytes"):
        verify()
    assert not output.exists()


@pytest.mark.parametrize(
    "process",
    [
        {"pid": True, "job_id": "123"},
        {"pid": "101", "job_id": "123"},
        {"pid": -1, "job_id": "123"},
        {"pid": 101, "job_id": True},
        {"pid": 101, "job_id": "other"},
        {"pid": 100, "job_id": "123"},
        {"pid": 101, "job_id": "124"},
    ],
)
def test_repeat_requires_real_distinct_process_identifiers(
    repeat_pair, process
) -> None:
    _, sidecars, verify, _ = repeat_pair
    sidecars[1].provenance["process"] = process
    with pytest.raises(ValueError, match="fresh processes"):
        verify()


@pytest.mark.parametrize("value", [None, "", True, 123])
def test_repeat_requires_physical_gpu_identity(repeat_pair, value) -> None:
    _, sidecars, verify, _ = repeat_pair
    for sidecar in sidecars:
        sidecar.provenance["inference_environment"]["cuda_device_uuid"] = value
    with pytest.raises(ValueError, match="same identified GPU"):
        verify()


def test_repeat_rejects_different_gpus(repeat_pair) -> None:
    _, sidecars, verify, _ = repeat_pair
    sidecars[1].provenance["inference_environment"]["cuda_device_uuid"] = "GPU-other"
    with pytest.raises(ValueError, match="same identified GPU"):
        verify()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "naive",
        "future",
        "reversed",
        "overlap",
        "underreported",
        "bad_stage",
        "absent_stage",
    ],
)
def test_repeat_requires_consistent_timing_evidence(repeat_pair, mutation) -> None:
    _, sidecars, verify, output = repeat_pair
    provenance = sidecars[1].provenance
    if mutation == "missing":
        del provenance["started_at"]
    elif mutation == "naive":
        provenance["started_at"] = "2026-01-01T00:00:00"
    elif mutation == "future":
        provenance["ended_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    elif mutation == "reversed":
        provenance["started_at"], provenance["ended_at"] = (
            provenance["ended_at"],
            provenance["started_at"],
        )
    elif mutation == "overlap":
        provenance["started_at"] = sidecars[0].provenance["started_at"]
        provenance["extraction"]["wall_time_seconds"] = 220
    elif mutation == "underreported":
        provenance["extraction"]["wall_time_seconds"] = 50
    elif mutation == "bad_stage":
        provenance["extraction"]["stage_seconds"]["encoder"] = float("nan")
    else:
        del provenance["extraction"]["stage_seconds"]["encoder"]
    with pytest.raises(ValueError):
        verify()
    assert not output.exists()


def test_repeat_rejects_one_hardlinked_output(repeat_pair) -> None:
    paths, _, verify, _ = repeat_pair
    paths[1].unlink()
    paths[1].hardlink_to(paths[0])
    with pytest.raises(ValueError, match="distinct extraction outputs"):
        verify()


def test_failed_resource_gate_preserves_failure_report(repeat_pair) -> None:
    _, sidecars, verify, output = repeat_pair
    sidecars[0].provenance["extraction"]["peak_gpu_memory_bytes"] = 17 * GIB
    with pytest.raises(ValueError, match="resource gate failed"):
        verify()
    assert '"status": "failed"' in output.read_text()
