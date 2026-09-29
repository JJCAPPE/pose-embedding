"""One dataset authorization boundary shared by historical and v3 commands."""

from __future__ import annotations

import functools
import json
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pose_embed.provenance import sha256_file, write_immutable_json

REGISTRY = "provenance/artifact-roots.v3.json"
REGISTRY_BINDING = "provenance/dataset-registry-binding.v3.json"
OPENING = "locks/dataset-opening.json"
LEGACY_OPENINGS = (
    "locks/test-opening.v1.json",
    "benchmark-v2/locks/test-opening.json",
    "study-v3/locks/test-opening.v3.json",
)


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"missing, unreadable or malformed {label}: {path}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"{label} must be a JSON object")
    return document


def _absolute(value: object) -> bool:
    return isinstance(value, str) and Path(value).is_absolute()


def _registry() -> tuple[Path, dict[str, Any]] | None:
    """Recover the registry from the data root or any registered artifact root."""
    raw_data = os.environ.get("POSE_EMBED_DATA_ROOT")
    if raw_data and not _absolute(raw_data):
        raise ValueError("POSE_EMBED_DATA_ROOT must be an absolute path")
    data_path = Path(raw_data).resolve() / REGISTRY if raw_data else None
    raw_artifact = os.environ.get("POSE_EMBED_ARTIFACT_ROOT")
    pointer = Path(raw_artifact).resolve() / REGISTRY_BINDING if raw_artifact else None
    binding = None
    if pointer is not None and (pointer.exists() or pointer.is_symlink()):
        binding = _read_object(pointer, "artifact-root registry binding")
        if (
            binding.get("schema_version") != 1
            or not _absolute(binding.get("registry_path"))
            or re.fullmatch(r"[0-9a-f]{64}", str(binding.get("registry_sha256")))
            is None
        ):
            raise ValueError("invalid artifact-root registry binding")
        path = Path(binding["registry_path"]).resolve()
        if raw_data and data_path != path:
            raise ValueError("data root differs from the registered dataset root")
    elif data_path is not None and (data_path.exists() or data_path.is_symlink()):
        path = data_path
    else:
        return None
    value = _read_object(path, "dataset artifact-root registry")
    if (
        value.get("schema_version") != 1
        or not _absolute(value.get("canonical_artifact_root"))
        or not _absolute(value.get("data_root"))
        or Path(value["data_root"]).resolve() / REGISTRY != path
        or not isinstance(value.get("historical_roots"), list)
        or not value["historical_roots"]
        or not isinstance(value.get("external_audits"), list)
    ):
        raise ValueError("invalid dataset artifact-root registry")
    for entry in value["historical_roots"]:
        if not isinstance(entry, dict) or not _absolute(entry.get("path")):
            raise ValueError("historical roots must be absolute")
    if binding is not None and sha256_file(path) != binding["registry_sha256"]:
        raise ValueError("dataset artifact-root registry changed after registration")
    return path, value


def canonical_artifact_root() -> Path:
    raw = os.environ.get("POSE_EMBED_ARTIFACT_ROOT")
    if not raw or not Path(raw).is_absolute():
        raise ValueError("POSE_EMBED_ARTIFACT_ROOT must be an absolute path")
    root = Path(raw).resolve()
    registry = _registry()
    if registry is not None and registry[1]["canonical_artifact_root"] != str(root):
        raise ValueError(
            "POSE_EMBED_ARTIFACT_ROOT differs from the registered dataset root"
        )
    return root


