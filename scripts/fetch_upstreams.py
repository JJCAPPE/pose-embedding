#!/usr/bin/env python3
"""Fetch or verify exact upstream research repositories in an ignored cache."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "third_party" / "upstreams.toml"
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


class UpstreamError(RuntimeError):
    """Raised when an upstream cannot be reproduced safely."""


@dataclass(frozen=True)
class Upstream:
    name: str
    repository: str
    commit: str
    license: str
    license_files: tuple[str, ...]
    reference_only: bool


def run_git(*arguments: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        raise UpstreamError(f"git {' '.join(arguments)} failed: {detail}") from error
    return result.stdout.strip()


def normalize_repository(repository: str) -> str:
    return repository.removesuffix("/").removesuffix(".git")


def load_manifest(path: Path) -> tuple[Path, list[Upstream]]:
    with path.open("rb") as manifest_file:
        document = tomllib.load(manifest_file)

    if document.get("schema_version") != 1:
        raise UpstreamError("unsupported upstream manifest schema_version")

    raw_cache = document.get("cache_directory")
    if not isinstance(raw_cache, str) or not raw_cache:
        raise UpstreamError("cache_directory must be a non-empty string")
    cache_directory = (ROOT / raw_cache).resolve()
    if not cache_directory.is_relative_to(ROOT):
        raise UpstreamError("cache_directory must resolve inside the repository")

    entries: list[Upstream] = []
    names: set[str] = set()
    for raw_entry in document.get("upstream", []):
        name = raw_entry.get("name")
        repository = raw_entry.get("repository")
        commit = raw_entry.get("commit")
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
            raise UpstreamError(f"invalid upstream name: {name!r}")
        if name in names:
            raise UpstreamError(f"duplicate upstream name: {name}")
        names.add(name)
        if not isinstance(repository, str):
            raise UpstreamError(f"{name}: repository must be a string")
        parsed_repository = urlparse(repository)
        if (
            parsed_repository.scheme != "https"
            or parsed_repository.hostname != "github.com"
        ):
            raise UpstreamError(f"{name}: repository must be an HTTPS github.com URL")
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise UpstreamError(f"{name}: commit must be a lowercase 40-character SHA")

        entries.append(
            Upstream(
                name=name,
                repository=repository,
                commit=commit,
                license=str(raw_entry.get("license", "UNSPECIFIED")),
                license_files=tuple(raw_entry.get("license_files", [])),
                reference_only=bool(raw_entry.get("reference_only", True)),
            )
        )

    if not entries:
        raise UpstreamError("upstream manifest contains no entries")
    return cache_directory, entries


def verify_checkout(entry: Upstream, destination: Path) -> None:
    if not (destination / ".git").is_dir():
        raise UpstreamError(
            f"{entry.name}: checkout is missing or not a Git repository"
        )

    actual_remote = run_git("remote", "get-url", "origin", cwd=destination)
    if normalize_repository(actual_remote) != normalize_repository(entry.repository):
        raise UpstreamError(
            f"{entry.name}: origin mismatch; expected {entry.repository}, "
            f"got {actual_remote}"
        )

    actual_commit = run_git("rev-parse", "HEAD", cwd=destination)
    if actual_commit != entry.commit:
        raise UpstreamError(
            f"{entry.name}: HEAD mismatch; expected {entry.commit}, got {actual_commit}"
        )

    for relative_license in entry.license_files:
        if not (destination / relative_license).is_file():
            raise UpstreamError(
                f"{entry.name}: declared license file is missing: {relative_license}"
            )


def fetch_checkout(entry: Upstream, destination: Path) -> None:
    if destination.exists():
        verify_checkout(entry, destination)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{entry.name}.", dir=destination.parent))
    try:
        run_git("init", "--quiet", str(temporary))
        run_git("remote", "add", "origin", entry.repository, cwd=temporary)
        run_git(
            "fetch",
            "--quiet",
            "--depth",
            "1",
            "origin",
            entry.commit,
            cwd=temporary,
        )
        run_git("checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=temporary)
        verify_checkout(entry, temporary)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--cache-dir", type=Path, help="Override the manifest cache directory"
    )
    parser.add_argument(
        "--name", action="append", dest="names", help="Select one or more entries"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing checkouts without fetching or changing anything",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        cache_directory, entries = load_manifest(arguments.manifest.resolve())
        if arguments.cache_dir:
            cache_directory = arguments.cache_dir.resolve()
        if arguments.names:
            selected_names = set(arguments.names)
            entries = [entry for entry in entries if entry.name in selected_names]
            missing_names = selected_names - {entry.name for entry in entries}
            if missing_names:
                formatted_names = ", ".join(sorted(missing_names))
                raise UpstreamError(f"unknown upstream name(s): {formatted_names}")

        for entry in entries:
            destination = cache_directory / entry.name
            if arguments.check:
                verify_checkout(entry, destination)
            else:
                fetch_checkout(entry, destination)
            restriction = (
                "reference-only" if entry.reference_only else "licensed port permitted"
            )
            print(
                f"verified {entry.name} @ {entry.commit} "
                f"({entry.license}; {restriction})"
            )
    except (
        OSError,
        subprocess.CalledProcessError,
        UpstreamError,
        tomllib.TOMLDecodeError,
    ) as error:
        print(f"upstream verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
