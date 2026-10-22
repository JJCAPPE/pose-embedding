"""Independent allocated-process revalidation of successor caches and paired pilots."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from pose_embed.artifacts import (
    load_feature_sidecar,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.config import load_protocol
from pose_embed.dataset_seal import (
    canonical_artifact_root,
    dataset_access,
    require_dataset_unopened,
)
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.motionbert_reproducibility import verify_repeatability
from pose_embed.protocol import protocol_digest
from pose_embed.protocol_v3 import require_v3_design
from pose_embed.provenance import (
    capture_runtime_telemetry,
    require_path_within,
    sha256_file,
    write_immutable_json,
)
from pose_embed.training.runner import validate_engineering_pilot
from pose_embed.validation_proofs import (
    validation_session,
    verify_validation_proofs,
)

CACHES = (
    ("final-train-first", "final-train.jsonl", 95001, "training", "final_train"),
    ("final-train-second", "final-train.jsonl", 95001, "training", "final_train"),
    (
        "development-train",
        "development-train.jsonl",
        76013,
        "training",
        "development_train",
    ),
    (
        "development-gallery",
        "development/development-gallery.jsonl",
        20,
        "gallery_clean",
        "development_validation",
    ),
    (
        "development-queries",
        "development/development-queries.jsonl",
        18929,
        "query_clean",
        "development_validation",
    ),
)


def validate_caches(cache, bundle, protocol, protocol_path, output):
    records = {}
    for name, manifest, count, role, split in CACHES:
        source = cache / f"{name}.npz"
        started = time.perf_counter()
        digest = sha256_file(source)
        hash_seconds = time.perf_counter() - started
        started = time.perf_counter()
        sidecar = validate_feature_artifact(
            source, protocol=protocol, manifest_path=bundle / manifest
        )
        if not sidecar.scientific_use_allowed or (
            sidecar.shape,
            sidecar.role,
            sidecar.split,
            sidecar.method,
        ) != ((count, 8704), role, split, "frozen_encoder_cache"):
            raise ValueError("cache scientific identity or dimensions differ")
        if digest != sidecar.artifact_sha256:
            raise ValueError("cache changed between hashing and validation")
        records[name] = {
            "artifact_sha256": digest,
            "sidecar_sha256": sha256_file(sidecar_path_for(source)),
            "hashing_seconds": hash_seconds,
            "artifact_validation_seconds": time.perf_counter() - started,
            "extraction": sidecar.provenance["extraction"],
        }
    quota = output.with_name("validation-quota.txt")
    with quota.open("x") as stream:
        subprocess.run(["pquota", "textconv"], check=True, stdout=stream)
    repeated = output.with_name("validation-repeatability.json")
    repeat = verify_repeatability(
        cache / "final-train-first.npz",
        cache / "final-train-second.npz",
        protocol_path=protocol_path,
        manifest_path=bundle / "final-train.jsonl",
        output_path=repeated,
        project_quota_report=quota,
    )
    original = json.loads((cache / "repeatability.json").read_text())
    if original["status"] != "passed" or original["inputs"] != repeat["inputs"]:
        raise ValueError("original repeatability input bindings differ")
    return {
        "caches": records,
        "repeatability_sha256": sha256_file(repeated),
        "parity_sha256": sha256_file(cache / "parity.json"),
    }


def validate_pilots(pilots, cache, bundle):
    records = {}
    paired = []
    training = load_feature_sidecar(cache / "development-train.npz").model_dump(
        mode="json"
    )
    development = {
        str(path.resolve()): sha256_file(path)
        for name in ("gallery", "queries")
        for path in (
            cache / f"development-{name}.npz",
            sidecar_path_for(cache / f"development-{name}.npz"),
            bundle / f"development/development-{name}.jsonl",
        )
    }
    for method, run in zip(
        ("contrastive", "contextual", "supcon"), pilots, strict=True
    ):
        if (run.parent / "scheduler-exit.txt").read_text().strip() != "exit_status=0":
            raise ValueError("pilot scheduler job did not complete successfully")
        metrics = validate_engineering_pilot(run)
        manifest = json.loads((run / "run-manifest.json").read_text())
        if (
            metrics["objective"] != method
            or metrics["input_metadata"] != training
            or manifest["development_inputs"] != development
        ):
            raise ValueError("pilot method or input cache differs")
        fixture = json.loads((run.parent / "learnable-fixture.json").read_text())
        outcome = json.loads((run.parent / "fixture-outcome.json").read_text())
        if (
            fixture["updates"],
            fixture["top1"],
            fixture["input_dimension"],
            fixture["embedding_dimension"],
        ) != (1000, 1.0, 8704, 2048):
            raise ValueError("fixed full-size learnable fixture failed")
        if outcome["status"] != "success" or outcome["result_sha256"] != sha256_file(
            run.parent / "learnable-fixture.json"
        ):
            raise ValueError("fixture outcome binding differs")
        if (
            fixture["provenance"]["configuration"]
            != manifest["configuration"]["experiment"]
        ):
            raise ValueError("fixture and pilot recipes differ")
        paired.append(
            {
                key: metrics[key]
                for key in (
                    "initialization_sha256",
                    "batch_plan_sha256",
                    "epoch_batch_plan_sha256",
                )
            }
        )
        records[method] = {
            "run_manifest_sha256": sha256_file(run / "run-manifest.json"),
            "metrics_sha256": sha256_file(run / "metrics.json"),
            "fixture_sha256": outcome["result_sha256"],
            "stage_seconds": metrics["stage_seconds"],
            "updates": metrics["updates"],
            "peak_host_memory_bytes": metrics["peak_host_memory_bytes"],
            "peak_gpu_allocated_bytes": metrics["peak_gpu_allocated_bytes"],
        }
    if any(value != paired[0] for value in paired):
        raise ValueError("successor pilots are not paired")
    return {"pilots": records, "paired_hashes": paired[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("caches", "pilots"))
    parser.add_argument("--protocol-config", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--manifest-set", type=Path, required=True)
    parser.add_argument("--pilot-dirs", type=Path, nargs=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("JOB_ID", "").isdecimal() or (args.mode == "pilots") != bool(
        args.pilot_dirs
    ):
        parser.error("allocated job and mode-specific arguments required")
    root = canonical_artifact_root()
    output = require_path_within(args.output, root, label="validation output")
    if output.exists():
        raise ValueError("validation receipts are immutable")
    started = datetime.now(UTC)
    receipt = {
        "mode": args.mode,
        "started_at": started.isoformat(),
        "script_sha256": sha256_file(__file__),
    }
    try:
        with validation_session(fresh=True) as proof_session, dataset_access():
            require_dataset_unopened(require_registry=True)
            require_clean_repository()
            protocol = load_protocol(args.protocol_config)
            require_v3_design(protocol)
            receipt["protocol_sha256"] = protocol_digest(protocol)
            receipt["manifest_set_sha256"] = sha256_file(args.manifest_set)
            if (
                args.cache_dir / "scheduler-exit.txt"
            ).read_text().strip() != "exit_status=0":
                raise ValueError("cache job did not complete successfully")
            if args.mode == "caches":
                receipt.update(
                    validate_caches(
                        args.cache_dir,
                        args.manifest_set.parent,
                        protocol,
                        args.protocol_config,
                        output,
                    )
                )
            else:
                receipt.update(
                    validate_pilots(
                        args.pilot_dirs, args.cache_dir, args.manifest_set.parent
                    )
                )
            verify_validation_proofs()
            receipt["status"] = "passed"
        receipt["numerical_validation"] = proof_session.statistics()
    except Exception as error:
        receipt.update(
            status="failed", error_type=type(error).__name__, error_message=str(error)
        )
    receipt["validation_telemetry"] = capture_runtime_telemetry(
        started_at=started, ended_at=datetime.now(UTC)
    ).model_dump(mode="json")
    write_immutable_json(output, receipt)
    if receipt["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
