"""Positive novel backend path in an isolated, explicitly non-scientific fixture.

No production gate is relaxed. Test-local adapters admit synthetic source bytes,
a tiny encoder, fixture parity, and metadata-only heads. Real opening, source
inspection, preprocessing, corruptions, cache checks and primary export execute.
The backend's temporary sidecars use its scientific=True schema; the surrounding
receipt explicitly excludes these test artifacts from scientific admission.
"""

from __future__ import annotations

import json
import pickle
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from pose_embed.artifacts import (
    load_feature_sidecar,
    sidecar_path_for,
    validate_feature_artifact,
)
from pose_embed.cli import main
from pose_embed.config import load_protocol
from pose_embed.config_v3 import ArtifactBinding, V3Preparation
from pose_embed.data.inventory import (
    build_split_manifests,
    inspect_ntu_aggregate_sources,
)
from pose_embed.dataset_seal import (
    OPENING,
    REGISTRY,
    register_artifact_roots,
    require_dataset_unopened,
)
from pose_embed.models.motionbert import (
    configure_deterministic_inference,
    inference_environment,
)
from pose_embed.motionbert_features import write_feature_npz
from pose_embed.motionbert_inputs import motionbert_code_digest
from pose_embed.protocol import (
    EvaluationPlan,
    evaluation_plan_digest,
    final_run_set_digest,
    protocol_digest,
    resolve_scientific_paths,
    verify_protocol_lock,
)
from pose_embed.protocol_v3 import V3FinalLock, V3FinalRunSet
from pose_embed.provenance import sha256_file, write_immutable_json
from pose_embed.test_access import validate_recorded_test_opening
from tests.scientific_fixtures import locked_plan, locked_run_set

PREFIX = "study-v3/revisions/execution-r1"


