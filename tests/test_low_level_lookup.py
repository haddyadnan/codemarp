from pathlib import Path

import pytest

from codemarp.errors import FocusFormatError, ResolutionError
from codemarp.parser.python.low_level import find_function_node, parse_low_level_focus


def test_parse_low_level_focus_accepts_top_level_function() -> None:
    module_id, target = parse_low_level_focus("app.main:run")
    assert module_id == "app.main"
    assert target == "run"


def test_parse_low_level_focus_accepts_method() -> None:
    module_id, target = parse_low_level_focus("app.main:Service.run")
    assert module_id == "app.main"
    assert target == "Service.run"


def test_parse_low_level_focus_rejects_module_only() -> None:
    with pytest.raises(FocusFormatError, match="Invalid --focus format"):
        parse_low_level_focus("app.main")


def test_parse_low_level_focus_rejects_empty_target() -> None:
    with pytest.raises(FocusFormatError, match="Invalid --focus format"):
        parse_low_level_focus("app.main:")


def test_find_function_node_finds_top_level_function(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n    return 1\n",
        encoding="utf-8",
    )

    function_id, node = find_function_node(repo, "app.main:run")
    assert function_id == "app.main:run"
    assert node.name == "run"


def test_find_function_node_finds_method(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "class Service:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )

    function_id, node = find_function_node(repo, "app.main:Service.run")
    assert function_id == "app.main:Service.run"
    assert node.name == "run"


def test_find_function_node_raises_for_missing_module(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    with pytest.raises(ResolutionError, match="Module not found"):
        find_function_node(repo, "app.main:run")


def test_find_function_node_raises_for_missing_function(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def other():\n    return 1\n",
        encoding="utf-8",
    )

    with pytest.raises(ResolutionError, match="Function or method not found"):
        find_function_node(repo, "app.main:run")
