import pytest

from codemarp.cli.main import _validate_mode_args, build_parser, view_command
from codemarp.pipeline.apply_mode import ModeType


def test_view_command_runs(monkeypatch, tmp_path) -> None:

    monkeypatch.setattr(
        "codemarp.cli.main.open_mermaid_view",
        lambda *args, **kwargs: tmp_path / "codemarp_view.html",
    )
    monkeypatch.setattr(
        "codemarp.cli.main.render_mode_to_mermaid",
        lambda *args, **kwargs: "flowchart LR",
    )

    view_command(root=tmp_path, mode=ModeType.FULL)


def test_view_low_requires_focus():
    parser = build_parser()
    args = parser.parse_args(["view", ".", "--mode", "low"])

    with pytest.raises(SystemExit):
        _validate_mode_args(args, parser)


def test_view_trace_requires_focus():
    parser = build_parser()
    args = parser.parse_args(["view", ".", "--mode", "trace"])

    with pytest.raises(SystemExit):
        _validate_mode_args(args, parser)


def test_view_calls_render_and_open(monkeypatch, tmp_path):

    called = {}

    def fake_render(*args, **kwargs):
        called["render"] = True
        return "flowchart LR\nA --> B"

    def fake_open(*args, **kwargs):
        called["open"] = True

    monkeypatch.setattr("codemarp.cli.main.render_mode_to_mermaid", fake_render)
    monkeypatch.setattr("codemarp.cli.main.open_mermaid_view", fake_open)

    view_command(
        root=tmp_path,
        mode=ModeType.FULL,
    )

    assert called.get("render")
    assert called.get("open")


def test_view_low_uses_low_mode(monkeypatch, tmp_path):

    called = {}

    def fake_low_mode(*args, **kwargs):
        called["low"] = True

        class Dummy:
            nodes = []
            edges = []

        return Dummy()

    monkeypatch.setattr(
        "codemarp.cli.main._build_low_mode",
        fake_low_mode,
    )

    monkeypatch.setattr(
        "codemarp.pipeline.render_mode.render_mode_to_mermaid",
        lambda *a, **k: "flowchart LR",
    )
    monkeypatch.setattr(
        "codemarp.cli.main.open_mermaid_view",
        lambda *a, **k: None,
    )

    view_command(
        root=tmp_path,
        mode=ModeType.LOW,
        focus="x:y",
    )

    assert called.get("low")
