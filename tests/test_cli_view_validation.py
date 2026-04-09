import argparse

import pytest

from codemap.cli.main import _validate_analyze_args, build_parser


def _parse(argv: list[str]) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = build_parser()
    args = parser.parse_args(argv)
    return parser, args


def test_full_view_rejects_focus() -> None:
    parser, args = _parse(["analyze", "src", "--view", "full", "--focus", "x:y"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_full_view_rejects_module() -> None:
    parser, args = _parse(["analyze", "src", "--view", "full", "--module", "pkg.mod"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_full_view_rejects_max_depth() -> None:
    parser, args = _parse(["analyze", "src", "--view", "full", "--max-depth", "2"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_trace_view_requires_focus() -> None:
    parser, args = _parse(["analyze", "src", "--view", "trace"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_trace_view_rejects_module() -> None:
    parser, args = _parse(
        ["analyze", "src", "--view", "trace", "--focus", "x:y", "--module", "pkg.mod"]
    )
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_trace_view_accepts_focus_and_depth() -> None:
    parser, args = _parse(
        [
            "analyze",
            "src",
            "--view",
            "trace",
            "--focus",
            "codemap.cli.main:analyze_command",
            "--max-depth",
            "3",
        ]
    )
    _validate_analyze_args(args, parser)


def test_module_view_requires_module() -> None:
    parser, args = _parse(["analyze", "src", "--view", "module"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_module_view_rejects_focus() -> None:
    parser, args = _parse(
        ["analyze", "src", "--view", "module", "--module", "pkg.mod", "--focus", "x:y"]
    )
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_module_view_rejects_max_depth() -> None:
    parser, args = _parse(
        [
            "analyze",
            "src",
            "--view",
            "module",
            "--module",
            "pkg.mod",
            "--max-depth",
            "2",
        ]
    )
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_module_view_accepts_module() -> None:
    parser, args = _parse(
        [
            "analyze",
            "src",
            "--view",
            "module",
            "--module",
            "codemap.parser.python_parser",
        ]
    )
    _validate_analyze_args(args, parser)


def test_reverse_view_requires_focus() -> None:
    parser, args = _parse(["analyze", "src", "--view", "reverse"])
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_reverse_view_rejects_module() -> None:
    parser, args = _parse(
        ["analyze", "src", "--view", "reverse", "--focus", "x:y", "--module", "pkg.mod"]
    )
    with pytest.raises(SystemExit):
        _validate_analyze_args(args, parser)


def test_reverse_view_accepts_focus_and_depth() -> None:
    parser, args = _parse(
        [
            "analyze",
            "src",
            "--view",
            "reverse",
            "--focus",
            "codemap.views.trace:trace_function_view",
            "--max-depth",
            "2",
        ]
    )
    _validate_analyze_args(args, parser)
