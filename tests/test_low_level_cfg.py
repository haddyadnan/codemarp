from pathlib import Path

from codemap.analyzers.low_level import build_low_level_view


def test_low_level_builds_linear_flow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n    x = 1\n    return x\n",
        encoding="utf-8",
    )

    result = build_low_level_view(repo, "app.main:run")

    labels = [node.label for node in result.nodes]
    assert labels[0] == "Start"
    assert "Assign" in labels
    assert "Return" in labels
    assert labels[-1] == "End"


def test_low_level_builds_if_flow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run(flag):\n    if flag:\n        return 1\n    else:\n        return 2\n",
        encoding="utf-8",
    )

    result = build_low_level_view(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "flag" in labels
    assert "Then" in labels
    assert "Else" in labels
    assert "Merge" in labels
    assert "Return" in labels


def test_low_level_builds_loop_flow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run(items):\n    for item in items:\n        x = item\n    return 1\n",
        encoding="utf-8",
    )

    result = build_low_level_view(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "For" in labels
    assert "Loop Body" in labels
    assert "After Loop" in labels
    assert "Return" in labels


def test_low_level_supports_method_focus(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "class Service:\n    def run(self):\n        return 1\n",
        encoding="utf-8",
    )

    result = build_low_level_view(repo, "app.main:Service.run")
    assert result.function_id == "app.main:Service.run"
    assert any(node.label == "Return" for node in result.nodes)


def test_low_level_supports_async_function(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "async def run():\n    return 1\n",
        encoding="utf-8",
    )

    result = build_low_level_view(repo, "app.main:run")
    assert result.function_id == "app.main:run"
    assert any(node.label == "Return" for node in result.nodes)