@pytest.fixture
def novel_backend_fixture(repository_root, tmp_path, monkeypatch):
    root, data = tmp_path / "fixture-only-artifacts", tmp_path / "fixture-only-data"
    root.mkdir()
    data.mkdir()
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(root))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(data))
    register_artifact_roots([])
    marker = root / PREFIX / "FIXTURE-ONLY-NOT-SCIENTIFIC.json"
    write_immutable_json(
        marker, {"fixture_only": True, "scientific_use_allowed": False}
    )

    def binding(path):
        return ArtifactBinding(
            relative_path=str(path.relative_to(root)), sha256=sha256_file(path)
        )

    template = load_protocol(repository_root / "configs/protocol.v3.yaml")
    anchors = template.dataset.official_one_shot_exemplars
    other_views = tuple(value[:5] + "001" + value[8:] for value in anchors)
    primary = tuple(
        f"S002C002P002R001A{action:03d}" for action in template.dataset.novel_actions
    )
    auxiliary = tuple(
        f"S003C001P003R001A{action:03d}"
        for action in range(1, 121)
        if action not in template.dataset.novel_actions
    )
    ids = (*auxiliary, *anchors, *other_views, *primary)
    annotations = []
    for index, sample_id in enumerate(ids):
        rng = np.random.default_rng(index)
        xy = rng.uniform(100, 700, size=(1, 4, 17, 2)).astype(np.float32)
        scores = np.ones((1, 4, 17), dtype=np.float32)
        if sample_id in (other_views[1], primary[0]):
            scores[:, :, [5, 6, 11, 12]] = 0
        annotations.append(
            {
                "frame_dir": sample_id,
                "label": int(sample_id[-3:]) - 1,
                "keypoint": xy,
                "keypoint_score": scores,
                "total_frames": 4,
                "img_shape": (1080, 1920),
                "original_shape": (1080, 1920),
            }
        )
    aggregate = data / "fixture-only-aggregate.pkl"
    aggregate.write_bytes(pickle.dumps({"annotations": annotations}))
    missing = data / "fixture-only-missing.txt"
    missing.write_text("S032C003P106R002A120\n")
    # Deliberately not a valid adopted scientific protocol: the loader adapter is
    # test-local. Actual source bytes/counts remain verified throughout the path.
    source = template.dataset.source_contract.model_copy(
        update={
            "aggregate_relative_path": aggregate.name,
            "aggregate_bytes": aggregate.stat().st_size,
            "aggregate_sha256": sha256_file(aggregate),
            "missing_list_relative_path": missing.name,
            "missing_list_bytes": missing.stat().st_size,
            "missing_list_sha256": sha256_file(missing),
            "missing_sample_count": 1,
            "nominal_capture_count": len(ids) + 1,
        }
    )
    access = template.test_access.model_copy(
        update={
            key: value.replace("study-v3/locks/", f"{PREFIX}/locks/")
            for key, value in template.test_access.model_dump().items()
            if key.endswith("_relative_path")
        }
    )
    protocol = template.model_copy(
        update={
            "test_access": access,
            "dataset": template.dataset.model_copy(
                update={
                    "source_contract": source,
                    "expected_source_sample_count": len(ids),
                }
            ),
        }
    )
    inspected = inspect_ntu_aggregate_sources(
        data, protocol, **source.model_dump(), usable_annotation_count=len(ids)
    )
    manifests = build_split_manifests(inspected.records, protocol)
    directory = root / PREFIX / "manifests"
    directory.mkdir()
    inventory = directory / "source-inventory.jsonl"
    rows_by_name = {inventory.name: inspected.records, **manifests}
    for name, rows in rows_by_name.items():
        (directory / name).write_text(
            "".join(row.model_dump_json() + "\n" for row in rows)
        )
    checkpoint, config = (
        data / "fixture-only-weights",
        data / "fixture-only-architecture",
    )
    checkpoint.write_text("tiny encoder; no MotionBERT checkpoint")
    config.write_text("tiny encoder; no MotionBERT architecture")
    assets = {
        "checkpoint_path": str(checkpoint),
        "config_path": str(config),
        "checkpoint_sha256": sha256_file(checkpoint),
        "config_sha256": sha256_file(config),
        "upstream_sha256": "a" * 64,
        "license_sha256": "b" * 64,
        "upstream_commit": "c" * 40,
    }
    protocol = protocol.model_copy(
        update={
            "status": "resolved",
            "preparation": V3Preparation(
                auxiliary_container=binding(marker),
                fallback_evidence=binding(marker),
                fallback_value=1.0,
                source_inventory=binding(inventory),
                identities=binding(marker),
                encoder_checkpoint_sha256=assets["checkpoint_sha256"],
                upstream_sha256={
                    key: assets[key]
                    for key in ("upstream_sha256", "config_sha256", "license_sha256")
                },
            ),
        }
    )
    digest = protocol_digest(protocol)
    paths = resolve_scientific_paths(protocol)
    protocol_path = root / access.resolved_protocol_relative_path
    write_immutable_json(protocol_path, protocol.model_dump(mode="json"))
    bundle = directory / "manifest-set.json"
    write_immutable_json(
        bundle,
        {
            "schema_version": 1,
            "protocol_sha256": digest,
            "source": {
                key: value
                for key, value in source.model_dump().items()
                if key not in {"missing_sample_count", "nominal_capture_count"}
            },
            "protocol_count": {
                "usable_annotations": len(ids),
                "official_missing_skeletons": 1,
                "nominal_captures": len(ids) + 1,
                "locked_expected_rows": len(ids),
                "amendment_required": False,
            },
            "files": {
                name: {"sha256": sha256_file(directory / name), "records": len(rows)}
                for name, rows in rows_by_name.items()
            },
        },
    )
    plan_payload = locked_plan().model_dump(mode="json")
    for key, name in (
        ("source_inventory", inventory.name),
        ("anchor", "novel-anchor.jsonl"),
        ("official_query", "novel-query-official.jsonl"),
        ("primary_query", "novel-query-primary.jsonl"),
    ):
        plan_payload[f"{key}_manifest"] = binding(directory / name).model_dump() | {
            "sample_count": len(rows_by_name[name]),
            "sample_ids": [row.sample_id for row in rows_by_name[name]],
        }
    plan_payload["source_inventory_manifest"].update(
        kind="ntu_aggregate_inventory", aggregate_source=source.model_dump()
    )
    plan = EvaluationPlan.model_validate(plan_payload)
    runs_payload = locked_run_set(digest, plan).model_dump(mode="json")
    runs_payload.update(
        schema_version=3,
        run_set_id="final-core-run-set-v3",
        selection_authorization_sha256=sha256_file(marker),
        selection_evidence=binding(marker).model_dump(),
    )
    for run in runs_payload["runs"]:
        for key in tuple(run):
            if key.endswith("_relative_path"):
                run[key] = f"{PREFIX}/{run[key]}"
    runs = V3FinalRunSet.model_validate(runs_payload)
    lock = V3FinalLock(
        protocol_id="protocol-v3",
        protocol_sha256=digest,
        evaluation_plan_sha256=evaluation_plan_digest(plan),
        final_run_set_sha256=final_run_set_digest(runs),
        **{
            f"{key}_manifest_sha256": getattr(plan, f"{key}_manifest").sha256
            for key in ("source_inventory", "anchor", "official_query", "primary_query")
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
    design = SimpleNamespace(
        manifests={
            name.removesuffix(".jsonl").replace("-", "_"): binding(directory / name)
            for name in manifests
        }
    )

    def fixture_protocol(path):
        assert Path(path).resolve() == protocol_path
        assert json.loads(protocol_path.read_text()) == protocol.model_dump(mode="json")
        return protocol

    def fixture_admission(active, **_):
        assert (
            active == protocol
            and json.loads(marker.read_text())["scientific_use_allowed"] is False
        )
        verify_protocol_lock(active, lock, plan, runs)
        return lock

    for module in ("motionbert_inputs", "motionbert_features", "novel_subset_v3"):
        monkeypatch.setattr(f"pose_embed.{module}.load_protocol", fixture_protocol)
    monkeypatch.setattr(
        "pose_embed.protocol_v3.require_v3_final_authorization", fixture_admission
    )
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.require_v3_final_authorization", fixture_admission
    )
    monkeypatch.setattr(
        "pose_embed.protocol_v3.require_v3_design",
        lambda active: (
            design if active == protocol else pytest.fail("different protocol")
        ),
    )
    monkeypatch.setattr(
        "pose_embed.novel_subset_v3.require_v3_design",
        lambda active: (
            design if active == protocol else pytest.fail("different protocol")
        ),
    )
    monkeypatch.setattr(
        "pose_embed.test_access.validate_final_run_artifacts",
        lambda run_set, run, root_path, **_: (
            None
            if run_set == runs and run in runs.runs and root_path == root
            else pytest.fail("different heads")
        ),
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.require_clean_repository",
        lambda: "fixture-only-clean-check-adapter",
    )
    monkeypatch.setattr("pose_embed.provenance._git_dirty", lambda _: False)

    def capacity(active, lock_sha):
        assert active == protocol and lock_sha == sha256_file(paths.protocol_lock)
        output = root / PREFIX / "fixture-only-capacity.json"
        write_immutable_json(
            output,
            {
                "fixture_only": True,
                "recorded_at": datetime.now(UTC).isoformat(),
                "lock_sha256": lock_sha,
            },
        )
        return binding(output)

    def check_capacity(active, bound, lock_sha):
        assert active == protocol and binding(root / bound.relative_path) == bound
        document = json.loads((root / bound.relative_path).read_text())
        assert document["fixture_only"] and document["lock_sha256"] == lock_sha
        return datetime.fromisoformat(document["recorded_at"])

    monkeypatch.setattr(
        "pose_embed.opening_capacity_v3.record_opening_capacity", capacity
    )
    monkeypatch.setattr(
        "pose_embed.opening_capacity_v3.validate_opening_capacity", check_capacity
    )
    configure_deterministic_inference()
    environment = inference_environment(torch.device("cpu"))
    bindings = {
        "protocol_sha256": digest,
        "manifest_set_sha256": sha256_file(bundle),
        "source_inventory_sha256": sha256_file(inventory),
        "aggregate_sha256": sha256_file(aggregate),
        "missing_list_sha256": sha256_file(missing),
        "code_sha256": motionbert_code_digest(),
        "dependency_lock_sha256": sha256_file(repository_root / "uv.lock"),
        **{
            key: assets[key]
            for key in (
                "upstream_sha256",
                "checkpoint_sha256",
                "config_sha256",
                "license_sha256",
                "upstream_commit",
            )
        },
    }
    parity = root / PREFIX / "fixture-only-parity.json"
    write_immutable_json(
        parity, {"fixture_only": True, "bindings": bindings, "environment": environment}
    )

    def check_parity(path, expected):
        document = json.loads(Path(path).read_text())
        assert document["fixture_only"] and document["bindings"] == expected
        return document

    calls = {"encoder": 0, "novel_load": 0}

    class TinyEncoder:
        def get_representation(self, tensor):
            calls["encoder"] += 1
            return (
                (tensor[..., 0] + 2 * tensor[..., 1] + 3 * tensor[..., 2])
                .unsqueeze(-1)
                .expand(*tensor.shape[:-1], 512)
            )

    monkeypatch.setattr(
        "pose_embed.models.motionbert.load_frozen_encoder",
        lambda *a, **k: (TinyEncoder(), assets),
    )
    monkeypatch.setattr(
        "pose_embed.models.motionbert.verify_motionbert_assets", lambda _: assets
    )
    monkeypatch.setattr(
        "pose_embed.motionbert_parity.validate_parity_report", check_parity
    )

    def inspect_after_opening(*args, **kwargs):
        # This is the actual novel-loader deserialization boundary, after the
        # opening's initial physical-source audit and atomic common/ledger writes.
        validate_recorded_test_opening(protocol)
        assert (root / OPENING).is_file() and paths.test_opening_ledger.is_file()
        calls["novel_load"] += 1
        return inspect_ntu_aggregate_sources(*args, **kwargs)

    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.inspect_ntu_aggregate_sources",
        inspect_after_opening,
    )
    return SimpleNamespace(
        root=root,
        data=data,
        protocol=protocol,
        protocol_path=protocol_path,
        paths=paths,
        aggregate=aggregate,
        bundle=bundle,
        parity=parity,
        directory=directory,
        calls=calls,
        primary=primary,
        other_views=other_views,
    )


