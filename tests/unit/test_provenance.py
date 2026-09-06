from __future__ import annotations

from pathlib import Path

import pytest

from pose_embed.provenance import (
    capture_provenance,
    require_path_within,
    write_immutable_json,
)


def test_run_evidence_is_create_only(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    write_immutable_json(path, {"run": 1})

    with pytest.raises(ValueError, match="refusing to overwrite"):
        write_immutable_json(path, {"run": 2})


def test_provenance_hashes_inputs(repository_root: Path, tmp_path: Path) -> None:
    source = tmp_path / "input.bin"
    source.write_bytes(b"stable input")

    provenance = capture_provenance(
        command="fixture",
        configuration={"seed": 7},
        inputs=[source],
        repository=repository_root,
    )

    assert provenance["git_sha"]
    assert len(provenance["inputs"][str(source)]) == 64
    assert provenance["configuration"] == {"seed": 7}


def test_scientific_output_path_must_remain_under_artifact_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts"
    assert (
        require_path_within(root / "runs/one", root, label="scientific output")
        == (root / "runs/one").resolve()
    )
    with pytest.raises(ValueError, match="POSE_EMBED_ARTIFACT_ROOT"):
        require_path_within(
            tmp_path / "tracked/head.pt",
            root,
            label="scientific output",
        )
