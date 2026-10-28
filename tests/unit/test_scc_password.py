from __future__ import annotations

import os
import pty
import select
import signal
import termios
import time
from contextlib import suppress

import pytest

from scripts import scc_password


@pytest.fixture
def password_file(tmp_path, monkeypatch):
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    path = directory / "scc-password"
    path.touch(mode=0o600)
    monkeypatch.setattr(scc_password, "PASSWORD_FILE", path)
    monkeypatch.setenv("SSH_ASKPASS_REQUIRE", "force")
    monkeypatch.delenv("SSH_ASKPASS_PROMPT", raising=False)
    return path


@pytest.mark.parametrize(
    "prompt",
    ["Password: ", "(tester@scc1.bu.edu) Password:", "tester@scc2.bu.edu's password:"],
)
def test_store_then_supply_exact_password(password_file, monkeypatch, capsys, prompt):
    password = "  dummy '$`\\ password  "
    password_file.write_text("old password that is much longer than the new one")
    monkeypatch.setattr(scc_password, "hidden_input", lambda _: password)
    monkeypatch.setattr("sys.argv", ["scc_password.py", "--store"])
    scc_password.main()
    assert password not in capsys.readouterr().out
    assert password_file.read_text() == password
    monkeypatch.setattr("sys.argv", ["scc_password.py", prompt])
    scc_password.main()
    assert capsys.readouterr().out == password + "\n"


@pytest.mark.parametrize("invalid", ["", "abc\ndef", "abc\rdef", "abc\0def"])
def test_reject_invalid_password(password_file, monkeypatch, capsys, invalid):
    password_file.write_text(invalid)
    monkeypatch.setattr("sys.argv", ["scc_password.py", "Password:"])
    with pytest.raises(ValueError):
        scc_password.main()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "unsafe", ["file_mode", "directory_mode", "symlink", "hardlink"]
)
def test_reject_unsafe_storage(password_file, unsafe):
    password_file.write_text("dummy")
    if unsafe == "file_mode":
        password_file.chmod(0o644)
    elif unsafe == "directory_mode":
        password_file.parent.chmod(0o755)
    elif unsafe == "symlink":
        target = password_file.with_name("target")
        password_file.rename(target)
        password_file.symlink_to(target)
    else:
        os.link(password_file, password_file.with_name("hardlink"))
    with pytest.raises((ValueError, OSError)):
        scc_password.credential_file(os.O_RDONLY)


def test_duo_uses_separate_input(password_file, monkeypatch, capsys):
    password_file.write_text("dummy-password")
    prompt = "Duo two-factor login: Passcode or option (1-3): "
    monkeypatch.setattr("sys.argv", ["scc_password.py", prompt])
    prompts = []
    monkeypatch.setattr(
        scc_password, "hidden_input", lambda prompt: prompts.append(prompt) or "1"
    )
    scc_password.main()
    assert prompts == [prompt]
    assert capsys.readouterr().out == "1\n"


@pytest.mark.parametrize("hint", ["confirm", "none"])
def test_host_confirmation_never_reads_password(
    password_file, monkeypatch, capsys, hint
):
    monkeypatch.setattr("sys.argv", ["scc_password.py", "Password:"])
    monkeypatch.setenv("SSH_ASKPASS_PROMPT", hint)
    with pytest.raises(ValueError):
        scc_password.main()
    assert capsys.readouterr().out == ""


def test_direct_invocation_is_rejected(password_file, monkeypatch, capsys):
    monkeypatch.delenv("SSH_ASKPASS_REQUIRE")
    monkeypatch.setattr("sys.argv", ["scc_password.py", "Password:"])
    with pytest.raises(ValueError):
        scc_password.main()
    assert capsys.readouterr().out == ""


def test_hidden_input_uses_terminal_without_echo():
    pid, fd = pty.fork()
    if pid == 0:
        try:
            answer = scc_password.hidden_input("Hidden input: ")
            if answer == "synthetic-test-only":
                os.write(1, b"INPUT_OK\n")
        finally:
            os._exit(0)
    output = b""
    sent = False
    deadline = time.monotonic() + 5
    try:
        while time.monotonic() < deadline:
            if not select.select([fd], [], [], 0.1)[0]:
                continue
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            output += chunk
            if output.endswith(b"Hidden input: ") and not sent:
                assert not termios.tcgetattr(fd)[3] & termios.ECHO
                os.write(fd, b"synthetic-test-only\n")
                sent = True
        assert sent and b"INPUT_OK" in output
        assert b"synthetic-test-only" not in output
    finally:
        os.close(fd)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