def _external_audit(path: Path) -> dict[str, Any]:
    """Validate a dated observation, never represent it as a live remote check."""
    document = _read_object(path, "external historical-root audit")
    if (
        document.get("schema_version") != 1
        or document.get("status") != "sealed"
        or not isinstance(document.get("host"), str)
        or not document["host"].strip()
        or re.fullmatch(r"[0-9a-f]{64}", str(document.get("source_inventory_sha256")))
        is None
        or not isinstance(document.get("roots"), list)
        or not document["roots"]
    ):
        raise ValueError(
            "external historical-root audit must be resolved and source-bound"
        )
    try:
        recorded = datetime.fromisoformat(document["recorded_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("external audit requires a timezone-aware timestamp") from exc
    if (
        recorded.tzinfo is None
        or recorded.utcoffset() is None
        or recorded > datetime.now(UTC)
    ):
        raise ValueError("external audit timestamp is invalid")
    paths = set()
    for entry in document["roots"]:
        if (
            not isinstance(entry, dict)
            or not _absolute(entry.get("path"))
            or entry.get("status") != "sealed"
            or entry.get("readable") is not True
            or entry["path"] in paths
        ):
            raise ValueError(
                "every external historical root must be resolved and readable"
            )
        paths.add(entry["path"])
    return document


def registered_roots(*, required: bool = False) -> tuple[Path, ...]:
    root = canonical_artifact_root()
    found = _registry()
    if found is None:
        if required:
            raise ValueError(
                "scientific access requires the historical artifact-root registry"
            )
        return (root,)
    registry_path, registry = found
    roots = tuple(Path(row["path"]).resolve() for row in registry["historical_roots"])
    if root not in roots or len(set(roots)) != len(roots):
        raise ValueError(
            "registry omits its canonical root or duplicates historical roots"
        )
    expected_binding = {
        "schema_version": 1,
        "registry_path": str(registry_path),
        "registry_sha256": sha256_file(registry_path),
    }
    for path in roots:
        if not path.is_dir() or not os.access(path, os.R_OK | os.X_OK):
            raise ValueError(f"unresolved or unreadable historical root: {path}")
        if (
            _read_object(path / REGISTRY_BINDING, "artifact-root registry binding")
            != expected_binding
        ):
            raise ValueError("historical root registry binding changed")
    # These remain timestamped observations. Later stage gates must demand a fresh
    # audit; rehashing a prior observation is not a new remote seal inspection.
    source_hashes = set()
    for audit in registry["external_audits"]:
        if not isinstance(audit, dict) or not _absolute(audit.get("path")):
            raise ValueError("external audit references must be absolute")
        evidence = Path(audit["path"])
        if sha256_file(evidence) != audit.get("sha256"):
            raise ValueError("historical external-root audit changed")
        source_hashes.add(_external_audit(evidence)["source_inventory_sha256"])
    if len(source_hashes) > 1:
        raise ValueError("external historical audits disagree on the source inventory")
    return roots


def require_dataset_unopened(*, require_registry: bool = False) -> None:
    """A namespace, malformed ledger, or legacy opening cannot reseal the data."""
    for root in registered_roots(required=require_registry):
        for relative in (OPENING, *LEGACY_OPENINGS):
            path = root / relative
            if path.exists() or path.is_symlink():
                raise ValueError(
                    f"auxiliary work is forbidden after test opening: {path}"
                )


def validate_registered_source_inventory(source_inventory_sha256: str) -> None:
    """Bind every external root observation to the actual verified source inventory."""
    registered_roots(required=True)
    found = _registry()
    assert found is not None
    for audit in found[1]["external_audits"]:
        document = _external_audit(Path(audit["path"]))
        if document["source_inventory_sha256"] != source_inventory_sha256:
            raise ValueError("external historical audit refers to a different source")


def require_no_v3_opening(*, require_registry: bool = False) -> None:
    """Legacy authorized final readers cannot bypass v3 or unreadable openings."""
    for root in registered_roots(required=require_registry):
        path = root / LEGACY_OPENINGS[2]
        if path.exists() or path.is_symlink():
            raise ValueError("legacy source access is forbidden after v3 test opening")
        path = root / OPENING
        if path.exists() or path.is_symlink():
            record = _read_object(path, "dataset opening record")
            _validate_opening_record(record)
            if record.get("protocol_version") not in {"protocol-v1", "protocol-v2"}:
                raise ValueError(
                    "legacy source access is forbidden after v3 test opening"
                )


def _validate_opening_record(record: dict[str, Any]) -> None:
    if (
        record.get("schema_version") != 1
        or record.get("protocol_version")
        not in {"protocol-v1", "protocol-v2", "protocol-v3"}
        or not isinstance(record.get("authorization"), dict)
        or not record["authorization"]
    ):
        raise ValueError("malformed dataset opening record")
    try:
        opened = datetime.fromisoformat(record["opened_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("malformed dataset opening timestamp") from exc
    if (
        opened.tzinfo is None
        or opened.utcoffset() is None
        or opened > datetime.now(UTC)
    ):
        raise ValueError("invalid dataset opening timestamp")


@contextmanager
def dataset_access(*, opening: bool = False) -> Iterator[None]:
    """Coordinate running auxiliary work and opening across all protocol versions."""
    import fcntl

    root = canonical_artifact_root()
    lock = root / "locks/dataset-access.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as stream:
        try:
            fcntl.flock(
                stream, (fcntl.LOCK_EX if opening else fcntl.LOCK_SH) | fcntl.LOCK_NB
            )
        except BlockingIOError as exc:
            raise ValueError(
                "dataset opening or auxiliary operation is active"
            ) from exc
        try:
            if not opening:
                require_dataset_unopened()
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def guarded_auxiliary(function: Callable) -> Callable:
    """Keep the dataset sealed for an entire operation; pure fixtures need no root."""

    @functools.wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> Any:
        if not os.environ.get("POSE_EMBED_ARTIFACT_ROOT"):
            return function(*args, **kwargs)
        with dataset_access():
            return function(*args, **kwargs)

    return guarded


def guarded_opening(function: Callable) -> Callable:
    @functools.wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> Any:
        with dataset_access(opening=True):
            return function(*args, **kwargs)

    return guarded


def record_dataset_opening(*, version: str, authorization: dict[str, Any]) -> dict:
    """Publish the common event first; a partial transaction can only retry itself."""
    registered_roots(required=True)
    root = canonical_artifact_root()
    destination = root / OPENING
    identity = {"protocol_version": version, "authorization": authorization}
    if destination.exists() or destination.is_symlink():
        record = _read_object(destination, "dataset opening record")
        _validate_opening_record(record)
        if {key: record.get(key) for key in identity} != identity:
            raise ValueError("dataset was opened under a different authorization")
        return record
    # Called while holding the exclusive dataset-access lock, after all locks verify.
    require_dataset_unopened(require_registry=True)
    record = {
        "schema_version": 1,
        **identity,
        "opened_at": datetime.now(UTC).isoformat(),
    }
    _validate_opening_record(record)
    write_immutable_json(destination, record)
    return record


def _publish_binding(path: Path, binding: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        if _read_object(path, "artifact-root registry binding") != binding:
            raise ValueError("refusing to replace a registered artifact-root binding")
    else:
        write_immutable_json(path, binding)


def register_artifact_roots(
    roots: list[str], *, external_audits: list[str] | None = None
) -> dict:
    """Register audited roots once and place immutable registry pointers at each."""
    raw_data = os.environ.get("POSE_EMBED_DATA_ROOT", "")
    if not Path(raw_data).is_absolute():
        raise ValueError("POSE_EMBED_DATA_ROOT must be absolute")
    root = canonical_artifact_root()
    paths = sorted({root, *(Path(value).resolve() for value in roots)}, key=str)
    for path in paths:
        if not path.is_dir() or not os.access(path, os.R_OK | os.X_OK):
            raise ValueError(f"unresolved or unreadable historical root: {path}")
        for relative in (OPENING, *LEGACY_OPENINGS):
            marker = path / relative
            if marker.exists() or marker.is_symlink():
                raise ValueError(f"historical opening requires investigation: {marker}")
        for directory, _, files in os.walk(
            path, onerror=lambda error: (_ for _ in ()).throw(error)
        ):
            for name in files:
                if "opening" in name.lower() and name.endswith(".json"):
                    raise ValueError(
                        "historical opening requires investigation: "
                        f"{Path(directory) / name}"
                    )
    audits = []
    source_hashes = set()
    for value in external_audits or []:
        path = Path(value).resolve()
        source_hashes.add(_external_audit(path)["source_inventory_sha256"])
        audits.append({"path": str(path), "sha256": sha256_file(path)})
    if len(source_hashes) > 1:
        raise ValueError("external historical audits disagree on the source inventory")
    document = {
        "schema_version": 1,
        "data_root": str(Path(raw_data).resolve()),
        "canonical_artifact_root": str(root),
        "historical_roots": [{"path": str(path)} for path in paths],
        "external_audits": audits,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    destination = Path(raw_data).resolve() / REGISTRY
    if destination.exists() or destination.is_symlink():
        existing = _read_object(destination, "dataset artifact-root registry")
        if {key: value for key, value in existing.items() if key != "recorded_at"} != {
            key: value for key, value in document.items() if key != "recorded_at"
        }:
            raise ValueError("refusing to replace an existing dataset registry")
        document = existing
    else:
        write_immutable_json(destination, document)
    binding = {
        "schema_version": 1,
        "registry_path": str(destination),
        "registry_sha256": sha256_file(destination),
    }
    for path in paths:
        _publish_binding(path / REGISTRY_BINDING, binding)
    registered_roots(required=True)
    return document
