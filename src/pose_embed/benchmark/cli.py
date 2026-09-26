"""CLI adapters for the complete roster and paired development experiments."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from pose_embed.benchmark.config import (
    METHOD_IDS,
    REPOSITORY_ROOT,
    benchmark_digest,
    load_benchmark,
    load_methods,
)
from pose_embed.benchmark.losses import supports
from pose_embed.benchmark.runner import compare_development, run_experiment
from pose_embed.benchmark.runtime import artifact_path
from pose_embed.provenance import write_immutable_json

DEFAULT_CONFIG = str(REPOSITORY_ROOT / "configs/benchmark.v2.yaml")


def _profile_steps(value: str) -> int:
    steps = int(value)
    if not 1 <= steps <= 100:
        raise argparse.ArgumentTypeError("profile steps must be between 1 and 100")
    return steps


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add the benchmark command without modifying the legacy command handlers."""
    parser = subparsers.add_parser(
        "benchmark", help="run the versioned motion-retrieval benchmark"
    )
    commands = parser.add_subparsers(dest="benchmark_operation", required=True)
    coverage = commands.add_parser(
        "coverage", help="show all required methods and unresolved implementation gates"
    )
    coverage.add_argument("--config", default=DEFAULT_CONFIG)
    coverage.add_argument("--output", help="write immutable coverage evidence")
    for name in ("profile", "train"):
        command = commands.add_parser(
            name,
            help=(
                "measure actual optimizer steps on auxiliary training data"
                if name == "profile"
                else "train one explicitly selected method and paired seed"
            ),
        )
        command.add_argument("--config", default=DEFAULT_CONFIG)
        command.add_argument("--method", choices=METHOD_IDS, required=True)
        command.add_argument("--seed", type=int, required=True)
        command.add_argument("--manifest-set", required=True)
        command.add_argument("--parity-evidence", required=True)
        command.add_argument("--output-dir", required=True)
        command.add_argument(
            "--track",
            choices=("frozen", "finetune"),
            default=None,
            help="must match encoder_mode in the selected configuration",
        )
        command.add_argument("--device", default="cuda")
        if name == "profile":
            command.add_argument("--steps", type=_profile_steps, default=3)
        else:
            command.add_argument(
                "--resume-from",
                help="latest sealed segment manifest of this experiment",
            )
            command.add_argument(
                "--segment-steps",
                type=int,
                help="stop at a safe boundary after this many additional updates",
            )
            command.add_argument(
                "--max-segment-seconds",
                type=float,
                help=(
                    "request a safe stop after this wall time; leave job time "
                    "for validation/checkpoint writes"
                ),
            )
            command.add_argument(
                "--candidate",
                choices=("baseline", "half", "double"),
                help="predeclared development candidate; final runs adopt the winner",
            )
            command.add_argument(
                "--phase",
                choices=("development", "final"),
                default="development",
                help="final training additionally requires the complete selection lock",
            )
    campaign = commands.add_parser(
        "declare-campaign",
        help="seal the three-candidate development grid after all GPU profiles",
    )
    campaign.add_argument("--config", default=DEFAULT_CONFIG)
    campaign.add_argument("--run-root", required=True)
    campaign.add_argument("--profiles", nargs="+", required=True)
    campaign.add_argument("--prior-trial-roots", nargs="+", required=True)
    campaign.add_argument("--priority-comparison", required=True)
    review = commands.add_parser(
        "review-failure", help="append an operational failure classification"
    )
    review.add_argument("--run", required=True)
    review.add_argument(
        "--category",
        choices=("gpu_allocation", "preemption", "filesystem", "process_interruption"),
        required=True,
    )
    review.add_argument("--reason", required=True)
    compare = commands.add_parser(
        "compare", help="verify and compare a complete paired development run matrix"
    )
    compare.add_argument("--runs", nargs="+", required=True)
    compare.add_argument("--output", required=True)
    for name in ("select", "lock-final"):
        command = commands.add_parser(
            name, help="seal the complete required run matrix"
        )
        command.add_argument("--config", default=DEFAULT_CONFIG)
        command.add_argument("--runs", nargs="+", required=True)
    evaluate = commands.add_parser(
        "evaluate", help="evaluate a locked final checkpoint"
    )
    evaluate.add_argument("--config", default=DEFAULT_CONFIG)
    evaluate.add_argument("--run", required=True)
    evaluate.add_argument("--manifest-set", required=True)
    evaluate.add_argument("--parity-evidence", required=True)
    evaluate.add_argument("--output-dir", required=True)
    evaluate.add_argument("--device", default="cuda")
    report = commands.add_parser("report", help="report the complete final comparison")
    report.add_argument("--config", default=DEFAULT_CONFIG)
    report.add_argument("--results", nargs="+", required=True)
    report.add_argument("--output-dir", required=True)
    return parser


