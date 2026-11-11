"""Hand off one terminal SCC job from the existing SSH pane to Codex on the Mac."""

import argparse
import base64
import fcntl
import json
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
import uuid
from datetime import datetime
from pathlib import Path

from notify_scc_job import notify, terminal_accounting
from scc_codex_dispatch import dispatch

STATE = Path.home() / ".config/pose-embed/scc-completion"
LABEL = "org.pose-embed.scc-completion"
SCHEDULE = "automations/complete-pose-embed-week-5/automation.toml"

# The remote loop only observes metadata. A failed qstat never implies completion.
WAIT = (
    "job=$1; nonce=$2; at=$3; umask 077; file=$(mktemp) || exit 1; "
    "trap 'rm -f -- \"$file\"' EXIT; trap 'exit 130' INT TERM; "
    'now=$(date +%s); if [ "$now" -lt "$at" ]; then sleep "$((at-now))" || exit; fi; '
    "while :; do "
    'if jobs=$(qstat -xml -u "$USER") && '
    '! grep -Eq "<JB_job_number>[[:space:]]*$job[[:space:]]*</JB_job_number>" '
    '<<< "$jobs" && '
    'LC_ALL=C qacct -j "$job" > "$file" 2>/dev/null; then '
    'printf "\\nPOSE_SCC_%s_BEGIN\\n" "$nonce"; base64 < "$file" | fold -w 64; '
    'printf "\\nPOSE_SCC_%s_END\\n" "$nonce"; break; fi; sleep 3600; done'
)


def pane_snapshot(pane):
    # launchd's default PATH does not include Homebrew.
    tmux = shutil.which("tmux", path="/opt/homebrew/bin:/usr/local/bin:/usr/bin")
    if tmux is None:
        raise RuntimeError("tmux not found")
    identity = subprocess.check_output(
        [
            tmux,
            "display-message",
            "-p",
            "-t",
            pane,
            "#{session_name}:#{pane_current_command}:#{pane_id}:#{pane_pid}",
        ],
        text=True,
        timeout=5,
    ).strip()
    if not re.fullmatch(r"remote:ssh:" + re.escape(pane) + r":[0-9]+", identity):
        raise ValueError("expected the existing SSH pane in the remote tmux session")
    return tmux, identity


def accounting_from_pane(snapshot, ticket):
    nonce = ticket["nonce"]
    match = re.search(
        rf"^POSE_SCC_{nonce}_BEGIN\n([A-Za-z0-9+/=\n]+)^POSE_SCC_{nonce}_END$",
        snapshot,
        re.M,
    )
    if not match:
        return None
    raw = base64.b64decode(match[1].replace("\n", ""), validate=True)
    terminal_accounting(ticket["job_id"], raw.decode("utf-8"))
    return raw


def install():
    if sys.platform != "darwin":
        raise RuntimeError("SCC continuation requires the local Mac")
    source = Path(__file__).resolve().parent
    bin_dir = STATE / "bin"
    bin_dir.mkdir(mode=0o700, exist_ok=True)
    if source != bin_dir:
        for name in ("watch_scc_job.py", "notify_scc_job.py", "scc_codex_dispatch.py"):
            shutil.copyfile(source / name, bin_dir / name)
    target = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(
        plistlib.dumps(
            {
                "Label": LABEL,
                "ProgramArguments": [
                    sys.executable,
                    str(bin_dir / "watch_scc_job.py"),
                    "check",
                ],
                "StartInterval": 60,
                "StandardErrorPath": str(STATE / "errors.log"),
            }
        )
    )
    print(target)


def require_legacy_paused():
    automation = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / SCHEDULE
    if (
        automation.exists()
        and tomllib.loads(automation.read_text())["status"] != "PAUSED"
    ):
        raise ValueError(
            "pause the legacy Week 5 Codex automation before using the watcher"
        )


