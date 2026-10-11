"""CLI orchestration for result-blind v3 preparation."""

from pathlib import Path

from pose_embed.config import load_protocol
from pose_embed.dataset_seal import canonical_artifact_root, register_artifact_roots
from pose_embed.preparation_v3 import prepare_v3, rebind_v3_manifests
from pose_embed.provenance import sha256_file


def run_preparation_command(args) -> dict:
    if args.operation in {"authorize-selection", "select"}:
        from pose_embed.config_v3 import ArtifactBinding
        from pose_embed.protocol_v3 import V3SelectionAuthorization
        from pose_embed.protocol_v3_campaign import (
            create_selected_configs,
            record_selection_authorization,
        )

        protocol = load_protocol(args.protocol_config)
        if args.operation == "authorize-selection":
            record = V3SelectionAuthorization.model_validate_json(
                Path(args.authorization).read_text()
            )
            return record_selection_authorization(protocol, record).model_dump(
                mode="json"
            )
        root = canonical_artifact_root()
        path = Path(args.ledger).resolve()
        binding = ArtifactBinding(
            relative_path=str(path.relative_to(root)), sha256=sha256_file(path)
        )
        return create_selected_configs(
            protocol, binding, recorded_by=args.recorded_by
        ).model_dump(mode="json")
    if args.operation == "geometry-panel":
        from pose_embed.geometry_v3 import run_geometry_panel

        return run_geometry_panel(
            args.protocol_config, args.manifest_set, args.output_dir
        )
    if args.operation == "prepare-execution":
        from pose_embed.revision_v3 import prepare_execution_revision

        return prepare_execution_revision(
            historical_manifest_set=args.historical_manifest_set,
            recorded_by=args.recorded_by,
        )
    if args.operation == "register-roots":
        return register_artifact_roots(args.root, external_audits=args.external_audit)
    if args.operation == "prepare":
        return prepare_v3(
            template_path=args.template,
            historical_protocol_path=args.historical_protocol,
            manifest_set_path=args.manifest_set,
            output_dir=args.output_dir,
        )
    if args.operation == "rebind-manifests":
        return rebind_v3_manifests(
            protocol_path=args.protocol_config,
            historical_manifest_set=args.historical_manifest_set,
            output_dir=args.output_dir,
        )
    from pose_embed.protocol_v3 import COUNTS, freeze_v3_design

    protocol = load_protocol(args.protocol_config)
    root = canonical_artifact_root()
    directory = Path(args.manifest_set).resolve().parent
    manifests = {}
    for role in COUNTS:
        parent = (
            directory / "development"
            if role in {"development_gallery", "development_queries"}
            else directory
        )
        path = parent / (role.replace("_", "-") + ".jsonl")
        manifests[role] = {
            "relative_path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
        }
    lock = freeze_v3_design(protocol, manifests=manifests, recorded_by=args.recorded_by)
    return lock.model_dump(mode="json")
