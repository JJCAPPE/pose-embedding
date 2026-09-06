from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def protocol_path(repository_root: Path) -> Path:
    return repository_root / "configs" / "protocol.v1.yaml"


@pytest.fixture
def evaluation_plan_path(repository_root: Path) -> Path:
    return repository_root / "configs" / "evaluation-plan.v1.yaml"
