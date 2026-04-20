from pathlib import Path

import pytest

from codemarp.cli.main import analyze_command, build_parser, package_version
from codemarp.pipeline.apply_mode import ModeType


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "worker.py").write_text(
        "def work():\n    return 1\n",
        encoding="utf-8",
    )
    (pkg / "main.py").write_text(
        "from app.worker import work\n"
        "\n"
        "def run(flag: bool = True):\n"
        "    if flag:\n"
        "        work()\n"
        "    return 1\n",
        encoding="utf-8",
    )

    return repo


def _run_analyze_from_args(args) -> None:
    analyze_command(
        root=Path(args.root),
        out=Path(args.out),
        mode=ModeType(args.mode),
        focus=args.focus,
        module=args.module,
        max_depth=args.max_depth,
        debug_resolution=args.debug_resolution,
        parser_engine=args.parser_engine,
    )


@pytest.mark.parametrize("flag", ["--version", "-v"])
def test_cli_version_flag_prints_package_version(flag: str, capsys) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([flag])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert captured.out == f"codemarp {package_version()}\n"


def test_cli_smoke_full_mode_writes_expected_outputs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(["analyze", str(repo), "--out", str(out_dir)])

    _run_analyze_from_args(args)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "mid_level.mmd").exists()
    assert (out_dir / "mid_level.json").exists()


def test_cli_smoke_trace_mode_writes_expected_outputs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            str(repo),
            "--mode",
            "trace",
            "--focus",
            "app.main:run",
            "--max-depth",
            "2",
            "--parser-engine",
            "tree-sitter",
            "--out",
            str(out_dir),
        ]
    )

    _run_analyze_from_args(args)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "mid_level.mmd").exists()
    assert (out_dir / "mid_level.json").exists()


def test_cli_smoke_trace_mode_writes_expected_outputs_with_ast(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            str(repo),
            "--mode",
            "trace",
            "--focus",
            "app.main:run",
            "--max-depth",
            "2",
            "--out",
            str(out_dir),
        ]
    )

    _run_analyze_from_args(args)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "mid_level.mmd").exists()
    assert (out_dir / "mid_level.json").exists()


def test_cli_smoke_low_mode_writes_expected_outputs_and_styles(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            str(repo),
            "--mode",
            "low",
            "--focus",
            "app.main:run",
            "--out",
            str(out_dir),
        ]
    )

    _run_analyze_from_args(args)

    low_level_mmd = out_dir / "low_level.mmd"
    low_level_json = out_dir / "low_level.json"

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert low_level_mmd.exists()
    assert low_level_json.exists()

    content = low_level_mmd.read_text(encoding="utf-8")
    assert "classDef decision" in content
    assert "classDef merge" in content
    assert "classDef terminal" in content


def test_cli_smoke_module_mode_writes_expected_outputs(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            str(repo),
            "--mode",
            "module",
            "--module",
            "app.main",
            "--out",
            str(out_dir),
        ]
    )

    _run_analyze_from_args(args)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "mid_level.mmd").exists()
    assert (out_dir / "mid_level.json").exists()


def test_cli_smoke_debug_resolution_prints_reasons(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    out_dir = tmp_path / "out"

    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            str(repo),
            "--out",
            str(out_dir),
            "--debug-resolution",
        ]
    )

    _run_analyze_from_args(args)

    captured = capsys.readouterr()

    assert "app.main:run -> app.worker:work" in captured.out
    assert "[imported_symbol]" in captured.out
