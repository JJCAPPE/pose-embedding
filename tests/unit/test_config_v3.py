"""Protocol mutations cannot silently adopt settings from another study."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from pose_embed.config import (
    ProtocolConfig,
    load_experiment,
    load_protocol,
    validate_experiment_against_protocol,
)
from pose_embed.config_v3 import ArtifactBinding, ProtocolV3Config
from pose_embed.protocol import protocol_digest
from pose_embed.protocol_v3 import (
    COUNTS,
    V3DesignLock,
    V3EvaluationPlan,
    _bound_file,
    _validate_design_inputs,
    require_v3_design,
    v3_design_code_hashes,
)
from pose_embed.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[2]


def template():
    return yaml.safe_load((ROOT / "configs/protocol.v3.yaml").read_text())


def test_explicit_dispatch_preserves_historical_protocol():
    v1 = load_protocol(ROOT / "configs/protocol.v1.yaml")
    v3 = load_protocol(ROOT / "configs/protocol.v3.yaml")
    assert isinstance(v1, ProtocolConfig)
    assert isinstance(v3, ProtocolV3Config)
    assert (
        protocol_digest(v1)
        == "c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f"
    )
    assert v1.objectives.contextual.positive_margin == 0.9
    assert v3.objectives.contextual.positive_margin == 0.75
    assert v1.training.epochs == 50
    assert v3.training.epochs == 20
    assert len(v1.training.tuning_grid) == 6
    assert len(v3.training.tuning_grid) == 3


@pytest.mark.parametrize(
    "options", [{"require_locked": True}, {"lock_path": "fake.json"}]
)
def test_v3_final_lock_cannot_fall_through_to_legacy_authorization(
    options, monkeypatch
):
    import pose_embed.protocol as module

    def legacy_loader_must_not_run(*_args, **_kwargs):
        raise AssertionError("v3 final authorization reached a legacy lock loader")

    monkeypatch.setattr(module, "load_protocol_lock", legacy_loader_must_not_run)
    with pytest.raises(ValueError, match="v3 final authorization is unavailable"):
        module.verify_protocol(ROOT / "configs/protocol.v3.yaml", **options)


@pytest.mark.parametrize(
    ("keys", "value"),
    [
        (("objectives", "core"), ["contrastive", "contextual"]),
        (("objectives", "contextual", "positive_margin"), 0.9),
        (("objectives", "contextual", "contextual_weight"), 0.2),
        (("objectives", "contextual", "target_mean_similarity"), 0.0),
        (("objectives", "contextual_target"), "algorithm_1_printed_target"),
        (("objectives", "reciprocal_denominator"), "detached"),
        (("training", "epochs"), 10),
        (("training", "seeds"), [7, 17, 30]),
        (
            ("training", "tuning_grid"),
            [{"learning_rate": 0.0003, "weight_decay": 0.0001}],
        ),
        (
            ("training", "final_selection_tie_breakers"),
            ["higher_mrr", "lower_seed_standard_deviation"],
        ),
        (("training", "pilot", "snapshot_epochs"), [5, 10, 20]),
        (("training", "pilot", "selection_eligible"), True),
        (("training", "weight_decay_scope"), "weight_only"),
        (("dataset", "development_validation_actions"), list(range(3, 120, 6))),
        (("dataset", "exclude_anchor_performance_views_from_primary_queries"), False),
        (("batch", "physical_batch_size"), 64),
        (
            ("corruptions", "seed_derivation"),
            "sha256_protocol_id_sample_id_family_canonical_severity_first_63_bits",
        ),
        (("corruptions", "nested_severities"), False),
        (("corruptions", "joint_mask_counts"), [3, 6, 9]),
        (("analysis", "bootstrap_stratification"), "global_groups"),
        (("analysis", "resample_seeds"), True),
        (("analysis", "secondary_methods"), ["supcon", "multi_similarity_with_miner"]),
        (("test_access", "protocol_lock_relative_path"), "locks/protocol-lock.v1.json"),
        (("provenance", "development_anchor_prefix"), "protocol-v3|dev-anchor-v1|"),
        (("status",), "resolved"),
    ],
)
def test_scientific_design_mutations_are_rejected(keys, value):
    payload = template()
    target = payload
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    with pytest.raises(ValueError):
        ProtocolV3Config.model_validate(payload)


def test_all_twenty_seven_configs_match_v3_and_not_v1():
    v3 = load_protocol(ROOT / "configs/protocol.v3.yaml")
    v1 = load_protocol(ROOT / "configs/protocol.v1.yaml")
    configs = sorted((ROOT / "configs/experiments/v3").glob("*.yaml"))
    assert len(configs) == 27
    matrix = set()
    for path in configs:
        config = load_experiment(path)
        validate_experiment_against_protocol(config, v3)
        matrix.add((config.objective, config.learning_rate, config.seed))
        with pytest.raises(ValueError):
            validate_experiment_against_protocol(config, v1)
    assert len(matrix) == 27


def test_template_never_authorizes_caches_or_pilots():
    with pytest.raises(ValueError, match="unresolved"):
        require_v3_design(load_protocol(ROOT / "configs/protocol.v3.yaml"))


@pytest.mark.parametrize(
    "path", ["../escape", "/outside", "a//b", "a/./b", "a/../b", r"a\b"]
)
def test_bound_artifact_paths_cannot_escape_or_alias(path):
    with pytest.raises(ValueError):
        ArtifactBinding(relative_path=path, sha256="a" * 64)


def test_v3_evaluation_matrix_requires_exact_seeds_and_roles():
    payload = yaml.safe_load((ROOT / "configs/evaluation-plan.v3.yaml").read_text())
    plan = V3EvaluationPlan.model_validate(payload)
    assert plan.expected_rows == 180
    for key, value in [
        ("seeds", [7, 17, 31]),
        ("query_roles", ["query_clean"]),
        ("expected_rows", 90),
        ("plan_id", "final-evaluation-v1"),
    ]:
        changed = deepcopy(payload)
        changed[key] = value
        with pytest.raises(ValueError):
            V3EvaluationPlan.model_validate(changed)


def test_design_authorization_rejects_wrong_checkpoint_before_source_loading(
    tmp_path, monkeypatch
):
    binding = {"relative_path": "input.json", "sha256": "a" * 64}
    payload = template()
    payload.update(
        status="resolved",
        preparation={
            "auxiliary_container": binding,
            "fallback_evidence": binding,
            "fallback_value": 1.0,
            "source_inventory": binding,
            "identities": binding,
            "encoder_checkpoint_sha256": "a" * 64,
            "upstream_sha256": {
                key: "a" * 64
                for key in ("upstream_sha256", "config_sha256", "license_sha256")
            },
        },
    )
    protocol = ProtocolV3Config.model_validate(payload)
    lock = V3DesignLock(
        schema_version=3,
        kind="v3_auxiliary_design_and_pilot_authorization",
        protocol_sha256=protocol_digest(protocol),
        protocol_relative_path="study-v3/locks/protocol.v3.json",
        recorded_at=datetime.now(UTC),
        recorded_by="test",
        manifests={key: binding for key in COUNTS},
        code_sha256={"src/example.py": "a" * 64},
        artifact_root_registry_sha256="a" * 64,
        pilot=protocol.training.pilot,
        epochs=20,
        novel_access_authorized=False,
    )
    monkeypatch.setenv("POSE_EMBED_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "pose_embed.models.motionbert.verify_motionbert_assets",
        lambda _: {"checkpoint_sha256": "b" * 64},
    )
    with pytest.raises(ValueError, match="encoder asset hashes"):
        _validate_design_inputs(protocol, lock, tmp_path)


def test_bound_evidence_detects_modification_and_symlink_escape(tmp_path):
    root = tmp_path / "artifacts"
    root.mkdir()
    source = root / "evidence.json"
    source.write_text('{"status":"prepared"}')
    binding = ArtifactBinding(relative_path=source.name, sha256=sha256_file(source))
    assert _bound_file(root, binding) == source
    source.write_text('{"status":"changed"}')
    with pytest.raises(ValueError, match="hash mismatch"):
        _bound_file(root, binding)
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    escaped = root / "escape.json"
    escaped.symlink_to(outside)
    with pytest.raises(ValueError, match="escaping"):
        _bound_file(
            root,
            ArtifactBinding(relative_path=escaped.name, sha256=sha256_file(outside)),
        )


def test_design_freezes_pilot_math_and_evaluator_before_caches():
    paths = set(v3_design_code_hashes())
    assert {
        "src/pose_embed/training/runner.py",
        "src/pose_embed/training/sampler.py",
        "src/pose_embed/evaluation/metrics.py",
    } <= paths
    assert {
        str(path.relative_to(ROOT))
        for path in (ROOT / "src/pose_embed/losses").glob("*.py")
    } <= paths
    assert "src/pose_embed/protocol_v3_campaign.py" not in paths
