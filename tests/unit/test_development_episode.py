from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import pose_embed.data.development as development
from pose_embed.config import ProtocolConfig, load_protocol
from pose_embed.data.development import (
    GALLERY_FILENAME,
    QUERY_FILENAME,
    REPORT_FILENAME,
    build_development_episode,
    generate_development_episode,
    validate_development_episode,
)
from pose_embed.data.inventory import NTUInventoryRecord, build_split_manifests
from pose_embed.data.manifest import ManifestRecord, load_manifest
from pose_embed.data.ntu import parse_ntu_sample_id
from pose_embed.evaluation.runner import _validate_identities
from pose_embed.validation_proofs import validation_session


def _validation_records(protocol: ProtocolConfig) -> list[ManifestRecord]:
    return [
        ManifestRecord(
            sample_id=f"S001C{camera:03d}P{performer:03d}R001A{action:03d}",
            split="development_validation",
        )
        for action in reversed(protocol.dataset.development_validation_actions)
        for performer in (1, 2)
        for camera in (3, 1, 2)
    ]


def _write_manifest(path: Path, rows: list[ManifestRecord]) -> None:
    path.write_text("".join(row.model_dump_json() + "\n" for row in rows))


def test_development_selection_is_result_blind_and_preserves_source_order(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    rows = _validation_records(protocol)
    gallery, queries, exclusions = build_development_episode(rows, protocol)
    chosen = {
        min(
            (row.sample_id for row in rows if row.ntu.action == action),
            key=lambda value: hashlib.sha256(
                f"protocol-v1|dev-anchor-v1|{value}".encode()
            ).hexdigest(),
        )
        for action in protocol.dataset.development_validation_actions
    }

    assert [row for row in rows if row.sample_id in chosen] == gallery
    performances = {row.ntu.performance_id for row in gallery}
    assert [
        row for row in rows if row.ntu.performance_id not in performances
    ] == queries
    assert len(gallery) == 20
    assert len(queries) == 60
    assert len(exclusions) == 60
    assert all(not row.is_anchor for row in gallery)
    assert sum(row["reason"] == "gallery_sample" for row in exclusions) == 20
    assert set(chosen).isdisjoint(row.sample_id for row in queries)
    reversed_gallery, _, _ = build_development_episode(list(reversed(rows)), protocol)
    assert {row.sample_id for row in reversed_gallery} == chosen


def test_development_selection_rejects_missing_class_duplicate_and_empty_queries(
    protocol_path: Path,
) -> None:
    protocol = load_protocol(protocol_path)
    rows = _validation_records(protocol)
    with pytest.raises(ValueError, match="all validation actions"):
        build_development_episode(rows[6:], protocol)
    with pytest.raises(ValueError, match="duplicate"):
        build_development_episode([*rows, rows[0]], protocol)
    with pytest.raises(ValueError, match="independent queries"):
        build_development_episode(
            [row for row in rows if row.ntu.performer == 1], protocol
        )
    with pytest.raises(ValueError, match="development_validation records"):
        build_development_episode(
            [
                ManifestRecord(
                    sample_id="S001C001P001R001A003", split="development_train"
                )
            ],
            protocol,
        )


@pytest.fixture
def episode_bundle(
    protocol_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, ProtocolConfig]:
    protocol = load_protocol(protocol_path)
    sample_ids = [
        f"S001C{camera:03d}P{performer:03d}R001A{action:03d}"
        for action in range(1, 121)
        for performer in (1, 2)
        for camera in (1, 2, 3)
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
    # Only this tiny fixture relaxes the production inventory-count requirement.
    protocol = protocol.model_copy(
        update={
            "dataset": protocol.dataset.model_copy(
                update={"expected_source_sample_count": len(inventory)}
            )
        }
    )
    monkeypatch.setattr("pose_embed.data.development.load_protocol", lambda _: protocol)
    monkeypatch.setenv("POSE_EMBED_ARTIFACT_ROOT", str(tmp_path))
    (tmp_path / "source-inventory.jsonl").write_text(
        "".join(row.model_dump_json() + "\n" for row in inventory)
    )
    manifest = tmp_path / "development-validation.jsonl"
    _write_manifest(
        manifest,
        build_split_manifests(inventory, protocol)["development-validation.jsonl"],
    )
    return manifest, tmp_path / "episode", protocol


def test_development_episode_is_immutable_and_independently_verifiable(
    episode_bundle: tuple[Path, Path, ProtocolConfig], protocol_path: Path
) -> None:
    manifest, output, protocol = episode_bundle
    report = generate_development_episode(manifest, output, protocol_path)
    assert (
        validate_development_episode(
            output / REPORT_FILENAME,
            protocol=protocol,
            manifest_path=output / GALLERY_FILENAME,
            role="gallery_clean",
        )
        == report
    )
    with pytest.raises(ValueError, match="already exists"):
        generate_development_episode(manifest, output, protocol_path)
    with pytest.raises(ValueError, match="differs from its development episode role"):
        validate_development_episode(
            output / REPORT_FILENAME,
            protocol=protocol,
            manifest_path=output / QUERY_FILENAME,
            role="gallery_clean",
        )


@pytest.mark.parametrize(
    "changed", ["source", "inventory", "query", "report", "missing"]
)
def test_development_episode_rejects_changed_or_partial_evidence(
    episode_bundle: tuple[Path, Path, ProtocolConfig], protocol_path: Path, changed: str
) -> None:
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    if changed in {"source", "inventory"}:
        path = (
            manifest
            if changed == "source"
            else manifest.parent / "source-inventory.jsonl"
        )
        path.write_text(path.read_text() + "\n")
    elif changed == "query":
        _write_manifest(
            output / QUERY_FILENAME,
            list(reversed(load_manifest(output / QUERY_FILENAME))),
        )
    elif changed == "report":
        path = output / REPORT_FILENAME
        report = json.loads(path.read_text())
        report["selection_prefix"] = "choose-after-scores"
        path.write_text(json.dumps(report))
    else:
        (output / GALLERY_FILENAME).unlink()
    with pytest.raises(ValueError, match="development episode|manifest does not exist"):
        validate_development_episode(output / REPORT_FILENAME, protocol=protocol)


@pytest.mark.parametrize(
    "ledger_name",
    ["locks/test-opening.v1.json", "benchmark-v2/locks/test-opening.json"],
)
def test_development_episode_rejects_source_subset_and_opened_test(
    episode_bundle: tuple[Path, Path, ProtocolConfig],
    protocol_path: Path,
    ledger_name: str,
) -> None:
    manifest, output, protocol = episode_bundle
    rows = load_manifest(manifest)
    _write_manifest(manifest, rows[:-1])
    with pytest.raises(ValueError, match="complete ordered validation manifest"):
        generate_development_episode(manifest, output, protocol_path)
    _write_manifest(manifest, rows)
    ledger = manifest.parent / ledger_name
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("{}")
    with pytest.raises(ValueError, match="after test opening"):
        generate_development_episode(manifest, output, protocol_path)


@pytest.mark.parametrize(
    ("query_id", "message"),
    [
        ("S001C001P001R001A002", "identities must be disjoint"),
        ("S001C002P001R001A002", "share a gallery performance"),
    ],
)
def test_development_evaluator_rejects_identity_and_synchronized_view_overlap(
    protocol_path: Path, tmp_path: Path, query_id: str, message: str
) -> None:
    gallery = tmp_path / "gallery.jsonl"
    query = tmp_path / "query.jsonl"
    _write_manifest(
        gallery,
        [
            ManifestRecord(
                sample_id="S001C001P001R001A002", split="development_validation"
            )
        ],
    )
    _write_manifest(
        query, [ManifestRecord(sample_id=query_id, split="development_validation")]
    )
    with pytest.raises(ValueError, match=message):
        _validate_identities(
            protocol=load_protocol(protocol_path),
            gallery_manifest_path=gallery,
            query_manifest_path=query,
            mode="development",
        )


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
def test_episode_reconstruction_reuses_success_only_within_one_command(
    episode_bundle, protocol_path, monkeypatch
):
    manifest, output, protocol = episode_bundle
    expected = generate_development_episode(manifest, output, protocol_path)
    original = development._complete_validation_records
    calls = []

    def reconstruct(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(development, "_complete_validation_records", reconstruct)
    arguments = dict(protocol=protocol, scientific_use_allowed=False)
    with validation_session():
        first = validate_development_episode(output / REPORT_FILENAME, **arguments)
        first["exclusions"].clear()
        assert (
            validate_development_episode(output / REPORT_FILENAME, **arguments)
            == expected
        )
        assert len(calls) == 1
        with validation_session(fresh=True):
            assert (
                validate_development_episode(output / REPORT_FILENAME, **arguments)
                == expected
            )
    with validation_session():
        assert (
            validate_development_episode(output / REPORT_FILENAME, **arguments)
            == expected
        )
    assert len(calls) == 3


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
@pytest.mark.parametrize(
    "dependency", ["report", "source", "inventory", "gallery", "query"]
)
@pytest.mark.parametrize("mutation", ["same_size", "missing", "retarget"])
def test_episode_reuse_rejects_every_changed_input(
    episode_bundle, protocol_path, dependency, mutation
):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    paths = dict(
        report=output / REPORT_FILENAME,
        source=manifest,
        inventory=manifest.parent / "source-inventory.jsonl",
        gallery=output / GALLERY_FILENAME,
        query=output / QUERY_FILENAME,
    )
    with pytest.raises(ValueError), validation_session():
        validate_development_episode(
            output / REPORT_FILENAME, protocol=protocol, scientific_use_allowed=False
        )
        path = paths[dependency]
        content = path.read_bytes()
        if mutation == "same_size":
            position = content.index(b"0")
            path.write_bytes(content[:position] + b"1" + content[position + 1 :])
        else:
            path.unlink()
            if mutation == "retarget":
                other = path.with_suffix(".replacement")
                other.write_bytes(content)
                path.symlink_to(other)
        validate_development_episode(
            output / REPORT_FILENAME, protocol=protocol, scientific_use_allowed=False
        )


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
@pytest.mark.parametrize(
    "dependency",
    [
        "data/development.py",
        "data/inventory.py",
        "data/manifest.py",
        "data/ntu.py",
        "config.py",
        "config_v3.py",
        "protocol.py",
        "provenance.py",
    ],
)
def test_episode_reuse_binds_transitive_source(
    episode_bundle, protocol_path, dependency, monkeypatch, tmp_path
):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    package = Path(development.__file__).resolve().parents[1]
    copied = tmp_path / "source"
    for name in [
        "data/development.py",
        "data/inventory.py",
        "data/manifest.py",
        "data/ntu.py",
        "config.py",
        "config_v3.py",
        "protocol.py",
        "provenance.py",
    ]:
        path = copied / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((package / name).read_bytes())
    monkeypatch.setattr(development, "__file__", str(copied / "data/development.py"))
    with pytest.raises(ValueError, match="dependency"), validation_session():
        validate_development_episode(
            output / REPORT_FILENAME, protocol=protocol, scientific_use_allowed=False
        )
        path = copied / dependency
        content = path.read_bytes()
        path.write_bytes(b"#" + content[1:])
        validate_development_episode(
            output / REPORT_FILENAME, protocol=protocol, scientific_use_allowed=False
        )


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
def test_episode_reuse_keeps_roles_and_protocol_fresh(episode_bundle, protocol_path):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    arguments = dict(protocol=protocol, scientific_use_allowed=False)
    with validation_session():
        validate_development_episode(output / REPORT_FILENAME, **arguments)
        for selected, role in [
            (QUERY_FILENAME, "gallery_clean"),
            (GALLERY_FILENAME, None),
            (None, "query_clean"),
        ]:
            with pytest.raises(ValueError, match="role"):
                validate_development_episode(
                    output / REPORT_FILENAME,
                    **arguments,
                    manifest_path=output / selected if selected else None,
                    role=role,
                )
        for selected, role in [
            (GALLERY_FILENAME, "gallery_clean"),
            (QUERY_FILENAME, "query_clean"),
        ]:
            validate_development_episode(
                output / REPORT_FILENAME,
                **arguments,
                manifest_path=output / selected,
                role=role,
            )
        changed = protocol.model_copy(update={"protocol_id": "changed"})
        with pytest.raises(ValueError, match="hashes or selection"):
            validate_development_episode(
                output / REPORT_FILENAME, protocol=changed, scientific_use_allowed=False
            )


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
def test_episode_failed_reconstruction_is_not_reused(
    episode_bundle, protocol_path, monkeypatch
):
    manifest, output, protocol = episode_bundle
    expected = generate_development_episode(manifest, output, protocol_path)
    original = development._complete_validation_records
    calls = []

    def reconstruct(*args):
        calls.append(True)
        if len(calls) == 1:
            raise ValueError("interrupted reconstruction")
        return original(*args)

    monkeypatch.setattr(development, "_complete_validation_records", reconstruct)
    arguments = dict(protocol=protocol, scientific_use_allowed=False)
    with validation_session():
        with pytest.raises(ValueError, match="interrupted reconstruction"):
            validate_development_episode(output / REPORT_FILENAME, **arguments)
        assert (
            validate_development_episode(output / REPORT_FILENAME, **arguments)
            == expected
        )
        assert (
            validate_development_episode(output / REPORT_FILENAME, **arguments)
            == expected
        )
    assert len(calls) == 2


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
def test_episode_binds_the_report_bytes_it_parsed(
    episode_bundle, protocol_path, monkeypatch
):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    path = output / REPORT_FILENAME
    original = json.loads

    def parse_then_change(content, *args, **kwargs):
        result = original(content, *args, **kwargs)
        if isinstance(result, dict) and "source_inventory" in result:
            path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(development.json, "loads", parse_then_change)
    with pytest.raises(ValueError, match="dependency"), validation_session():
        validate_development_episode(
            path, protocol=protocol, scientific_use_allowed=False
        )


@pytest.mark.parametrize("protocol_path", [Path("configs/protocol.v3.yaml")])
def test_episode_selected_manifest_is_rechecked_before_publication(
    episode_bundle, protocol_path
):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    selected = output / "selected.jsonl"
    selected.write_bytes((output / QUERY_FILENAME).read_bytes())
    with pytest.raises(ValueError, match="dependency"), validation_session():
        validate_development_episode(
            output / REPORT_FILENAME,
            protocol=protocol,
            scientific_use_allowed=False,
            manifest_path=selected,
            role="query_clean",
        )
        selected.write_bytes(selected.read_bytes() + b" ")


@pytest.mark.parametrize(
    "protocol_path",
    [Path("configs/protocol.v1.yaml"), Path("configs/protocol.v3.yaml")],
)
def test_historical_episode_validation_remains_cold(
    episode_bundle, protocol_path, monkeypatch
):
    manifest, output, protocol = episode_bundle
    generate_development_episode(manifest, output, protocol_path)
    original = development._complete_validation_records
    calls = []

    def reconstruct(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(development, "_complete_validation_records", reconstruct)
    with validation_session():
        for _ in range(2):
            validate_development_episode(output / REPORT_FILENAME, protocol=protocol)
    assert len(calls) == 2
