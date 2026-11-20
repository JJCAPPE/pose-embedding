import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/operations"))
import watch_scc_job as watch  # noqa: E402

ACCOUNTING = b"""jobnumber  42
qsub_time  Wed Nov 11 10:00:00 2026
end_time   Wed Nov 11 11:00:00 2026
taskid     undefined
failed     0
exit_status 1

"""


@pytest.mark.parametrize("running", [False, True])
def test_scc_wait_preserves_raw_accounting(tmp_path, monkeypatch, running):
    fixture = tmp_path / "accounting"
    fixture.write_bytes(ACCOUNTING)
    jobs = "<JB_job_number>42</JB_job_number>" if running else "<job_info/>"
    qacct_called = tmp_path / "qacct-called"
    for name, script in (
        ("qstat", f'printf "%s\\n" "{jobs}"'),
        ("qacct", f'touch "{qacct_called}"; cat "{fixture}"'),
        ("sleep", 'kill -TERM "$PPID"'),
    ):
        path = tmp_path / name
        path.write_text("#!/bin/sh\n" + script + "\n")
        path.chmod(0o700)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")
    result = subprocess.run(
        ["bash", "-c", watch.WAIT, "--", "42", "testnonce", "0"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    accounting = watch.accounting_from_pane(
        result.stdout, {"job_id": "42", "nonce": "testnonce"}
    )
    assert (result.returncode, accounting, qacct_called.exists()) == (
        (130, None, False) if running else (0, ACCOUNTING, True)
    )


def test_only_matching_terminal_frame_claimed_once(tmp_path, monkeypatch):
    active = tmp_path / "active.json"
    ticket = {
        "job_id": "42",
        "nonce": "testnonce",
        "pane": "%0",
        "identity": "remote:ssh:%0:10",
        "not_before": "2000-01-01T00:00:00Z",
    }
    active.write_text(json.dumps(ticket))
    monkeypatch.setattr(watch, "require_legacy_paused", lambda: None)
    monkeypatch.setattr(watch, "pane_snapshot", lambda _: ("tmux", ticket["identity"]))
    encoded = base64.b64encode(ACCOUNTING).decode()
    frame = f"POSE_SCC_testnonce_BEGIN\n{encoded}\nPOSE_SCC_testnonce_END\n"
    monkeypatch.setattr(watch.subprocess, "check_output", lambda *a, **kw: frame[:-6])
    assert watch.claim_completion(active) is None
    assert active.exists()
    monkeypatch.setattr(watch.subprocess, "check_output", lambda *a, **kw: frame)
    _, event = watch.claim_completion(active)
    assert (event / "accounting.txt").read_bytes() == ACCOUNTING
    assert not active.exists()
    active.write_text(json.dumps(ticket))
    with pytest.raises(FileExistsError):
        watch.claim_completion(active)


def test_rejects_accounting_for_different_job():
    encoded = base64.b64encode(ACCOUNTING).decode()
    with pytest.raises(ValueError, match="accounting must describe"):
        watch.accounting_from_pane(
            f"POSE_SCC_testnonce_BEGIN\n{encoded}\nPOSE_SCC_testnonce_END\n",
            {"job_id": "43", "nonce": "testnonce"},
        )