def test_positive_novel_extraction_primary_export_and_archival_validation(
    novel_backend_fixture, monkeypatch, capsys
):
    fixture = novel_backend_fixture
    commands, artifacts = [], []

    def command(*arguments):
        argv = [str(value) for value in arguments]
        assert main(argv) == 0, capsys.readouterr().err
        capsys.readouterr()
        commands.append(argv)

    assert not fixture.paths.test_opening_ledger.exists()
    for condition in ("clean", "coordinate_jitter:0.025"):
        official = fixture.root / PREFIX / f"official-{condition.replace(':', '-')}.npz"
        arguments = [
            "features",
            "extract",
            "--backend",
            "motionbert",
            "--device",
            "cpu",
            "--input",
            fixture.aggregate,
            "--output",
            official,
            "--protocol-config",
            fixture.protocol_path,
            "--manifest-set",
            fixture.bundle,
            "--parity-evidence",
            fixture.parity,
            "--manifest",
            fixture.directory / "novel-query-official.jsonl",
            "--role",
            "query_clean" if condition == "clean" else "query_corrupted",
            "--split",
            "novel_query_official",
        ]
        if condition != "clean":
            arguments += [
                "--corruption-family",
                "coordinate_jitter",
                "--corruption-severity",
                "0.025",
            ]
        command(*arguments)
        opening = validate_recorded_test_opening(fixture.protocol)
        with pytest.raises(ValueError, match="after test opening"):
            require_dataset_unopened(require_registry=True)
        seal_hash = sha256_file(fixture.root / OPENING)
        ledger_hash = sha256_file(fixture.paths.test_opening_ledger)
        encoder_calls = fixture.calls["encoder"]
        primary = fixture.root / PREFIX / f"primary-{condition.replace(':', '-')}.npz"
        command(
            "features",
            "export-primary",
            "--protocol-config",
            fixture.protocol_path,
            "--input",
            official,
            "--output",
            primary,
        )
        assert fixture.calls["encoder"] == encoder_calls
        assert sha256_file(fixture.root / OPENING) == seal_hash
        assert sha256_file(fixture.paths.test_opening_ledger) == ledger_hash
        assert (
            validate_recorded_test_opening(fixture.protocol).event_id
            == opening.event_id
        )
        sidecar = validate_feature_artifact(
            primary,
            protocol=fixture.protocol,
            manifest_path=fixture.directory / "novel-query-primary.jsonl",
        )
        assert sidecar.sample_ids == fixture.primary
        assert sidecar.provenance["primary_subset"]["artifact_sha256"] == sha256_file(
            official
        )
        with np.load(official) as full, np.load(primary) as subset:
            positions = [
                list(full["sample_ids"]).index(value) for value in fixture.primary
            ]
            for key in ("features", "labels", "sample_ids"):
                np.testing.assert_array_equal(subset[key], full[key][positions])
        if condition != "clean":
            assert (
                load_feature_sidecar(official).provenance["jitter_fallback"][
                    "fallback_count"
                ]
                == 2
            )
            assert sidecar.provenance["jitter_fallback"]["fallback_sample_ids"] == [
                fixture.primary[0]
            ]
            assert [
                row["sample_id"] for row in sidecar.provenance["geometry"]["rows"]
            ] == list(fixture.primary)
        artifacts.extend((official, primary))
    assert fixture.calls == {"encoder": 4, "novel_load": 2}

    def forbidden(*args, **kwargs):
        pytest.fail("archival validation reopened raw poses or loaded the encoder")

    monkeypatch.setattr(
        "pose_embed.motionbert_inputs.inspect_ntu_aggregate_sources", forbidden
    )
    monkeypatch.setattr(
        "pose_embed.data.inventory.inspect_ntu_aggregate_sources", forbidden
    )
    monkeypatch.setattr("pose_embed.models.motionbert.load_frozen_encoder", forbidden)
    for artifact in artifacts:
        split = load_feature_sidecar(artifact).split
        validate_feature_artifact(
            artifact,
            protocol=fixture.protocol,
            manifest_path=fixture.directory / f"{split.replace('_', '-')}.jsonl",
        )
    # Even with self-consistent hashes/shapes/labels, invented subset features fail.
    forged = fixture.root / PREFIX / "rejected-forged-primary.npz"
    with np.load(primary) as source:
        write_feature_npz(
            forged, source["features"][::-1], source["labels"], source["sample_ids"]
        )
    forged_sidecar = load_feature_sidecar(primary).model_copy(
        update={"artifact_sha256": sha256_file(forged)}
    )
    write_immutable_json(
        sidecar_path_for(forged), forged_sidecar.model_dump(mode="json")
    )
    with pytest.raises(ValueError, match="exact ordered official rows"):
        validate_feature_artifact(
            forged,
            protocol=fixture.protocol,
            manifest_path=fixture.directory / "novel-query-primary.jsonl",
        )
    # Retain an explicit fixture classification alongside backend-schema sidecars.
    # These outputs cannot meet the production protocol/admission/parity gates.
    write_immutable_json(
        fixture.root / "novel-pipeline-software-rehearsal.json",
        {
            "fixture_only": True,
            "scientific_use_allowed": False,
            "status": "passed",
            "artifact_root": str(fixture.root),
            "data_root": str(fixture.data),
            "commands": commands,
            "test_local_adapters": [
                "synthetic physical-source protocol/cardinality",
                "prior design/campaign and metadata-only nine heads",
                "tiny encoder/assets and fixture parity",
                "clean-checkout status",
                "fixture opening capacity",
            ],
            "checks": [
                "actual atomic opening and canonical ledger identity",
                "novel deserialization after opening",
                "real synthetic aggregate hashes/inventory/partitions",
                "real preprocessing/corruption/pooling",
                "official cache provenance",
                "exact primary feature/telemetry subset without encoding",
                "archival validation without raw source access",
                "hash-consistent forged primary features rejected",
            ],
            "files": {
                str(path): sha256_file(path)
                for base in (fixture.root, fixture.data)
                for path in sorted(base.rglob("*"))
                if path.is_file()
            },
            "backend_sidecars_use_scientific_schema": True,
            "intentionally_rejected_artifacts": [str(forged)],
        },
    )