def arm(args, active):
    require_legacy_paused()
    if active.exists():
        raise ValueError("one job is already armed; reconcile or disarm it first")
    if not re.fullmatch(r"[1-9][0-9]*", args.job_id):
        raise ValueError("job ID must be a positive decimal integer")
    if (active.parent / f"job-{args.job_id}").exists():
        raise ValueError(
            "this job already has a completion receipt; reconcile it first"
        )
    if not re.fullmatch(r"%[0-9]+", args.pane):
        raise ValueError("supply the exact tmux pane ID, for example %0")
    if not args.handoff.is_absolute() or not args.handoff.is_file():
        raise ValueError("handoff must be an existing absolute local file")
    if not args.cwd.is_absolute() or not (args.cwd / "AGENTS.md").is_file():
        raise ValueError("cwd must be the absolute research worktree")
    not_before = datetime.fromisoformat(args.not_before)
    if not_before.utcoffset() is None:
        raise ValueError("not-before must include its time zone")
    _, identity = pane_snapshot(args.pane)
    ticket = {
        "nonce": uuid.uuid4().hex,
        "job_id": args.job_id,
        "launch_receipt": args.launch_receipt,
        "handoff": str(args.handoff),
        "not_before": args.not_before,
        "cwd": str(args.cwd),
        "project_id": str(uuid.UUID(args.project_id)),
        "pane": args.pane,
        "identity": identity,
    }
    temporary = active.with_suffix(".tmp")
    temporary.write_text(json.dumps(ticket, indent=2) + "\n")
    temporary.replace(active)
    print(
        shlex.join(
            [
                "bash",
                "-c",
                WAIT,
                "--",
                args.job_id,
                ticket["nonce"],
                str(int(not_before.timestamp())),
            ]
        )
    )


def claim_completion(active):
    require_legacy_paused()
    ticket = json.loads(active.read_text())
    if datetime.now().astimezone() < datetime.fromisoformat(ticket["not_before"]):
        return None
    tmux, identity = pane_snapshot(ticket["pane"])
    if identity != ticket["identity"]:
        raise ValueError("the armed SCC pane changed; reconcile before rearming")
    snapshot = subprocess.check_output(
        [tmux, "capture-pane", "-p", "-J", "-S", "-200", "-t", ticket["pane"]],
        text=True,
        timeout=5,
    )
    raw = accounting_from_pane(snapshot, ticket)
    if raw is None:
        return None
    event = active.parent / f"job-{ticket['job_id']}"
    # Existing event directories mean a prior dispatch may have started.
    event.mkdir(mode=0o700)
    (event / "accounting.txt").write_bytes(raw)
    active.rename(event / "handoff.json")
    return ticket, event


def continue_job(ticket, event):
    job = ticket["job_id"]
    accounting = event / "accounting.txt"
    try:
        notify(job, accounting)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        (event / "alert-error.txt").write_text(str(exc) + "\n")
    prompt = (
        f"SCC job {job} has terminal accounting. Take over as the sole SCC controller "
        "for the current authorized research week. Read AGENTS.md, the SCC runbook, "
        f"and the current private handoff at {ticket['handoff']!r}. "
        f"Event receipt: {str(event / 'handoff.json')!r}. "
        f"Launch receipt: {ticket['launch_receipt']!r}. qacct: {str(accounting)!r}. "
        f"Use the research worktree {ticket['cwd']!r}. "
        "Reconcile current pause, pane and authorization before any SCC action. "
        "Independently verify the job: scheduler exit is not scientific acceptance. "
        "Continue only the next authorized prerequisite or record the blocker. "
        "If you submit the next job, update the same handoff and arm the watcher. "
        "Preserve all research gates and publish only verified changes."
    )
    try:
        dispatch(
            ticket["project_id"],
            Path(ticket["cwd"]),
            f"Pose Embed SCC {job}: review and continue",
            prompt,
            lambda thread: (event / "thread-id").write_text(thread + "\n"),
        )
    except (OSError, RuntimeError) as exc:
        (event / "dispatch-error.txt").write_text(str(exc) + "\n")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "check", "status", "disarm"):
        commands.add_parser(command)
    registration = commands.add_parser("arm")
    for name in ("job-id", "launch-receipt", "not-before", "project-id", "pane"):
        registration.add_argument(f"--{name}", required=True)
    for name in ("handoff", "cwd"):
        registration.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
    if STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise ValueError(
            "the SCC watcher state directory must be private to the local user"
        )
    if args.command == "install":
        install()
        return
    active = STATE / "active.json"
    result = None
    with (STATE / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.command == "arm":
            arm(args, active)
        elif args.command == "status":
            print(
                json.loads(active.read_text())["job_id"] if active.exists() else "idle"
            )
        elif args.command == "disarm" and active.exists():
            active.rename(
                STATE / f"disarmed-{json.loads(active.read_text())['nonce']}.json"
            )
        elif args.command == "check" and active.exists():
            result = claim_completion(active)
    if result:
        continue_job(*result)


if __name__ == "__main__":
    main()
