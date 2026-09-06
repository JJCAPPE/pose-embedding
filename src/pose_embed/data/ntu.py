"""Parsing for canonical NTU RGB+D sample identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_NTU_ID = re.compile(
    r"^(?P<sample>S(?P<setup>\d{3})C(?P<camera>\d{3})"
    r"P(?P<performer>\d{3})R(?P<repetition>\d{3})A(?P<action>\d{3}))"
    r"(?:\.[A-Za-z0-9_-]+)*$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, order=True)
class NTUSampleId:
    sample_id: str
    setup: int
    camera: int
    performer: int
    repetition: int
    action: int

    @property
    def performance_id(self) -> tuple[int, int, int, int]:
        """Identity shared by synchronized camera views of one performance."""
        return (self.setup, self.performer, self.repetition, self.action)


def parse_ntu_sample_id(value: str | Path) -> NTUSampleId:
    """Extract and validate an NTU identifier from a bare ID or filename."""
    text = str(value)
    match = _NTU_ID.fullmatch(Path(text).name)
    if match is None:
        raise ValueError(f"expected one canonical NTU sample filename in {text!r}")
    values = {
        name: int(match.group(name))
        for name in (
            "setup",
            "camera",
            "performer",
            "repetition",
            "action",
        )
    }
    bounds = {
        "setup": (1, 32),
        "camera": (1, 3),
        "performer": (1, 106),
        "repetition": (1, 2),
        "action": (1, 120),
    }
    for key, (minimum, maximum) in bounds.items():
        if not minimum <= values[key] <= maximum:
            raise ValueError(
                f"{key} must be in [{minimum}, {maximum}], got {values[key]}"
            )
    return NTUSampleId(sample_id=match.group("sample").upper(), **values)
