"""Report partitions require an explicit predecessor path and digest."""

from __future__ import annotations

import json

import pytest

from pose_embed import cli


@pytest.mark.parametrize("operation", ["build", "validate"])
@pytest.mark.parametrize("part", ["whole", "first", "second"])
def test_report_routes_each_pass_with_its_bound_continuation(
    monkeypatch, capsys, operation, part
):
    calls = []
    functions = {
        ("build", False): "build_report",
        ("build", True): "build_report_part_one",
        ("validate", False): "validate_core_report_summary",
        ("validate", True): "validate_core_report_summary_part_one",
    }
    for name in functions.values():
        monkeypatch.setattr(
            cli,
            name,
            lambda *args, _name=name, **kwargs: (
                calls.append((_name, args, kwargs)) or {"complete": part != "first"}
            ),
        )
    arguments = ["report", operation, "--protocol-config", "protocol.json"]
    if operation == "build":
        arguments += ["--results", "one.json", "two.json"]
        positional = (["one.json", "two.json"],)
        if part != "first":
            arguments += ["--output-dir", "report"]
            positional += ("report",)
    else:
        arguments += ["--summary", "report/summary.json"]
        positional = ("report/summary.json",)
    keyword = {"protocol_path": "protocol.json"}
    if part == "first":
        arguments += ["--write-continuation", "part-one.json"]
        positional += ("part-one.json",)
    else:
        keyword |= {"continuation_path": None, "continuation_sha256": None}
        if part == "second":
            arguments += [
                "--continuation",
                "part-one.json",
                "--continuation-sha256",
                "a" * 64,
            ]
            keyword |= {
                "continuation_path": "part-one.json",
                "continuation_sha256": "a" * 64,
            }
    assert cli.main(arguments) == 0
    assert calls == [(functions[operation, part == "first"], positional, keyword)]
    assert json.loads(capsys.readouterr().out) == {"complete": part != "first"}


@pytest.mark.parametrize("operation", ["build", "validate"])
@pytest.mark.parametrize(
    "flags",
    [
        ["--continuation", "part-one.json"],
        ["--continuation-sha256", "a" * 64],
        [
            "--write-continuation",
            "part-one.json",
            "--continuation-sha256",
            "a" * 64,
        ],
        ["--write-continuation", "part-one.json", "--continuation", "prior.json"],
        ["--part", "3"],
    ],
)
def test_report_rejects_incomplete_or_conflicting_partition_arguments(
    monkeypatch, capsys, operation, flags
):
    def unexpected(*_args, **_kwargs):
        pytest.fail("invalid arguments reached a report operation")

    for name in (
        "build_report",
        "build_report_part_one",
        "validate_core_report_summary",
        "validate_core_report_summary_part_one",
    ):
        monkeypatch.setattr(cli, name, unexpected)
    arguments = ["report", operation]
    arguments += (
        ["--results", "result.json", "--output-dir", "report"]
        if operation == "build"
        else ["--summary", "report/summary.json"]
    )
    try:
        status = cli.main(arguments + flags)
    except SystemExit as error:
        status = error.code
    assert status == 2
    assert "error:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "flags",
    [[], ["--write-continuation", "part-one.json", "--output-dir", "report"]],
)
def test_report_build_requires_output_only_for_complete_report(capsys, flags):
    assert cli.main(["report", "build", "--results", "result.json", *flags]) == 2
    assert "--output-dir" in capsys.readouterr().err
