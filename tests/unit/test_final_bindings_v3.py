"""Full-cardinality synthetic metadata; no source bytes or scientific admission."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from itertools import islice, product
from pathlib import Path
from types import SimpleNamespace

import pytest

from pose_embed.config import load_protocol
from pose_embed.config_v3 import ProtocolV3Config
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.protocol import (
    current_code_hashes,
    evaluation_plan_digest,
    final_run_set_digest,
    load_evaluation_plan,
    load_final_run_set,
    load_protocol_lock,
    protocol_digest,
    validate_evaluation_manifests,
    verify_protocol_lock,
)
from pose_embed.protocol_v3 import (
    V3EvaluationPlan,
    V3FinalLock,
    V3FinalRunSet,
    V3SelectionAuthorization,
    require_v3_final_authorization,
)
from pose_embed.provenance import sha256_file, write_immutable_json
from tests.scientific_fixtures import locked_run_set

PREFIX = "study-v3/revisions/execution-r1"


def _ids(actions):
    for setup, camera, performer, repetition, action in product(
        range(1, 33), range(1, 4), range(1, 107), (1, 2), actions
    ):
        yield f"S{setup:03}C{camera:03}P{performer:03}R{repetition:03}A{action:03}"


@pytest.fixture(scope="module")
def full_metadata_bundle(tmp_path_factory):
    root = tmp_path_factory.mktemp("synthetic-v3-bindings")
    repository = Path(__file__).resolve().parents[2]
    template = load_protocol(repository / "configs/protocol.v3.yaml")
    anchors = template.dataset.official_one_shot_exemplars
    excluded = {parse_ntu_sample_id(value).performance_id for value in anchors}
    primary = tuple(
        islice(
            (
                value
                for value in _ids(template.dataset.novel_actions)
                if parse_ntu_sample_id(value).performance_id not in excluded
            ),
            18884,
        )
    )
    other_anchor_views = tuple(
        value[:5] + f"00{camera}" + value[8:] for value in anchors for camera in (1, 2)
    )
    official = tuple(sorted((*primary, *other_anchor_views)))
    auxiliary = tuple(
        islice(
            _ids(sorted(set(range(1, 121)) - set(template.dataset.novel_actions))),
            95001,
        )
    )
    source_ids = tuple(sorted((*auxiliary, *anchors, *official)))
    source_path = root / PREFIX / "manifests/source-inventory.jsonl"
    source_path.parent.mkdir(parents=True)
    with source_path.open("w") as stream:
        for index, sample_id in enumerate(source_ids):
            parsed = parse_ntu_sample_id(sample_id)
            stream.write(
                json.dumps(
                    {
                        "sample_id": sample_id,
                        "annotation_index": index,
                        **{
                            name: getattr(parsed, name)
                            for name in (
                                "setup",
                                "camera",
                                "performer",
                                "repetition",
                                "action",
                            )
                        },
                        "label": parsed.action - 1,
                        "pose_track_count": 1,
                        "nonempty_track_count": 1,
                        "total_frames": 100,
                        "keypoint_shape": [1, 100, 17, 2],
                        "keypoint_score_shape": [1, 100, 17],
                        "image_shape": [1080, 1920],
                        "original_shape": [1080, 1920],
                    }
                )
                + "\n"
            )

    payload = template.model_dump(mode="json")
    for key, value in payload["test_access"].items():
        if key.endswith("_relative_path"):
            payload["test_access"][key] = value.replace(
                "study-v3/locks/", f"{PREFIX}/locks/"
            )
    marker = root / PREFIX / "fixture-only.json"
    write_immutable_json(
        marker, {"fixture_only": True, "scientific_use_allowed": False}
    )
    binding = {
        "relative_path": str(marker.relative_to(root)),
        "sha256": sha256_file(marker),
    }
    payload.update(
        status="resolved",
        preparation={
            "auxiliary_container": binding,
            "fallback_evidence": binding,
            "fallback_value": 1.0,
            "source_inventory": {
                "relative_path": str(source_path.relative_to(root)),
                "sha256": sha256_file(source_path),
            },
            "identities": binding,
            "encoder_checkpoint_sha256": "a" * 64,
            "upstream_sha256": {
                key: "a" * 64
                for key in ("upstream_sha256", "config_sha256", "license_sha256")
            },
        },
    )
    protocol = ProtocolV3Config.model_validate(payload)
    plan_payload = load_evaluation_plan(
        repository / "configs/evaluation-plan.v3.yaml"
    ).model_dump(mode="json")
    plan_payload["status"] = "locked"
    plan_payload["source_inventory_manifest"] = {
        "relative_path": str(source_path.relative_to(root)),
        "sha256": sha256_file(source_path),
        "sample_count": len(source_ids),
        "sample_ids": source_ids,
        "kind": "ntu_aggregate_inventory",
        "aggregate_source": protocol.dataset.source_contract.model_dump(mode="json"),
    }
    for key, ids, split in (
        ("anchor", anchors, "novel_anchor"),
        ("official_query", official, "novel_query_official"),
        ("primary_query", tuple(sorted(primary)), "novel_query_primary"),
    ):
        path = root / PREFIX / f"manifests/{split}.jsonl"
        path.write_text(
            "".join(
                json.dumps(
                    {
                        "sample_id": value,
                        "split": split,
                        "is_anchor": split == "novel_anchor",
                    }
                )
                + "\n"
                for value in ids
            )
        )
        plan_payload[f"{key}_manifest"] = {
            "relative_path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "sample_count": len(ids),
            "sample_ids": ids,
        }
    plan = V3EvaluationPlan.model_validate(plan_payload)
    digest = protocol_digest(protocol)
    authorization = V3SelectionAuthorization(
        schema_version=3,
        kind="v3_selection_authorization",
        protocol_sha256=digest,
        design_lock_sha256=sha256_file(marker),
        recorded_at=datetime(2026, 9, 30, tzinfo=UTC),
        recorded_by="test fixture",
        pilot_records={method: binding for method in plan.methods},
        corruption_verification=binding,
        analysis_verification=binding,
        capacity_report=binding,
        seal_audit=binding,
        run_matrix=binding,
        capacity_passed=True,
        novel_access_authorized=False,
    )
    selection_path = root / protocol.test_access.selection_authorization_relative_path
    write_immutable_json(selection_path, authorization.model_dump(mode="json"))
    runs_payload = locked_run_set(digest, plan).model_dump(mode="json")
    runs_payload.update(
        schema_version=3,
        run_set_id="final-core-run-set-v3",
        selection_authorization_sha256=sha256_file(selection_path),
        selection_evidence=binding,
        selection_locked_at="2026-10-01T00:00:00Z",
        locked_at="2026-10-02T00:00:00Z",
        code_sha256=current_code_hashes(repository).model_dump(),
    )
    for run in runs_payload["runs"]:
        for key in tuple(run):
            if key.endswith("_relative_path"):
                run[key] = f"{PREFIX}/{run[key]}"
    runs = V3FinalRunSet.model_validate(runs_payload)
    registry = root / "registry.json"
    write_immutable_json(registry, {"fixture_only": True})
    lock = V3FinalLock(
        protocol_id="protocol-v3",
        protocol_sha256=digest,
        evaluation_plan_sha256=evaluation_plan_digest(plan),
        **{
            f"{key}_manifest_sha256": getattr(plan, f"{key}_manifest").sha256
            for key in ("source_inventory", "anchor", "official_query", "primary_query")
        },
        final_run_set_sha256=final_run_set_digest(runs),
        recorded_by="test fixture",
        recorded_at=datetime(2026, 10, 3, tzinfo=UTC),
        locked_at=datetime(2026, 10, 3, tzinfo=UTC),
        design_lock_sha256=authorization.design_lock_sha256,
        selection_authorization_sha256=sha256_file(selection_path),
        artifact_root_registry_sha256=sha256_file(registry),
    )
    for relative, model in (
        (protocol.test_access.evaluation_plan_relative_path, plan),
        (protocol.test_access.final_run_set_relative_path, runs),
        (protocol.test_access.protocol_lock_relative_path, lock),
    ):
        write_immutable_json(root / relative, model.model_dump(mode="json"))
    return SimpleNamespace(
        root=root,
        protocol=protocol,
        plan=plan,
        runs=runs,
        lock=lock,
        authorization=authorization,
        registry=registry,
    )


def test_full_cardinality_v3_metadata_and_lock_cross_bindings(full_metadata_bundle):
    bundle = full_metadata_bundle
    receipt = validate_evaluation_manifests(
        bundle.protocol, bundle.plan, bundle.root, check_source_files=False
    )
    assert receipt.source_file_count == 2
    assert receipt.source_files_verified is False
    plan = load_evaluation_plan(
        bundle.root / bundle.protocol.test_access.evaluation_plan_relative_path
    )
    runs = load_final_run_set(
        bundle.root / bundle.protocol.test_access.final_run_set_relative_path
    )
    lock = load_protocol_lock(
        bundle.root / bundle.protocol.test_access.protocol_lock_relative_path
    )
    assert (
        isinstance(plan, V3EvaluationPlan)
        and isinstance(runs, V3FinalRunSet)
        and isinstance(lock, V3FinalLock)
    )
    assert verify_protocol_lock(bundle.protocol, lock, plan, runs) == protocol_digest(
        bundle.protocol
    )
    assert [
        plan.source_inventory_manifest.sample_count,
        plan.anchor_manifest.sample_count,
        plan.official_query_manifest.sample_count,
        plan.primary_query_manifest.sample_count,
    ] == [113945, 20, 18924, 18884]


@pytest.mark.parametrize(
    "field",
    [
        "protocol_sha256",
        "evaluation_plan_sha256",
        "source_inventory_manifest_sha256",
        "anchor_manifest_sha256",
        "official_query_manifest_sha256",
        "primary_query_manifest_sha256",
        "final_run_set_sha256",
    ],
)
def test_final_lock_rejects_each_broken_cross_binding(full_metadata_bundle, field):
    bundle = full_metadata_bundle
    lock = V3FinalLock.model_validate({**bundle.lock.model_dump(), field: "f" * 64})
    with pytest.raises(ValueError):
        verify_protocol_lock(bundle.protocol, lock, bundle.plan, bundle.runs)


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "seed", "batch", "initialization"]
)
def test_v3_final_metadata_rejects_incomplete_or_unpaired_heads(
    full_metadata_bundle, mutation
):
    payload = deepcopy(full_metadata_bundle.runs.model_dump(mode="json"))
    if mutation == "missing":
        payload["runs"].pop()
    elif mutation == "duplicate":
        payload["runs"][-1] = payload["runs"][0]
    elif mutation == "seed":
        payload["runs"][-1]["seed"] = 31
    else:
        payload["runs"][-1][
            f"{mutation if mutation == 'initialization' else 'batch_plan'}_sha256"
        ] = "f" * 64
    with pytest.raises(ValueError):
        V3FinalRunSet.model_validate(payload)


@pytest.mark.parametrize(
    "mutation", [None, "design", "selection", "registry", "chronology"]
)
def test_v3_final_stage_dispatch_keeps_binding_checks_real(
    full_metadata_bundle, tmp_path, monkeypatch, mutation
):
    """Only prior admission and heavy source/head inspection are test seams."""
    bundle = full_metadata_bundle
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(bundle.root))
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    selected_path = bundle.root / bundle.runs.selection_evidence.relative_path
    monkeypatch.setattr(
        "pose_embed.protocol_v3_campaign.require_selected_configurations",
        lambda _: SimpleNamespace(recorded_at=bundle.runs.selection_locked_at),
    )
    monkeypatch.setattr(
        "pose_embed.protocol_v3_campaign.selected_configs_path",
        lambda _: selected_path,
    )
    monkeypatch.setattr(
        "pose_embed.protocol_v3._registry_path", lambda: bundle.registry
    )
    monkeypatch.setattr(
        "pose_embed.protocol.validate_evaluation_manifests", lambda *a, **k: None
    )
    visited = []
    monkeypatch.setattr(
        "pose_embed.protocol.validate_final_run_artifacts",
        lambda _, run, *a, **k: visited.append((run.method, run.seed)),
    )
    lock_path = bundle.root / bundle.protocol.test_access.protocol_lock_relative_path
    original = lock_path.read_bytes()
    selection_path = (
        bundle.root / bundle.protocol.test_access.selection_authorization_relative_path
    )
    original_selection = selection_path.read_bytes()
    runs_path = bundle.root / bundle.protocol.test_access.final_run_set_relative_path
    original_runs = runs_path.read_bytes()
    payload = bundle.lock.model_dump(mode="json")
    if mutation in {"design", "selection", "registry"}:
        key = {
            "design": "design_lock_sha256",
            "selection": "selection_authorization_sha256",
            "registry": "artifact_root_registry_sha256",
        }[mutation]
        payload[key] = "f" * 64
    elif mutation == "chronology":
        selection_path.write_text(
            bundle.authorization.model_copy(
                update={"recorded_at": bundle.runs.selection_locked_at}
            ).model_dump_json()
        )
        changed_runs = V3FinalRunSet.model_validate(
            {
                **bundle.runs.model_dump(),
                "selection_authorization_sha256": sha256_file(selection_path),
            }
        )
        runs_path.write_text(changed_runs.model_dump_json())
        payload["selection_authorization_sha256"] = sha256_file(selection_path)
        payload["final_run_set_sha256"] = final_run_set_digest(changed_runs)
    try:
        lock_path.write_text(json.dumps(payload))
        if mutation is None:
            assert require_v3_final_authorization(bundle.protocol) == bundle.lock
            assert set(visited) == {
                (method, seed)
                for method in bundle.plan.methods
                for seed in bundle.plan.seeds
            }
            assert len(visited) == 9
        else:
            with pytest.raises(ValueError, match="bindings or chronology"):
                require_v3_final_authorization(bundle.protocol)
            assert not visited
    finally:
        lock_path.write_bytes(original)
        selection_path.write_bytes(original_selection)
        runs_path.write_bytes(original_runs)
