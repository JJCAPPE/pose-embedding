#!/usr/bin/env python3
"""Run fast, non-destructive repository and plan-integrity checks."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED_UPSTREAMS = {
    "MotionBERT",
    "MotionCLIP",
    "contextual-similarity",
    "MMAction2",
    "st-gcn",
    "text-to-motion-retrieval",
}
FORBIDDEN_TRACKED_PREFIXES = (
    ".cache/",
    "artifacts/",
    "data/raw/",
    "data/processed/",
    "lit-review/pdfs/",
    "lit-review/repos/",
    "node_modules/",
    "output/",
    "runs/",
    "tmp/",
)
MAX_TRACKED_BYTES = 20 * 1024 * 1024


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def validate_upstream_manifest(errors: list[str]) -> None:
    manifest_path = ROOT / "third_party" / "upstreams.toml"
    try:
        with manifest_path.open("rb") as manifest_file:
            manifest = tomllib.load(manifest_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        errors.append(f"cannot read upstream manifest: {error}")
        return

    entries = manifest.get("upstream", [])
    names = {entry.get("name") for entry in entries}
    if names != EXPECTED_UPSTREAMS:
        errors.append(
            f"upstream set mismatch: expected {sorted(EXPECTED_UPSTREAMS)}, "
            f"got {sorted(names)}"
        )
    for entry in entries:
        name = entry.get("name", "<unnamed>")
        repository = entry.get("repository")
        commit = entry.get("commit")
        if not isinstance(repository, str) or not repository.startswith(
            "https://github.com/"
        ):
            errors.append(f"{name}: repository is not an HTTPS GitHub URL")
        if not isinstance(commit, str) or not SHA_PATTERN.fullmatch(commit):
            errors.append(f"{name}: commit is not a full lowercase SHA")
        if name == "contextual-similarity" and (
            entry.get("license") != "UNSPECIFIED"
            or entry.get("reference_only") is not True
        ):
            errors.append(
                "contextual-similarity must remain unlicensed and reference-only"
            )


def validate_plan(errors: list[str]) -> None:
    plan_path = ROOT / "plan" / "research-plan.v1.json"
    if not plan_path.is_file():
        errors.append("missing plan/research-plan.v1.json")
        return

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"cannot read research plan: {error}")
        return

    if plan.get("schemaVersion") != "1.0.0":
        errors.append("research plan schemaVersion must be 1.0.0")
    project = plan.get("project", {})
    weeks = plan.get("weeks", [])
    if len(weeks) != 14:
        errors.append(f"research plan must contain 14 weeks, found {len(weeks)}")
        return

    try:
        project_start = date.fromisoformat(project["startDate"])
        project_end = date.fromisoformat(project["endDate"])
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"project date is invalid: {error}")
        return

    if project_start != date(2026, 9, 15) or project_end != date(2026, 12, 18):
        errors.append("project dates must be 2026-09-15 through 2026-12-18")

    expected_start = project_start
    all_ids: set[str] = {project.get("id", "")}
    for expected_number, week in enumerate(weeks, start=1):
        week_id = week.get("id")
        if week_id in all_ids:
            errors.append(f"duplicate plan id: {week_id}")
        all_ids.add(week_id)
        try:
            week_start = date.fromisoformat(week["startDate"])
            week_end = date.fromisoformat(week["endDate"])
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"week {expected_number} date is invalid: {error}")
            continue
        if week.get("number") != expected_number:
            errors.append(
                f"week position {expected_number} has number {week.get('number')!r}"
            )
        if week.get("projectId") != project.get("id"):
            errors.append(f"week {expected_number} projectId does not match project.id")
        if week_start != expected_start:
            errors.append(
                f"week {expected_number} does not start immediately "
                "after the prior week"
            )
        if week_end < week_start:
            errors.append(f"week {expected_number} ends before it starts")
        expected_start = week_end + timedelta(days=1)

        for collection_name in ("tasks", "gates"):
            for item in week.get(collection_name, []):
                item_id = item.get("id")
                if item_id in all_ids:
                    errors.append(f"duplicate plan id: {item_id}")
                all_ids.add(item_id)
                if item.get("weekId") != week.get("id"):
                    errors.append(f"{item_id}: weekId does not match containing week")

    if date.fromisoformat(weeks[-1]["endDate"]) != project_end:
        errors.append("the final week must end on the project end date")


def validate_tracked_files(errors: list[str]) -> None:
    stage_lines = git("ls-files", "--stage").splitlines()
    for line in stage_lines:
        mode, _object_id, _stage_and_path = line.split(maxsplit=2)
        path = _stage_and_path.split("\t", 1)[-1]
        if mode == "160000":
            errors.append(f"unresolved gitlink is tracked: {path}")
        if path == ".DS_Store" or path.endswith("/.DS_Store"):
            errors.append(f"Finder metadata is tracked: {path}")
        if path.startswith(FORBIDDEN_TRACKED_PREFIXES):
            errors.append(f"generated, licensed, or cache path is tracked: {path}")
        environment_name = Path(path).name
        is_example = environment_name.startswith(".env.") and environment_name.endswith(
            ".example"
        )
        is_environment = environment_name == ".env" or environment_name.startswith(
            ".env."
        )
        if is_environment and not is_example:
            errors.append(f"environment file is tracked: {path}")

        absolute_path = ROOT / path
        if absolute_path.is_file() and absolute_path.stat().st_size > MAX_TRACKED_BYTES:
            errors.append(f"tracked file exceeds 20 MiB: {path}")


def main() -> int:
    errors: list[str] = []
    validate_upstream_manifest(errors)
    validate_plan(errors)
    try:
        validate_tracked_files(errors)
    except (OSError, subprocess.CalledProcessError) as error:
        errors.append(f"Git workspace check failed: {error}")

    if errors:
        print("Workspace verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Workspace verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
