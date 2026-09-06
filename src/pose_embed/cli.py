"""Command-line interface for protocol-locked Pose Embed experiments."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from pose_embed.data import load_manifest, verify_manifests
from pose_embed.evaluation.runner import evaluate_files
from pose_embed.features import apply_trained_head, extract_fixture_features
from pose_embed.protocol import current_code_hashes, verify_protocol
from pose_embed.report import build_report
from pose_embed.training import train_head

DEFAULT_PROTOCOL = "configs/protocol.v1.yaml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pose-embed",
        description="Protocol-locked one-shot pose-retrieval experiments",
    )
    commands = parser.add_subparsers(dest="area", required=True)

    protocol = commands.add_parser("protocol", help="validate the study protocol")
    protocol_commands = protocol.add_subparsers(dest="operation", required=True)
    protocol_verify = protocol_commands.add_parser(
        "verify", help="verify protocol and lock"
    )
    protocol_verify.add_argument("--config", default=DEFAULT_PROTOCOL)
    protocol_verify.add_argument("--lock")
    protocol_verify.add_argument("--evaluation-plan")
    protocol_verify.add_argument("--final-run-set")
    protocol_verify.add_argument("--require-locked", action="store_true")

    data = commands.add_parser("data", help="validate metadata-only data manifests")
    data_commands = data.add_subparsers(dest="operation", required=True)
    data_verify = data_commands.add_parser(
        "verify",
        help=(
            "check canonicalized per-sample manifests and leakage; aggregate "
            "HRNet pickle import remains gated"
        ),
    )
    data_verify.add_argument("--manifest", action="append", required=True)
    data_verify.add_argument("--config", default=DEFAULT_PROTOCOL)
    data_verify.add_argument("--check-files", action="store_true")
    data_verify.add_argument("--data-root")
    data_verify.add_argument(
        "--allow-partial",
        action="store_true",
        help="validate a development subset without requiring every protocol class",
    )

    features = commands.add_parser("features", help="extract cached representations")
    feature_commands = features.add_subparsers(dest="operation", required=True)
    feature_extract = feature_commands.add_parser(
        "extract", help="extract feature cache"
    )
    feature_extract.add_argument("--input", required=True)
    feature_extract.add_argument("--output", required=True)
    feature_extract.add_argument("--protocol-config", default=DEFAULT_PROTOCOL)
    feature_extract.add_argument("--manifest", required=True)
    feature_extract.add_argument(
        "--role",
        choices=["training", "gallery_clean", "query_clean", "query_corrupted"],
        required=True,
    )
    feature_extract.add_argument(
        "--split",
        choices=[
            "development_train",
            "development_validation",
            "final_train",
            "novel_anchor",
            "novel_query_primary",
            "novel_query_official",
        ],
        required=True,
    )
    feature_extract.add_argument("--backend", choices=["fixture"], default="fixture")
    feature_extract.add_argument("--embedding-dimension", type=int, default=32)
    feature_extract.add_argument("--seed", type=int, default=0)
    feature_extract.add_argument(
        "--corruption-family",
        choices=["coordinate_jitter", "joint_mask", "frame_mask"],
    )
    feature_extract.add_argument("--corruption-severity", type=float, default=0)
    feature_apply_head = feature_commands.add_parser(
        "apply-head", help="apply a trained retrieval head to base features"
    )
    feature_apply_head.add_argument("--input", required=True)
    feature_apply_head.add_argument("--output", required=True)
    feature_apply_head.add_argument("--checkpoint", required=True)
    feature_apply_head.add_argument("--run-manifest", required=True)
    feature_apply_head.add_argument("--protocol-config", default=DEFAULT_PROTOCOL)
    feature_apply_head.add_argument("--manifest", required=True)
    feature_apply_head.add_argument("--allow-fixture", action="store_true")

    train = commands.add_parser("train", help="train a declared retrieval head")
    train.add_argument("--config", required=True)
    train.add_argument("--input", required=True)
    train.add_argument("--output-dir", required=True)
    train.add_argument("--protocol-config", default=DEFAULT_PROTOCOL)
    train.add_argument("--manifest", required=True)
    train.add_argument("--device", default="cpu")
    train.add_argument("--allow-fixture", action="store_true")
    train.add_argument("--stretch-gate-evidence")

    evaluate = commands.add_parser("evaluate", help="evaluate one-shot retrieval")
    evaluate.add_argument("--gallery", required=True)
    evaluate.add_argument("--queries", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.add_argument(
        "--mode", choices=["development", "final", "exploratory"], required=True
    )
    evaluate.add_argument("--protocol-config", default=DEFAULT_PROTOCOL)
    evaluate.add_argument("--gallery-manifest", required=True)
    evaluate.add_argument("--query-manifest", required=True)
    evaluate.add_argument(
        "--method",
        choices=[
            "contrastive",
            "supcon",
            "contextual",
            "multi_similarity_with_miner",
        ],
        required=True,
    )
    evaluate.add_argument("--seed", type=int, required=True)
    evaluate.add_argument("--condition", required=True)
    evaluate.add_argument(
        "--query-definition",
        choices=["development", "primary", "official"],
        required=True,
    )
    evaluate.add_argument("--allow-fixture", action="store_true")
    evaluate.add_argument("--stretch-run-manifest")
    evaluate.add_argument("--stretch-gate-evidence")

    report = commands.add_parser(
        "report", help="build deterministic result tables and core analysis"
    )
    report_commands = report.add_subparsers(dest="operation", required=True)
    report_build = report_commands.add_parser(
        "build",
        help=(
            "validate result rows; an exact final core matrix also produces the "
            "preregistered analysis, complete metric curves, class errors, and "
            "runtime/memory/failure evidence"
        ),
    )
    report_build.add_argument("--results", nargs="+", required=True)
    report_build.add_argument("--output-dir", required=True)
    report_build.add_argument("--protocol-config", default=DEFAULT_PROTOCOL)
    return parser


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.area == "protocol":
            protocol, digest = verify_protocol(
                args.config,
                lock_path=args.lock,
                evaluation_plan_path=args.evaluation_plan,
                final_run_set_path=args.final_run_set,
                require_locked=args.require_locked,
            )
            _print(
                {
                    "status": "valid",
                    "protocol_id": protocol.protocol_id,
                    "protocol_sha256": digest,
                    "lock_verified": args.lock is not None or args.require_locked,
                    "current_code_sha256": current_code_hashes().model_dump(),
                }
            )
            return 0
        if args.area == "data":
            protocol, _ = verify_protocol(args.config)
            records = [
                record
                for manifest in args.manifest
                for record in load_manifest(manifest)
            ]
            data_root = args.data_root or os.environ.get("POSE_EMBED_DATA_ROOT")
            _print(
                verify_manifests(
                    records,
                    protocol,
                    data_root=data_root,
                    check_files=args.check_files,
                    require_complete=not args.allow_partial,
                )
            )
            return 0
        if args.area == "features":
            if args.operation == "extract":
                _print(
                    extract_fixture_features(
                        args.input,
                        args.output,
                        protocol_path=args.protocol_config,
                        manifest_path=args.manifest,
                        role=args.role,
                        split=args.split,
                        embedding_dimension=args.embedding_dimension,
                        seed=args.seed,
                        corruption_family=args.corruption_family,
                        corruption_severity=args.corruption_severity,
                    )
                )
            else:
                _print(
                    apply_trained_head(
                        args.input,
                        args.output,
                        checkpoint_path=args.checkpoint,
                        run_manifest_path=args.run_manifest,
                        protocol_path=args.protocol_config,
                        manifest_path=args.manifest,
                        allow_fixture=args.allow_fixture,
                    )
                )
            return 0
        if args.area == "train":
            _print(
                train_head(
                    args.config,
                    args.input,
                    args.output_dir,
                    protocol_path=args.protocol_config,
                    manifest_path=args.manifest,
                    device=args.device,
                    allow_fixture=args.allow_fixture,
                    stretch_gate_evidence_path=args.stretch_gate_evidence,
                )
            )
            return 0
        if args.area == "evaluate":
            _print(
                evaluate_files(
                    args.gallery,
                    args.queries,
                    args.output,
                    mode=args.mode,
                    protocol_path=args.protocol_config,
                    gallery_manifest_path=args.gallery_manifest,
                    query_manifest_path=args.query_manifest,
                    method=args.method,
                    seed=args.seed,
                    condition=args.condition,
                    query_definition=args.query_definition,
                    allow_fixture=args.allow_fixture,
                    stretch_run_manifest_path=args.stretch_run_manifest,
                    stretch_gate_evidence_path=args.stretch_gate_evidence,
                )
            )
            return 0
        if args.area == "report":
            _print(
                build_report(
                    args.results,
                    args.output_dir,
                    protocol_path=args.protocol_config,
                )
            )
            return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    raise AssertionError("unreachable command dispatch")


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
