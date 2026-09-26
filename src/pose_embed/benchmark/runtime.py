"""Immutable artifacts and common provenance for the v2 benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch

from pose_embed.benchmark.config import BenchmarkConfig, benchmark_digest, load_methods
from pose_embed.provenance import sha256_file, write_immutable_json

REPOSITORY = Path(__file__).resolve().parents[3]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def now() -> str:
    return datetime.now(UTC).isoformat()


def code_digest() -> str:
    """Bind the whole scientific package and dependency lock, not a caller list."""
    paths = sorted((REPOSITORY / "src/pose_embed").rglob("*.py"))
    return digest(
        {str(p.relative_to(REPOSITORY)): sha256_file(p) for p in paths}
        | {"uv.lock": sha256_file(REPOSITORY / "uv.lock")}
    )


def artifact_root() -> Path:
    value = os.environ.get("POSE_EMBED_ARTIFACT_ROOT")
    if not value or not Path(value).is_absolute():
        raise ValueError("POSE_EMBED_ARTIFACT_ROOT must be an absolute path")
    return Path(value).resolve() / "benchmark-v2"


def artifact_path(value: str | Path) -> Path:
    path = Path(value).resolve()
    if not path.is_relative_to(artifact_root()):
        raise ValueError(
            "v2 artifacts must be inside POSE_EMBED_ARTIFACT_ROOT/benchmark-v2"
        )
    return path


def require_unopened() -> None:
    root = artifact_root()
    if (root / "locks/test-opening.json").exists() or (
        root.parent / "locks/test-opening.v1.json"
    ).exists():
        raise ValueError(
            "training and protocol selection are forbidden after test opening"
        )


def read_json(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text())
    if not isinstance(document, dict):
        raise ValueError("expected a JSON object")
    return document


def state_digest(module: torch.nn.Module) -> str:
    return _state_digest(module.state_dict())


def _state_digest(state: dict[str, torch.Tensor]) -> str:
    sha = hashlib.sha256()
    for name, value in sorted(state.items()):
        tensor = value.detach().cpu().contiguous()
        sha.update(name.encode())
        sha.update(str((tensor.dtype, tuple(tensor.shape))).encode())
        sha.update(tensor.numpy().tobytes())
    return sha.hexdigest()


def _verified_training_records(identity: dict, config: BenchmarkConfig):
    """Resolve the full declared training partition from its verified metadata."""
    from pose_embed.config import load_protocol
    from pose_embed.motionbert_inputs import verify_manifest_bundle
    from pose_embed.protocol import protocol_digest

    paths = identity.get("input_paths", {})
    expected = {"manifest_set", "parity_evidence", "protocol", "configuration"}
    if set(paths) != expected or any(
        not isinstance(value, str) or not Path(value).is_absolute()
        for value in paths.values()
    ):
        raise ValueError("run requires complete absolute input provenance paths")
    protocol_path = Path(paths["protocol"]).resolve()
    if protocol_path != (REPOSITORY / config.input_protocol).resolve():
        raise ValueError("run input protocol path differs from its configuration")
    protocol = load_protocol(protocol_path)
    if protocol_digest(protocol) != config.input_protocol_sha256:
        raise ValueError("run input protocol no longer matches its binding")
    import yaml

    supplied_config = BenchmarkConfig.model_validate(
        yaml.safe_load(Path(paths["configuration"]).read_text())
    )
    if supplied_config != config:
        raise ValueError("run configuration file differs from its bound configuration")
    bundle = Path(paths["manifest_set"]).resolve()
    raw_root = os.environ.get("POSE_EMBED_ARTIFACT_ROOT")
    if not raw_root or not bundle.is_relative_to(Path(raw_root).resolve()):
        raise ValueError("run manifest bundle must stay inside the artifact root")
    inputs = identity.get("inputs", {})
    if (
        sha256_file(bundle) != inputs.get("manifest_set_sha256")
        or sha256_file(bundle.parent / "source-inventory.jsonl")
        != inputs.get("source_inventory_sha256")
        or sha256_file(paths["parity_evidence"]) != identity.get("parity_sha256")
    ):
        raise ValueError("run input provenance files changed")
    _, manifests = verify_manifest_bundle(protocol, bundle)
    filename = (
        "final-train.jsonl"
        if identity["stage"] == "final"
        else "development-train.jsonl"
    )
    return manifests[filename]


@lru_cache(maxsize=2)
def _reference_encoder_state(checkpoint_path: str, checkpoint_sha256: str) -> dict:
    """Read shapes once from an already hash-verified immutable pretrained file."""
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    raw_state = checkpoint.get("model_pos")
    if not isinstance(raw_state, dict) or not raw_state:
        raise ValueError("pretrained checkpoint has no encoder state")
    state = {key.removeprefix("module."): value for key, value in raw_state.items()}
    if len(state) != len(raw_state):
        raise ValueError("pretrained checkpoint has duplicate normalized state keys")
    return {
        "shapes": {key: tuple(value.shape) for key, value in state.items()},
        "initialization_sha256": _state_digest(state),
        "unused_head_sha256": _state_digest(
            {key: value for key, value in state.items() if key.startswith("head.")}
        ),
    }


@lru_cache(maxsize=2)
def _reference_encoder_parameters(data_root: str, checkpoint_sha256: str) -> tuple:
    """Read parameter identities from the verified architecture, excluding buffers."""
    from pose_embed.models.motionbert import load_frozen_encoder

    with torch.random.fork_rng(devices=[]):
        encoder, metadata = load_frozen_encoder(Path(data_root))
    if metadata["checkpoint_sha256"] != checkpoint_sha256:
        raise ValueError("pretrained encoder changed while verifying parameters")
    return tuple(name for name, _ in encoder.named_parameters())


def _expected_model_state(identity: dict, config: BenchmarkConfig) -> dict:
    from pose_embed.config import load_protocol
    from pose_embed.models.motionbert import verify_motionbert_assets

    data_root = os.environ.get("POSE_EMBED_DATA_ROOT")
    if not data_root or not Path(data_root).is_absolute():
        raise ValueError("POSE_EMBED_DATA_ROOT must be an absolute path")
    assets = verify_motionbert_assets(Path(data_root).resolve())
    if assets["checkpoint_sha256"] != identity.get("inputs", {}).get(
        "checkpoint_sha256"
    ):
        raise ValueError("pretrained encoder differs from the run input binding")
    reference = _reference_encoder_state(
        str(assets["checkpoint_path"]), str(assets["checkpoint_sha256"])
    )
    protocol = load_protocol(REPOSITORY / config.input_protocol)
    dimension = identity["method_specification"]["embedding_dimension"]
    input_dimension = protocol.encoder.representation_dimension
    if identity["method"] not in {
        "proxy_nca_pp",
        "drml",
        "mhgl",
        "hist",
        "proxy_nca_metrix",
        "proxy_anchor_metrix",
        "multi_similarity_metrix",
    }:
        input_dimension *= protocol.dataset.joints
    head_shapes = {
        "head.projection.weight": (dimension, input_dimension),
        "head.projection.bias": (dimension,),
    }
    if identity["method"] == "drml":
        from pose_embed.benchmark.drml import DRMLHead

        with torch.random.fork_rng(devices=[]):
            head = DRMLHead(input_dimension, dimension // 4)
        head_shapes = {
            "head." + key: tuple(value.shape)
            for key, value in head.state_dict().items()
        }
    if identity["method"] == "mhgl":
        from pose_embed.benchmark.mhgl import MHGLHead

        with torch.random.fork_rng(devices=[]):
            head = MHGLHead(
                local_dimension=reference["shapes"]["joints_embed.weight"][0],
                global_dimension=input_dimension,
                embedding_dimension=dimension,
            )
        head_shapes = {
            "head." + key: tuple(value.shape)
            for key, value in head.state_dict().items()
        }
    return {
        **reference,
        "encoder_parameters": _reference_encoder_parameters(
            str(Path(data_root).resolve()), str(assets["checkpoint_sha256"])
        )
        if identity["method"]
        in {"proxy_nca_pp", "hist", "drml", "proxy_nca_metrix", "s2sd", "mhgl"}
        else (),
        "model_shapes": {
            **{f"encoder.{key}": shape for key, shape in reference["shapes"].items()},
            **head_shapes,
        },
    }


def _verify_batches(
    directory: Path, identity: dict, config: BenchmarkConfig
) -> tuple[int, int]:
    from pose_embed.training.sampler import BalancedBatchSampler

    records = _verified_training_records(identity, config)
    sample_ids = [row.sample_id for row in records]
    batch = read_json(directory / "batch-plan.json")
    actions = sorted({row.ntu.action for row in records})
    mapping = {str(action): index for index, action in enumerate(actions)}
    if batch.get("sample_ids") != sample_ids or batch.get("label_mapping") != mapping:
        raise ValueError(
            "batch identities or action mapping differ "
            "from the exact training partition"
        )
    labels = [mapping[str(row.ntu.action)] for row in records]
    expected = list(
        BalancedBatchSampler(
            labels,
            classes_per_batch=config.training.classes_per_batch,
            samples_per_class=config.training.samples_per_class,
            seed=identity["seed"],
            batches_per_epoch=identity["steps"],
        )
    )
    if batch.get("steps") != expected or any(
        type(index) is not int for row in batch.get("steps", []) for index in row
    ):
        raise ValueError(
            "physical batch plan differs from its deterministic paired seed"
        )
    return len(actions), len(records)


def _verify_training_recipe(identity: dict, config: BenchmarkConfig, num_records: int):
    from pose_embed.benchmark.model import head_recipe
    from pose_embed.benchmark.training import resolve_recipe

    selection_records = num_records
    if (
        identity["method"] in {"proxy_nca_pp", "hist", "proxy_nca_metrix"}
        and identity["stage"] != "final"
    ):
        selection_records = len(
            _verified_training_records(identity | {"stage": "final"}, config)
        )
    expected = resolve_recipe(
        identity["method"],
        identity["method_specification"]["parameters"],
        config.training,
        num_records,
        selection_num_records=selection_records,
        profile=identity["stage"] == "profile",
    )
    if (
        identity.get("training_recipe") != expected
        or identity.get("optimizer") != expected["optimizer"]
        or identity.get("head_recipe") != head_recipe(identity["method"])
    ):
        raise ValueError("run head/optimizer/warmup recipe differs from its method")
    if (
        identity["stage"] != "profile"
        and identity["steps"] < expected["minimum_selected_step"]
    ):
        raise ValueError("scientific run does not complete the full warmup")
    return expected


def _verify_proxy_optimizer(
    checkpoint: dict, recipe: dict, encoder_parameters: tuple
) -> None:
    """Validate method-specific auxiliary state and named Adam moment shapes."""
    from pose_embed.benchmark.training import hist_learning_rates, phase_for_step

    step = checkpoint["selected_step"]
    phase = phase_for_step(recipe, step)
    profiling = recipe["profile_phase"] is not None
    expected = {
        "phase": phase,
        "step": step,
        "warmup_updates": 0 if profiling else min(step, recipe["warmup_steps"]),
        "main_updates": step if profiling else max(0, step - recipe["warmup_steps"]),
        "encoder_trainable": recipe["encoder_mode"] == "finetune" and phase == "main",
    }
    if checkpoint.get("training_state") != expected:
        raise ValueError("checkpoint warmup/optimizer phase state is invalid")
    optimizer = checkpoint.get("optimizer", {})
    groups = optimizer.get("param_groups", [])
    states = optimizer.get("state", {})
    hist = recipe.get("recipe") == "lim2022_cub_motion"
    group_names = (
        ["encoder", "head", "distributions", "graph"]
        if hist
        else ["encoder", "head", "proxies"]
    )
    prefixes = ["model.encoder.", "model.head."] + (
        ["criterion.loss.distributions.", "criterion.loss.graph."]
        if hist
        else ["criterion."]
    )
    if [group.get("name") for group in groups] != group_names:
        raise ValueError("checkpoint optimizer groups are invalid")
    tensors = {
        **{"model." + name: value for name, value in checkpoint["model"].items()},
        **{
            "criterion." + name: value
            for name, value in checkpoint["criterion"].items()
        },
    }
    seen_ids, seen_names = set(), set()
    for group, prefix in zip(groups, prefixes, strict=True):
        names, indices = group.get("param_names", []), group.get("params", [])
        learning_rate = (
            hist_learning_rates(recipe, step)[group["name"]]
            if hist
            else recipe["proxy_learning_rate"]
            if group["name"] == "proxies"
            else recipe["head_learning_rate"]
        )
        if group["name"] == "encoder" and not expected["encoder_trainable"]:
            learning_rate = 0.0
        if (
            len(names) != len(indices)
            or not names
            or group.get("lr") != learning_rate
            or group.get("eps") != recipe["optimizer_epsilon"]
            or group.get("weight_decay") != recipe["weight_decay"]
            or tuple(group.get("betas", [])) != (0.9, 0.999)
            or group.get("amsgrad") is not False
        ):
            raise ValueError(
                "checkpoint optimizer recipe or parameter mapping is invalid"
            )
        for name, index in zip(names, indices, strict=True):
            if (
                type(index) is not int
                or index in seen_ids
                or name in seen_names
                or name not in tensors
                or not name.startswith(prefix)
                or name.startswith("model.encoder.head.")
            ):
                raise ValueError("checkpoint optimizer parameter mapping is invalid")
            seen_ids.add(index)
            seen_names.add(name)
            state = states.get(index)
            if state is None:
                if group["name"] != "encoder" or expected["encoder_trainable"]:
                    raise ValueError(
                        "checkpoint optimizer is missing required parameter moments"
                    )
                continue
            updates = (
                step
                if hist and group["name"] != "encoder"
                else expected["main_updates"]
                if phase == "main"
                else expected["warmup_updates"]
            )
            if (
                set(state) != {"step", "exp_avg", "exp_avg_sq"}
                or not all(
                    isinstance(value, torch.Tensor) and torch.isfinite(value).all()
                    for value in state.values()
                )
                or state["step"].numel() != 1
                or state["step"].item() != updates
                or state["exp_avg"].shape != tensors[name].shape
                or state["exp_avg_sq"].shape != tensors[name].shape
                or (state["exp_avg_sq"] < 0).any()
                or (group["name"] == "encoder" and not expected["encoder_trainable"])
            ):
                raise ValueError(
                    "checkpoint optimizer moments or update count are invalid"
                )
    required = {
        name for name in tensors if name.startswith(("model.head.", "criterion."))
    } | {
        "model.encoder." + name
        for name in encoder_parameters
        if not name.startswith("head.")
    }
    if hist:
        # BatchNorm running statistics belong to the checkpoint, not Adam.
        required -= {
            "criterion.loss.graph.normalization." + key
            for key in ("running_mean", "running_var", "num_batches_tracked")
        }
    if required != seen_names or not set(states).issubset(seen_ids):
        raise ValueError("checkpoint optimizer has missing or unknown parameters")


def _verify_checkpoint_state(
    directory: Path,
    identity: dict,
    config: BenchmarkConfig,
    checkpoint: dict,
    num_classes: int,
) -> None:
    from pose_embed.benchmark.losses import build_loss

    expected = _expected_model_state(identity, config)
    model_state = checkpoint["model"]
    if set(model_state) != set(expected["model_shapes"]) or any(
        tuple(model_state[key].shape) != shape
        for key, shape in expected["model_shapes"].items()
    ):
        raise ValueError(
            "checkpoint model keys or shapes differ "
            "from MotionBERT and the declared head"
        )
    initial = read_json(directory / "initialization.json")
    if any(
        not isinstance(initial.get(key), str)
        or len(initial[key]) != 64
        or any(character not in "0123456789abcdef" for character in initial[key])
        for key in ("encoder", "head", "model", "criterion")
    ):
        raise ValueError("initialization state hashes are incomplete or malformed")
    if initial["encoder"] != expected["initialization_sha256"]:
        raise ValueError(
            "encoder initialization differs from the pretrained checkpoint"
        )
    encoder_state = {
        key.removeprefix("encoder."): value
        for key, value in model_state.items()
        if key.startswith("encoder.")
    }
    if (
        identity["track"] == "frozen"
        and _state_digest(encoder_state) != initial["encoder"]
    ):
        raise ValueError("frozen encoder state changed during training")
    if (
        _state_digest(
            {
                key: value
                for key, value in encoder_state.items()
                if key.startswith("head.")
            }
        )
        != expected["unused_head_sha256"]
    ):
        raise ValueError(
            "unused pretrained pose head changed during retrieval training"
        )
    with torch.random.fork_rng(devices=[]):
        criterion = build_loss(
            identity["method"],
            identity["method_specification"]["parameters"]
            | {
                "embedding_dimension": identity["method_specification"][
                    "embedding_dimension"
                ]
            },
            num_classes,
        )
    expected_criterion = criterion.state_dict()
    if set(checkpoint["criterion"]) != set(expected_criterion) or any(
        tuple(checkpoint["criterion"][key].shape) != tuple(value.shape)
        for key, value in expected_criterion.items()
    ):
        raise ValueError("checkpoint criterion/proxy state keys or shapes are invalid")
    if hasattr(criterion, "validate_checkpoint_state"):
        criterion.validate_checkpoint_state(
            checkpoint["criterion"],
            checkpoint["selected_step"]
            + identity["training_recipe"].get("profile_counter_offset", 0),
        )


def save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    """Publish complete checkpoints without overwriting a prior attempt."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".checkpoint-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def publish_manifest(directory: Path, identity: dict, outputs: list[str]) -> dict:
    manifest = {
        "schema_version": 2,
        "identity": identity,
        "outputs": {name: sha256_file(directory / name) for name in outputs},
        "completed_at": now(),
    }
    write_immutable_json(directory / "run-manifest.json", manifest)
    return manifest


