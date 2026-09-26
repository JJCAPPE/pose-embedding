from __future__ import annotations

import json
from pathlib import Path

import pytest

from pose_embed.benchmark.episodes import load_episode
from pose_embed.config import load_protocol
from pose_embed.data.inventory import NTUInventoryRecord, build_split_manifests
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.protocol import protocol_digest
from pose_embed.provenance import sha256_file


@pytest.fixture
def retrieval_bundle(
    tmp_path: Path, protocol_path: Path, monkeypatch: pytest.MonkeyPatch
):
    protocol = load_protocol(protocol_path)
    sample_ids = [
        f"S001C{camera:03d}P{performer:03d}R001A{action:03d}"
        for action in range(1, 121)
        for performer in (1, 2)
        for camera in (1, 2)
    ] + list(protocol.dataset.official_one_shot_exemplars)
    inventory = []
    for index, sample_id in enumerate(sample_ids):
        sample = parse_ntu_sample_id(sample_id)
        inventory.append(
            NTUInventoryRecord(
                sample_id=sample_id,
                annotation_index=index,
                setup=sample.setup,
                camera=sample.camera,
                performer=sample.performer,
                repetition=sample.repetition,
                action=sample.action,
                label=sample.action - 1,
                pose_track_count=1,
                nonempty_track_count=1,
                total_frames=100,
                keypoint_shape=(1, 100, 17, 2),
                keypoint_score_shape=(1, 100, 17),
                image_shape=(1080, 1920),
                original_shape=(1080, 1920),
            )
        )
    # The fixture relaxes only the production count; it still covers all classes.
    protocol = protocol.model_copy(
        update={
            "dataset": protocol.dataset.model_copy(
                update={"expected_source_sample_count": len(inventory)}
            )
        }
    )
    monkeypatch.setattr(
        "pose_embed.benchmark.episodes.load_protocol", lambda _: protocol
    )
    manifests = build_split_manifests(inventory, protocol)
    files = {}
    for filename, rows in {"source-inventory.jsonl": inventory, **manifests}.items():
        path = tmp_path / filename
        path.write_text("".join(row.model_dump_json() + "\n" for row in rows))
        files[filename] = {"records": len(rows), "sha256": sha256_file(path)}
    contract = protocol.dataset.source_contract
    bundle = tmp_path / "manifest-set.json"
    bundle.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_sha256": protocol_digest(protocol),
                "source": {
                    key: value
                    for key, value in contract.model_dump().items()
                    if key not in {"missing_sample_count", "nominal_capture_count"}
                },
                "protocol_count": {
                    "usable_annotations": len(inventory),
                    "official_missing_skeletons": contract.missing_sample_count,
                    "nominal_captures": contract.nominal_capture_count,
                    "locked_expected_rows": len(inventory),
                    "amendment_required": False,
                },
                "files": files,
            }
        )
    )
    return bundle, protocol, manifests


@pytest.mark.parametrize(
    ("split", "filename"),
    [
        ("development_validation", "development-validation.jsonl"),
        ("novel", "official-novel.jsonl"),
    ],
)
def test_episode_preserves_verified_parent_order_without_reading_poses(
    retrieval_bundle, split: str, filename: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, protocol, manifests = retrieval_bundle
    monkeypatch.setattr(
        "pose_embed.data.inventory.pickle.load",
        lambda _: pytest.fail("episode creation must not read poses"),
    )
    first = load_episode(bundle, split)
    assert first == load_episode(bundle, split)
    assert first["records"] == manifests[filename]
    metadata = first["metadata"]
    assert metadata["sample_ids"] == [row.sample_id for row in manifests[filename]]
    assert metadata["sample_count"] == len(manifests[filename])
    assert metadata["parent_protocol_sha256"] == protocol_digest(protocol)
    assert metadata["manifest_set_sha256"] == sha256_file(bundle)
    assert metadata["parent_manifest_sha256"] == sha256_file(bundle.parent / filename)
    assert (
        metadata["policy"]["exclusion"] == "self_and_all_synchronized_performance_views"
    )
    json.dumps(metadata, allow_nan=False)


def test_novel_pool_includes_all_official_anchors(retrieval_bundle) -> None:
    bundle, protocol, _ = retrieval_bundle
    episode = load_episode(bundle, "novel")
    assert set(protocol.dataset.official_one_shot_exemplars) <= set(
        episode["metadata"]["sample_ids"]
    )
    assert set(episode["metadata"]["actions"]).isdisjoint(
        protocol.dataset.development_validation_actions
    )


@pytest.mark.parametrize("changed", ["manifest", "contract", "count"])
def test_changed_parent_bundle_is_rejected(retrieval_bundle, changed: str) -> None:
    bundle, _, _ = retrieval_bundle
    if changed == "manifest":
        path = bundle.parent / "development-validation.jsonl"
        path.write_text(path.read_text() + "\n")
    else:
        document = json.loads(bundle.read_text())
        if changed == "contract":
            document["protocol_sha256"] = "0" * 64
        else:
            document["files"]["development-validation.jsonl"]["records"] -= 1
        bundle.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="checksum|protocol|count"):
        load_episode(bundle, "development_validation")


def test_other_splits_are_rejected_before_loading_any_data(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="episode split"):
        load_episode(tmp_path / "absent.json", "final_train")
