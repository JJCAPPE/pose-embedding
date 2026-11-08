"""Local notification checks use synthetic accounting and never display alerts."""

import hashlib
import importlib.util
import json
import subprocess

import pytest

ACCOUNTING = """==============================================================
jobnumber    123
qsub_time    Sat Nov  7 14:31:22 2026
end_time     Sat Nov  7 14:40:00 2026
taskid       undefined
failed       0
exit_status  0
"""


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "scc_alert_fixture", "scripts/operations/notify_scc_job.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    monkeypatch.setattr(helper.sys, "platform", "darwin")
    calls = []
    monkeypatch.setattr(
        helper.subprocess, "run", lambda *a, **kw: calls.append((a, kw))
    )
    accounting = tmp_path / "accounting.txt"
    accounting.write_text(ACCOUNTING)
    return helper, accounting, tmp_path / "notifications", calls


@pytest.mark.parametrize(
    "failed,exit_status,outcome",
    [(0, 0, "ended"), (0, 137, "failed"), (100, 0, "failed")],
)
def test_alert_binds_terminal_evidence_and_deduplicates(
    inputs, failed, exit_status, outcome
):
    helper, accounting, state, calls = inputs
    accounting.write_text(
        ACCOUNTING.replace("failed       0", f"failed       {failed}").replace(
            "exit_status  0", f"exit_status  {exit_status}"
        )
    )
    assert helper.notify("123", accounting, state)
    assert not helper.notify("123", accounting, state)
    assert len(calls) == 1
    command = calls[0][0][0]
    assert command[:3] == ["/usr/bin/osascript", "-e", helper.APPLESCRIPT]
    assert f"Job 123 {outcome}" in command[3]
    assert "evidence review pending" in command[3]
    receipt = json.loads(next(state.glob("*.json")).read_text())
    assert (
        receipt["accounting_sha256"]
        == hashlib.sha256(accounting.read_bytes()).hexdigest()
    )
    assert receipt["accounting"]["exit_status"] == exit_status
    assert receipt["accounting"]["failed"] == failed
    assert receipt["notified_at"].endswith("+00:00")


@pytest.mark.parametrize(
    "text",
    [
        "error: job id 123 not found\n",
        ACCOUNTING + ACCOUNTING,
        ACCOUNTING.replace("jobnumber    123", "jobnumber    456"),
        ACCOUNTING.replace("taskid       undefined", "taskid       1"),
        ACCOUNTING.replace("exit_status  0\n", ""),
        ACCOUNTING.replace("exit_status  0", "exit_status  0 trailing"),
        ACCOUNTING.replace("failed       0", "failed       unknown"),
        ACCOUNTING.replace("failed       0", "failed       "),
        ACCOUNTING.replace("end_time     Sat Nov  7 14:40:00 2026", "end_time     -/-"),
    ],
)
def test_invalid_or_nonterminal_accounting_never_alerts(inputs, text):
    helper, accounting, state, calls = inputs
    accounting.write_text(text)
    with pytest.raises(ValueError):
        helper.notify("123", accounting, state)
    assert not calls
    assert not state.exists()


def test_failed_delivery_is_retriable(inputs, monkeypatch):
    helper, accounting, state, calls = inputs
    deliver = helper.subprocess.run

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(helper.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        helper.notify("123", accounting, state)
    assert not list(state.glob("*.json"))
    monkeypatch.setattr(helper.subprocess, "run", deliver)
    assert helper.notify("123", accounting, state)
    assert len(calls) == 1


def test_reused_job_number_alerts_for_new_submission(inputs):
    helper, accounting, state, calls = inputs
    assert helper.notify("123", accounting, state)
    accounting.write_text(ACCOUNTING.replace("14:31:22", "14:32:22"))
    assert helper.notify("123", accounting, state)
    assert len(calls) == 2


def test_changed_terminal_result_does_not_replace_receipt(inputs):
    helper, accounting, state, calls = inputs
    assert helper.notify("123", accounting, state)
    receipt = next(state.glob("*.json"))
    previous = receipt.read_bytes()
    accounting.write_text(ACCOUNTING.replace("exit_status  0", "exit_status  137"))
    with pytest.raises(ValueError, match="conflicts"):
        helper.notify("123", accounting, state)
    assert receipt.read_bytes() == previous
    assert len(calls) == 1


def test_scheduler_failure_annotation_is_preserved_as_numeric_code(inputs):
    helper, accounting, state, calls = inputs
    accounting.write_text(
        ACCOUNTING.replace("failed       0", "failed       37 : limit")
    )
    assert helper.notify("123", accounting, state)
    assert "scheduler 37" in calls[0][0][0][3]


@pytest.mark.parametrize("job_id", ["0", "-1", "../123", "123;command"])
def test_invalid_job_ids_never_reach_notification_or_state(inputs, job_id):
    helper, accounting, state, calls = inputs
    with pytest.raises(ValueError):
        helper.notify(job_id, accounting, state)
    assert not calls
    assert not state.exists()


def test_non_mac_rejected_without_receipt(inputs, monkeypatch):
    helper, accounting, state, calls = inputs
    monkeypatch.setattr(helper.sys, "platform", "linux")
    with pytest.raises(RuntimeError):
        helper.notify("123", accounting, state)
    assert not calls
    assert not state.exists()
