#!/usr/bin/env python3
"""Store an SCC password locally or supply it to OpenSSH's askpass pipe."""

from __future__ import annotations

import getpass
import os
import re
import stat
import sys
import warnings
from pathlib import Path

PASSWORD_FILE = Path.home() / ".config/pose-embed/scc-password"
PASSWORD_PROMPT = re.compile(
    r"(?:\([\w.-]+@(?:scc[124]|scc-lite|geo)\.bu\.edu\)\s*"
    r"|[\w.-]+@(?:scc[124]|scc-lite|geo)\.bu\.edu's\s+)?password:",
    re.IGNORECASE,
)


def credential_file(flags: int):
    directory = PASSWORD_FILE.parent.lstat()
    if (
        not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != os.getuid()
        or stat.S_IMODE(directory.st_mode) != 0o700
    ):
        raise ValueError("Password directory must be owned by you with mode 700.")
    fd = os.open(PASSWORD_FILE, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    metadata = os.fstat(fd)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_nlink != 1
    ):
        os.close(fd)
        raise ValueError("Password must be a private, single-link file with mode 600.")
    return os.fdopen(fd, "w" if flags & os.O_WRONLY else "r", encoding="utf-8")


def validate_password(password: str) -> str:
    if not password or any(character in password for character in "\r\n\0"):
        raise ValueError("Password must be nonempty and contain no line breaks or NUL.")
    return password


def hidden_input(prompt: str) -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        with open("/dev/tty", "w") as tty:
            return getpass.getpass(prompt, stream=tty)


def main() -> None:
    if sys.argv[1:] == ["--store"]:
        password = validate_password(hidden_input("SCC password (hidden): "))
        PASSWORD_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with credential_file(os.O_WRONLY | os.O_CREAT) as target:
            target.write(password)
            target.truncate()
        print("SCC password saved locally; its value was not displayed.")
    elif len(sys.argv) == 2 and os.environ.get("SSH_ASKPASS_REQUIRE") == "force":
        if os.environ.get("SSH_ASKPASS_PROMPT") in {"confirm", "none"}:
            raise ValueError("Host confirmation must be handled separately.")
        if PASSWORD_PROMPT.fullmatch(sys.argv[1].strip()):
            with credential_file(os.O_RDONLY) as source:
                password = validate_password(source.read())
        else:
            # Duo and other challenges need a separate response, never the password.
            password = hidden_input(sys.argv[1])
        sys.stdout.write(password + "\n")
    else:
        raise ValueError("Use --store in Terminal; askpass mode is for SSH only.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError, getpass.GetPassWarning):
        print(
            "SCC password helper failed; no credential was displayed.", file=sys.stderr
        )
        sys.exit(1)