def verify_run(directory: str | Path) -> dict:
    directory = artifact_path(directory)
    manifest = read_json(directory / "run-manifest.json")
    if manifest.get("schema_version") != 2:
        raise ValueError("invalid benchmark run schema")
    identity = manifest.get("identity", {})
    if identity.get("code_sha256") != code_digest():
        raise ValueError("benchmark code differs from the recorded run")
    config = BenchmarkConfig.model_validate(identity.get("configuration", {}))
    if benchmark_digest(config) != identity.get("benchmark_sha256"):
        raise ValueError("benchmark configuration hash mismatch")
    method = load_methods().get(identity.get("method"))
    if (
        method is None
        or method.status != "implemented"
        or (method.model_dump(mode="json") != identity.get("method_specification"))
    ):
        raise ValueError("method implementation differs from the recorded run")
    if identity.get("seed") not in config.training.seeds or (
        identity.get("track") != config.training.encoder_mode
    ):
        raise ValueError("run seed/track differs from the configuration")
    stage = identity.get("stage")
    if stage not in {"profile", "development", "final"} or (
        identity.get("scientific_use_allowed") is not (stage != "profile")
    ):
        raise ValueError("invalid run stage")
    steps = identity.get("steps")
    if (
        type(steps) is not int
        or steps < 1
        or (stage == "development" and steps != config.training.steps)
    ):
        raise ValueError("invalid run step budget")
    required = {
        "attempt.json",
        "outcome.json",
        "checkpoint.pt",
        "history.json",
        "batch-plan.json",
        "initialization.json",
        "telemetry.json",
    }
    if stage == "development":
        required.add("development-result.json")
    if not required.issubset(manifest.get("outputs", {})):
        raise ValueError("run is missing required evidence")
    for name, expected in manifest["outputs"].items():
        if Path(name).name != name or sha256_file(directory / name) != expected:
            raise ValueError(f"run evidence changed: {name}")
    if read_json(directory / "attempt.json").get("identity") != identity:
        raise ValueError("run identity differs from its immutable attempt")
    if read_json(directory / "outcome.json").get("status") != "succeeded":
        raise ValueError("run has not succeeded")
    checkpoint = torch.load(
        directory / "checkpoint.pt", map_location="cpu", weights_only=True
    )
    if checkpoint.get("identity") != identity:
        raise ValueError("checkpoint identity mismatch")
    history = read_json(directory / "history.json")
    rows = history.get("steps", [])
    if len(rows) != steps or any(
        row.get("step") != index or not math.isfinite(row.get("loss", math.nan))
        for index, row in enumerate(rows, start=1)
    ):
        raise ValueError("training history is incomplete or non-finite")
    selected = history.get("selected_step")
    if checkpoint.get("selected_step") != selected or selected not in range(
        1, steps + 1
    ):
        raise ValueError("checkpoint selection differs from training history")
    num_classes, num_records = _verify_batches(directory, identity, config)
    recipe = _verify_training_recipe(identity, config, num_records)
    from pose_embed.benchmark.training import phase_for_step

    if any(row.get("phase") != phase_for_step(recipe, row["step"]) for row in rows):
        raise ValueError("training history has an incorrect warmup phase")
    if identity["method"] in {"proxy_nca_pp", "hist", "proxy_nca_metrix"}:
        for row in rows:
            gradients = row.get("encoder_gradient_parameters")
            needs_encoder = identity["track"] == "finetune" and row["phase"] == "main"
            if (
                type(gradients) is not int
                or gradients < 0
                or (gradients > 0) != needs_encoder
            ):
                raise ValueError(
                    "training history lacks the required encoder backward evidence"
                )
    if stage == "development":
        validation = [row for row in rows if "validation" in row]
        expected = [
            i
            for i in range(1, steps + 1)
            if i % config.training.validation_every == 0 or i == steps
        ]
        if [row["step"] for row in validation] != expected:
            raise ValueError("development validation schedule is incomplete")
        if any(
            not 0 <= row["validation"].get("r_at_1", math.nan) <= 1
            for row in validation
        ):
            raise ValueError("development validation score is invalid")
        eligible = [
            row for row in validation if row["step"] >= recipe["minimum_selected_step"]
        ]
        if not eligible:
            raise ValueError("no development checkpoint completed the full warmup")
        best = max(eligible, key=lambda row: row["validation"]["r_at_1"])
        result = read_json(directory / "development-result.json")
        if (
            result.get("identity") != identity
            or result.get("selected_step") != selected
            or (selected != best["step"] or result.get("metrics") != best["validation"])
        ):
            raise ValueError("development result differs from selected checkpoint")
    for group in ("model", "criterion"):
        state = checkpoint.get(group)
        if not isinstance(state, dict) or (group == "model" and not state):
            raise ValueError("checkpoint is missing trainable state")
        if any(
            not isinstance(v, torch.Tensor) or not torch.isfinite(v).all()
            for v in state.values()
        ):
            raise ValueError("checkpoint contains invalid parameters")
    _verify_checkpoint_state(directory, identity, config, checkpoint, num_classes)
    if identity["method"] == "mhgl":
        from pose_embed.benchmark.mhgl import verify_mhgl_optimizer

        verify_mhgl_optimizer(
            checkpoint,
            recipe,
            _expected_model_state(identity, config)["encoder_parameters"],
        )
    if identity["method"] == "s2sd":
        from pose_embed.benchmark.s2sd import verify_s2sd_optimizer

        verify_s2sd_optimizer(
            checkpoint,
            recipe,
            _expected_model_state(identity, config)["encoder_parameters"],
        )
    if identity["method"] == "drml":
        from pose_embed.benchmark.drml import verify_drml_optimizer

        verify_drml_optimizer(
            checkpoint,
            recipe,
            _expected_model_state(identity, config)["encoder_parameters"],
            rows,
            config.training.physical_batch_size,
        )
    if identity["method"] in {"proxy_nca_pp", "hist", "proxy_nca_metrix"}:
        _verify_proxy_optimizer(
            checkpoint,
            recipe,
            _expected_model_state(identity, config)["encoder_parameters"],
        )
    return manifest
