"""Send a deduplicated Mac alert from retained terminal SCC accounting."""

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

APPLESCRIPT = """on run argv
    display notification (item 1 of argv) with title "Pose Embed SCC" sound name "Glass"
end run"""
DEFAULT_STATE = (
    Path.home() / ".codex/automations/complete-pose-embed-week-5/notifications"
)


def terminal_accounting(job_id, text):
    if not re.fullmatch(r"[1-9][0-9]*", job_id):
        raise ValueError("job ID must be a positive decimal integer")
    fields = {}
    for key in (
        "jobnumber",
        "qsub_time",
        "end_time",
        "taskid",
        "failed",
        "exit_status",
    ):
        values = re.findall(rf"^{key}[ \t]+([^\n]+)$", text, re.M)
        if len(values) != 1:
            raise ValueError(f"accounting requires exactly one {key}")
        fields[key] = values[0].strip()
    if fields["jobnumber"] != job_id or fields["taskid"] != "undefined":
        raise ValueError("accounting must describe this single, non-array job")
    for key in ("qsub_time", "end_time"):
        if not fields[key] or fields[key] in {"0", "-/-", "undefined", "NONE"}:
            raise ValueError(f"accounting has no terminal {key}")
    for key in ("failed", "exit_status"):
        pattern = r"([0-9]+)(?:[ \t]+:.*)?" if key == "failed" else r"([0-9]+)"
        match = re.fullmatch(pattern, fields[key])
        if not match:
            raise ValueError(f"accounting has invalid {key}")
        fields[key] = int(match[1])
    return fields


def notify(job_id, accounting, state_dir=DEFAULT_STATE):
    raw = Path(accounting).read_bytes()
    fields = terminal_accounting(job_id, raw.decode("utf-8"))
    if sys.platform != "darwin":
        raise RuntimeError("SCC desktop alerts must run on the local Mac")
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    identity = hashlib.sha256(fields["qsub_time"].encode()).hexdigest()
    receipt = state_dir / f"{job_id}-{identity}.json"
    with (state_dir / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if receipt.exists():
            prior = json.loads(receipt.read_text())
            if prior["accounting"] != fields:
                raise ValueError("terminal accounting conflicts with the alert receipt")
            return False
        outcome = "failed" if fields["failed"] or fields["exit_status"] else "ended"
        message = (
            f"Job {job_id} {outcome} (exit {fields['exit_status']}, "
            f"scheduler {fields['failed']}); evidence review pending."
        )
        subprocess.run(
            ["/usr/bin/osascript", "-e", APPLESCRIPT, message],
            check=True,
            timeout=15,
            capture_output=True,
            text=True,
        )
        record = {
            "accounting": fields,
            "accounting_sha256": hashlib.sha256(raw).hexdigest(),
            "notified_at": datetime.now(UTC).isoformat(),
        }
        # shortcut: an alert/receipt crash may repeat it; use OS IDs for exact-once.
        temporary = receipt.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2) + "\n")
        temporary.replace(receipt)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--accounting", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    print(
        json.dumps({"notified": notify(args.job_id, args.accounting, args.state_dir)})
    )


if __name__ == "__main__":
    main()
