"""Executable software rehearsal; every persisted input remains fixture-only.

This intentionally does not grant research admission. The tiny evaluation plan
uses the general plan schema. Independent full-cardinality v3 checks run first.
The only seams substitute licensed source/campaign admission with hash-checked
fixture admission. CLI parsing, training, projection, locks, opening, evaluation,
result loading, provenance rehashing, rank recomputation and v3 analysis run.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import yaml

from pose_embed.artifacts import (
    load_feature_sidecar,
    validate_feature_artifact,
)
from pose_embed.cli import main
from pose_embed.config import (
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.config_v3 import ArtifactBinding
from pose_embed.data import ManifestRecord, load_manifest
from pose_embed.dataset_seal import OPENING, REGISTRY, register_artifact_roots
from pose_embed.protocol import (
    EvaluationManifestValidation,
    EvaluationPlan,
    current_code_hashes,
    evaluation_plan_digest,
    experiment_hyperparameters_digest,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    load_protocol_lock,
    protocol_digest,
    resolve_scientific_paths,
    validate_locked_manifest,
    verify_protocol_lock,
)
from pose_embed.protocol_v3 import V3FinalLock, V3FinalRunSet
from pose_embed.provenance import sha256_file, write_immutable_json
from pose_embed.report import validate_core_report_summary
from pose_embed.training.runner import validate_v3_training_run
from tests.scientific_fixtures import locked_plan
from tests.unit.test_final_bindings_v3 import (  # noqa: F401
    full_metadata_bundle,
)
from tests.unit.test_final_bindings_v3 import (
    test_full_cardinality_v3_metadata_and_lock_cross_bindings as check_full_bindings,
)
from tests.unit.test_training_v3 import _config


def test_complete_v3_cli_fixture_rehearsal(
    repository_root, tmp_path, monkeypatch, capsys, request
):
    check_full_bindings(request.getfixturevalue("full_metadata_bundle"))
    root, data = tmp_path / "fixture-artifacts", tmp_path / "fixture-data"
    root.mkdir()
    data.mkdir()
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    register_artifact_roots([])
    protocol_path = repository_root / "configs/protocol.v3.yaml"
    protocol = load_protocol(protocol_path)
    digest = protocol_digest(protocol)
    paths = resolve_scientific_paths(protocol)
    commands = []

    def fixture_dimensions(config, active):
        assert (config.input_dimension, config.embedding_dimension) == (32, 16)
        validate_experiment_against_protocol(
            config.model_copy(
                update={"input_dimension": 8704, "embedding_dimension": 2048}
            ),
            active,
        )

    monkeypatch.setattr(
        "pose_embed.training.runner.validate_experiment_against_protocol",
        fixture_dimensions,
    )

    def command(*arguments):
        argv = [str(value) for value in arguments]
        code = main(argv)
        output = capsys.readouterr()
        assert code == 0, output.err
        commands.append(argv)

    def source(name, ids, split):
        path = data / f"{name}.npz"
        manifest = root / f"{name}.jsonl"
        rng = np.random.default_rng(len(ids))
        poses = np.zeros((len(ids), 2, 100, 17, 3), dtype=np.float32)
        poses[:, 0, :, :, :2] = rng.normal(size=(len(ids), 100, 17, 2))
        poses[:, 0, :, :, 2] = 1
        np.savez(
            path,
            poses=poses,
            sample_ids=np.asarray(ids),
            labels=np.asarray([int(value[-3:]) for value in ids]),
        )
        manifest.write_text(
            "".join(
                ManifestRecord(
                    sample_id=value, split=split, is_anchor=split == "novel_anchor"
                ).model_dump_json()
                + "\n"
                for value in ids
            )
        )
        return path, manifest

    def extract(name, source_path, manifest, role, split, condition="clean"):
        output = root / f"{name}.npz"
        arguments = [
            "features",
            "extract",
            "--backend",
            "fixture",
            "--input",
            source_path,
            "--output",
            output,
            "--protocol-config",
            protocol_path,
            "--manifest",
            manifest,
            "--role",
            role,
            "--split",
            split,
            "--embedding-dimension",
            32,
        ]
        if condition != "clean":
            family, severity = condition.split(":")
            arguments += [
                "--corruption-family",
                family,
                "--corruption-severity",
                severity,
            ]
        command(*arguments)
        assert load_feature_sidecar(output).scientific_use_allowed is False
        return output

    train_ids = tuple(
        f"S003C001P{index + 1:03d}R001A{action:03d}"
        for index, action in enumerate(
            action for action in [3, 4, 5, 6, 9, 10, 11, 12] for _ in range(4)
        )
    )
    train_source, train_manifest = source("train", train_ids, "final_train")
    train_features = extract(
        "train", train_source, train_manifest, "training", "final_train"
    )
    selection_time = datetime.now(UTC)
    marker = root / "fixture-only.json"
    write_immutable_json(
        marker, {"scientific_use_allowed": False, "fixture_only": True}
    )
    records, selected = [], []
    prefix = root / "study-v3/fixture-rehearsal"
    for method in protocol.objectives.core:
        for seed in protocol.training.seeds:
            run_root = prefix / f"{method}-{seed}"
            run_root.parent.mkdir(parents=True, exist_ok=True)
            config_path = run_root.with_suffix(".yaml")
            config_path.write_text(
                yaml.safe_dump(
                    _config(method)
                    .model_copy(update={"seed": seed})
                    .model_dump(mode="json")
                )
            )
            command(
                "train",
                "--config",
                config_path,
                "--input",
                train_features,
                "--output-dir",
                run_root,
                "--protocol-config",
                protocol_path,
                "--manifest",
                train_manifest,
                "--allow-fixture",
                "--stage",
                "final_training",
            )
            metrics = validate_v3_training_run(run_root, stage="final_training")
            assert metrics["updates"] == 20
            assert metrics["epoch_records"] == {}
            record = {
                "method": method,
                "seed": seed,
                "initialization_sha256": metrics["initialization_sha256"],
            }
            for key, path in (
                ("config", config_path),
                ("run_manifest", run_root / "run-manifest.json"),
                ("checkpoint", run_root / "head.pt"),
                ("batch_plan", run_root / "batch-plan.json"),
                ("metrics", run_root / "metrics.json"),
                ("attempt", run_root / "attempt.json"),
                ("outcome", run_root / "outcome.json"),
            ):
                record[f"{key}_relative_path"] = str(path.relative_to(root))
                record[f"{key}_sha256"] = sha256_file(path)
            records.append(record)
        selected.append(
            {
                "method": method,
                "config_id": f"fixture-{method}",
                "hyperparameters_sha256": experiment_hyperparameters_digest(
                    load_experiment(config_path)
                ),
            }
        )
    assert not paths.test_opening_ledger.exists()
    assert not (root / OPENING).exists()

    anchors = protocol.dataset.official_one_shot_exemplars
    query_ids = tuple(
        f"S002C{camera:03d}P002R001A{action:03d}"
        for action in protocol.dataset.novel_actions
        for camera in (1, 2)
    )
    gallery_source, gallery_manifest = source("gallery", anchors, "novel_anchor")
    gallery = extract(
        "gallery", gallery_source, gallery_manifest, "gallery_clean", "novel_anchor"
    )
    query_inputs, query_manifests, raw_sources = {}, {}, [train_source, gallery_source]
    plan_payload = locked_plan().model_dump(mode="json")
    for definition in ("primary", "official"):
        split = f"novel_query_{definition}"
        raw, manifest = source(definition, query_ids, split)
        raw_sources.append(raw)
        query_manifests[definition] = manifest
        for condition in plan_payload["conditions"]:
            query_inputs[definition, condition] = extract(
                f"{definition}-{condition.replace(':', '-')}",
                raw,
                manifest,
                "query_clean" if condition == "clean" else "query_corrupted",
                split,
                condition,
            )
    inventory = root / "source-inventory.jsonl"
    inventory.write_text(
        train_manifest.read_text()
        + gallery_manifest.read_text()
        + query_manifests["official"].read_text()
    )
    for key, manifest in (
        ("source_inventory", inventory),
        ("anchor", gallery_manifest),
        ("primary_query", query_manifests["primary"]),
        ("official_query", query_manifests["official"]),
    ):
        ids = tuple(row.sample_id for row in load_manifest(manifest))
        plan_payload[f"{key}_manifest"] = {
            "relative_path": str(manifest.relative_to(root)),
            "sha256": sha256_file(manifest),
            "sample_count": len(ids),
            "sample_ids": ids,
        }
    plan = EvaluationPlan.model_validate(plan_payload)
    runs = V3FinalRunSet(
        schema_version=3,
        run_set_id="final-core-run-set-v3",
        protocol_sha256=digest,
        evaluation_plan_sha256=evaluation_plan_digest(plan),
        selection_locked_at=selection_time,
        locked_at=datetime.now(UTC),
        selected_configs=selected,
        runs=records,
        code_sha256=current_code_hashes(repository_root),
        selection_authorization_sha256=sha256_file(marker),
        selection_evidence={
            "relative_path": marker.name,
            "sha256": sha256_file(marker),
        },
    )
    lock = V3FinalLock(
        protocol_id="protocol-v3",
        protocol_sha256=digest,
        evaluation_plan_sha256=evaluation_plan_digest(plan),
        final_run_set_sha256=final_run_set_digest(runs),
        **{
            f"{name}_manifest_sha256": getattr(plan, f"{name}_manifest").sha256
            for name in (
                "source_inventory",
                "anchor",
                "official_query",
                "primary_query",
            )
        },
        recorded_at=datetime.now(UTC),
        locked_at=datetime.now(UTC),
        recorded_by="isolated software fixture",
        design_lock_sha256=sha256_file(marker),
        selection_authorization_sha256=sha256_file(marker),
        artifact_root_registry_sha256=sha256_file(data / REGISTRY),
    )
    for path, payload in (
        (paths.evaluation_plan, plan),
        (paths.final_run_set, runs),
        (paths.protocol_lock, lock),
    ):
        write_immutable_json(path, payload.model_dump(mode="json"))

    # Narrow test-only admission adapters. Never write scientific eligibility to disk.
    def fixture_run(run_set, run, artifact_root, *, protocol):
        assert Path(artifact_root) == root and run_set == runs
        files = {}
        for key in (
            "config",
            "run_manifest",
            "checkpoint",
            "batch_plan",
            "metrics",
            "attempt",
            "outcome",
        ):
            path = root / getattr(run, f"{key}_relative_path")
            assert path.resolve().is_relative_to(root)
            assert sha256_file(path) == getattr(run, f"{key}_sha256")
            files[key] = path
        manifest = json.loads(files["run_manifest"].read_text())
        assert manifest["scientific_use_allowed"] is False
        configuration = load_experiment(files["config"])
        assert (configuration.objective, configuration.seed) == (run.method, run.seed)
        validate_v3_training_run(files["run_manifest"].parent, stage="final_training")
        return files

    def fixture_final_authorization(active, **_):
        assert active == protocol
        current_plan = load_evaluation_plan(paths.evaluation_plan)
        current_runs = load_final_run_set(paths.final_run_set)
        current_lock = load_protocol_lock(paths.protocol_lock)
        verify_protocol_lock(active, current_lock, current_plan, current_runs)
        assert current_lock.artifact_root_registry_sha256 == sha256_file(
            data / REGISTRY
        )
        for run in current_runs.runs:
            fixture_run(current_runs, run, root, protocol=active)
        return current_lock

    raw_hashes = {str(path): sha256_file(path) for path in raw_sources}

    def fixture_manifests(
        active, active_plan, artifact_root, *, check_source_files=True
    ):
        assert (
            active == protocol and active_plan == plan and Path(artifact_root) == root
        )
        manifests = {
            "source_inventory": inventory,
            "anchor": gallery_manifest,
            **query_manifests,
        }
        for name, path in manifests.items():
            key = name if name in {"source_inventory", "anchor"} else name + "_query"
            binding = getattr(plan, f"{key}_manifest")
            validate_locked_manifest(
                binding,
                path,
                expected_split=None
                if name == "source_inventory"
                else "novel_anchor"
                if name == "anchor"
                else f"novel_query_{name}",
            )
        assert {str(path): sha256_file(path) for path in raw_sources} == raw_hashes
        return EvaluationManifestValidation(
            manifests, len(raw_sources), sha256_file(marker), check_source_files
        )

    def fixture_features(path, *, protocol, manifest_path, **_):
        assert Path(path).resolve().is_relative_to(root)
        sidecar = validate_feature_artifact(
            path, protocol=protocol, manifest_path=manifest_path, allow_fixture=True
        )
        assert sidecar.backend == "fixture" and sidecar.scientific_use_allowed is False
        return sidecar.model_copy(
            update={"backend": "motionbert", "scientific_use_allowed": True}
        )

    def fixture_capacity(active, lock_sha256):
        assert active == protocol and lock_sha256 == sha256_file(paths.protocol_lock)
        path = root / "fixture-opening-capacity.json"
        write_immutable_json(
            path,
            {
                "fixture_only": True,
                "recorded_at": datetime.now(UTC).isoformat(),
                "protocol_lock_sha256": lock_sha256,
            },
        )
        return ArtifactBinding(
            relative_path=str(path.relative_to(root)), sha256=sha256_file(path)
        )

    def validate_fixture_capacity(active, binding, lock_sha256):
        assert (
            active == protocol
            and sha256_file(root / binding.relative_path) == binding.sha256
        )
        receipt = json.loads((root / binding.relative_path).read_text())
        assert (
            receipt["fixture_only"] and receipt["protocol_lock_sha256"] == lock_sha256
        )
        return datetime.fromisoformat(receipt["recorded_at"])

    monkeypatch.setattr(
        "pose_embed.opening_capacity_v3.record_opening_capacity", fixture_capacity
    )
    monkeypatch.setattr(
        "pose_embed.opening_capacity_v3.validate_opening_capacity",
        validate_fixture_capacity,
    )
    monkeypatch.setattr(
        "pose_embed.protocol_v3.require_v3_final_authorization",
        fixture_final_authorization,
    )
    for module in (
        "pose_embed.protocol",
        "pose_embed.test_access",
        "pose_embed.evaluation.runner",
        "pose_embed.report",
    ):
        monkeypatch.setattr(f"{module}.validate_final_run_artifacts", fixture_run)
        monkeypatch.setattr(
            f"{module}.validate_evaluation_manifests", fixture_manifests
        )
    for module in ("pose_embed.evaluation.runner", "pose_embed.report"):
        monkeypatch.setattr(f"{module}.validate_feature_artifact", fixture_features)
    command("protocol", "verify", "--config", protocol_path, "--require-locked")

    results = []
    for run in runs.runs:
        projected = {}
        for key, base, manifest in [
            ("gallery", gallery, gallery_manifest),
            *[
                (key, base, query_manifests[key[0]])
                for key, base in query_inputs.items()
            ],
        ]:
            name = "gallery" if key == "gallery" else "-".join(key).replace(":", "-")
            output = prefix / f"{run.method}-{run.seed}-{name}.npz"
            command(
                "features",
                "apply-head",
                "--input",
                base,
                "--output",
                output,
                "--checkpoint",
                root / run.checkpoint_relative_path,
                "--run-manifest",
                root / run.run_manifest_relative_path,
                "--protocol-config",
                protocol_path,
                "--manifest",
                manifest,
                "--allow-fixture",
            )
            projected[key] = output
        for definition, condition in query_inputs:
            slug = f"{run.method}-{run.seed}-{definition}-{condition.replace(':', '-')}"
            output = prefix / f"result-{slug}.json"
            command(
                "evaluate",
                "--mode",
                "final",
                "--gallery",
                projected["gallery"],
                "--queries",
                projected[definition, condition],
                "--output",
                output,
                "--protocol-config",
                protocol_path,
                "--gallery-manifest",
                gallery_manifest,
                "--query-manifest",
                query_manifests[definition],
                "--method",
                run.method,
                "--seed",
                run.seed,
                "--condition",
                condition,
                "--query-definition",
                definition,
            )
            results.append(output)
    assert len(results) == 180
    opening_before = paths.test_opening_ledger.read_bytes()
    report_dir = root / "fixture-report"
    command(
        "report",
        "build",
        "--results",
        *results,
        "--output-dir",
        report_dir,
        "--protocol-config",
        protocol_path,
    )
    certification = validate_core_report_summary(
        report_dir / "summary.json", protocol_path=protocol_path
    )
    summary = json.loads((report_dir / "summary.json").read_text())
    assert certification["complete"] is True
    assert summary["matrix"] == {
        "observed_rows": 180,
        "expected_rows": 180,
        "complete": True,
    }
    assert paths.test_opening_ledger.read_bytes() == opening_before
    analysis = json.loads((report_dir / "primary-analysis.json").read_text())
    assert analysis["schema_version"] == 3
    assert analysis["bootstrap"]["replicates"] == 10000
    assert len(analysis["leave_one_action_out"]["rows"]) == 20
    assert all(
        load_feature_sidecar(path).scientific_use_allowed is False
        for path in root.rglob("*.npz")
    )
    assert all(
        json.loads(path.read_text())["scientific_use_allowed"] is False
        for path in root.rglob("attempt.json")
    )
    assert len(list(root.rglob("attempt.json"))) == 9
    # A schema-valid invented rank must still fail the real artifact recomputation.
    original = results[0].read_bytes()
    forged = json.loads(original)
    rows = forged["metrics"]["per_query"]
    rows[0]["rank"] = 2 if rows[0]["rank"] == 1 else 1
    rows[0]["top1_correct"] = rows[0]["rank"] == 1
    for key, value in (
        ("top1", sum(row["rank"] == 1 for row in rows) / len(rows)),
        ("mrr", sum(1 / row["rank"] for row in rows) / len(rows)),
        ("r_at_5", sum(row["rank"] <= 5 for row in rows) / len(rows)),
    ):
        forged["metrics"][key] = value
    try:
        results[0].write_text(json.dumps(forged))
        status = main(
            [
                "report",
                "build",
                "--results",
                *map(str, results),
                "--output-dir",
                str(root / "forged-report"),
                "--protocol-config",
                str(protocol_path),
            ]
        )
        assert status == 2
        assert "deterministic feature retrieval" in capsys.readouterr().err
        assert not (root / "forged-report").exists()
    finally:
        results[0].write_bytes(original)
    assert paths.test_opening_ledger.read_bytes() == opening_before
    # No raw fixture values or simulated admissions are emitted outside tmp_path.
    write_immutable_json(
        root / "software-rehearsal.json",
        {
            "fixture_only": True,
            "scientific_use_allowed": False,
            "commands": commands,
            "source_admission_seams": [
                "tiny general-plan metadata",
                "32-to-16 fixture head dimensions; remaining v3 recipe validated",
                "fixture-only head/source acceptance",
                "prior scientific campaign admission",
            ],
            "final_results": len(results),
            "trained_heads": 9,
            "report_sha256": sha256_file(report_dir / "summary.json"),
        },
    )