def _coverage(config_path: str | Path) -> dict[str, Any]:
    config = load_benchmark(config_path)
    methods = load_methods()
    runnable = []
    blocked = []
    for method_id in config.final_methods:
        spec = methods[method_id]
        if supports(method_id) != (spec.status == "implemented"):
            raise ValueError(
                f"registry implementation status differs from code: {method_id}"
            )
        (runnable if supports(method_id) else blocked).append(method_id)
    return {
        "schema_version": 2,
        "protocol_id": config.protocol_id,
        "benchmark_sha256": benchmark_digest(config),
        "methods_sha256": config.methods_sha256,
        "input_protocol_sha256": config.input_protocol_sha256,
        "phase": config.phase,
        "priority_methods": list(config.priority_methods),
        "encoder_mode": config.training.encoder_mode,
        "paired_seeds": list(config.training.seeds),
        "required_method_count": len(config.final_methods),
        "implemented_method_count": len(runnable),
        "blocked_method_count": len(blocked),
        "implemented_methods": runnable,
        "blocked_methods": blocked,
        "required_development_run_count": len(config.final_methods)
        * len(config.training.seeds)
        * 3,
        "development_candidates": ["baseline", "half", "double"],
        "profile_retrieval_prefix_size": 128,
        "engineering_pilots_select_final": False,
        "required_final_run_count": len(config.final_methods)
        * len(config.training.seeds),
        "final_gate_status": "requires_locked_selection_and_complete_final_suite",
        "final_test_authorized": False,
        "methods": [
            methods[method].model_dump(mode="json") for method in config.final_methods
        ],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Return serializable evidence; the parent CLI owns printing and exit codes."""
    operation = args.benchmark_operation
    if operation == "declare-campaign":
        from pose_embed.benchmark.campaign import declare_campaign

        return declare_campaign(
            config_path=args.config,
            run_root=args.run_root,
            profiles=args.profiles,
            prior_trial_roots=args.prior_trial_roots,
            priority_comparison=args.priority_comparison,
        )
    if operation == "review-failure":
        from pose_embed.benchmark.campaign import review_failure

        return review_failure(args.run, category=args.category, reason=args.reason)
    if operation in {"select", "lock-final"}:
        from pose_embed.benchmark.locks import create_selection, lock_final_runs

        action = create_selection if operation == "select" else lock_final_runs
        return action(args.runs, config_path=args.config)
    if operation == "evaluate":
        from pose_embed.benchmark.evaluation import evaluate_final

        return evaluate_final(
            run_dir=args.run,
            config_path=args.config,
            manifest_set_path=args.manifest_set,
            parity_evidence_path=args.parity_evidence,
            output_dir=args.output_dir,
            device=args.device,
        )
    if operation == "report":
        from pose_embed.benchmark.evaluation import report_final

        return report_final(
            args.results, config_path=args.config, output_dir=args.output_dir
        )
    if operation == "coverage":
        result = _coverage(args.config)
        if args.output is not None:
            write_immutable_json(artifact_path(args.output), result)
        return result
    if operation == "compare":
        return compare_development(args.runs, args.output)
    if operation not in {"profile", "train"}:
        raise ValueError(f"unknown benchmark operation: {operation}")
    config = load_benchmark(args.config)
    spec = load_methods()[args.method]
    if not supports(args.method) or spec.status != "implemented":
        raise ValueError(f"{args.method} is blocked: {spec.blocker}")
    if args.seed not in config.training.seeds:
        raise ValueError("seed is outside the six declared paired seeds")
    if args.track is not None and args.track != config.training.encoder_mode:
        raise ValueError("track must match encoder_mode in the selected configuration")
    return run_experiment(
        config_path=args.config,
        manifest_set_path=args.manifest_set,
        parity_evidence_path=args.parity_evidence,
        output_dir=args.output_dir,
        method=args.method,
        seed=args.seed,
        track=args.track,
        device=args.device,
        stage=args.phase if operation == "train" else "development",
        profile_steps=args.steps if operation == "profile" else None,
        resume_from=getattr(args, "resume_from", None),
        segment_steps=getattr(args, "segment_steps", None),
        max_segment_seconds=getattr(args, "max_segment_seconds", None),
        candidate=getattr(args, "candidate", None),
    )
