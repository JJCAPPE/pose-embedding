import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).parents[2] / "scripts/operations/week5_additional_checks.py"
    spec = importlib.util.spec_from_file_location("additional_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_successor_supplemental_checker_binds_full_release_and_source(monkeypatch):
    module = script()
    monkeypatch.setattr(module, "require_clean_repository", lambda: "a" * 40)
    bindings = module.execution_binding("a" * 40, "execution-r2")
    assert set(bindings) == {
        "scripts/operations/week5_additional_checks.py",
        "scripts/run_v3_execution.py",
    }
    with pytest.raises(ValueError, match="full reviewed"):
        module.execution_binding("aaaaaaa", "execution-r2")
    with pytest.raises(ValueError, match="checkout differs"):
        module.execution_binding("b" * 40, "execution-r2")
    monkeypatch.setattr(
        module,
        "require_clean_repository",
        lambda: "731938a157be575ee433d6939876f8ca0b95e459",
    )
    with pytest.raises(ValueError, match="new reviewed release"):
        module.execution_binding(
            "731938a157be575ee433d6939876f8ca0b95e459", "execution-r2"
        )


def test_successor_geometry_destination_stays_under_its_lock(tmp_path):
    module = script()
    output = module.geometry_destination(
        tmp_path,
        "study-v3/revisions/execution-r2/locks/protocol.v3.json",
        Path("fixture"),
    )
    assert output == tmp_path / "study-v3/revisions/execution-r2/locks/geometry/fixture"
