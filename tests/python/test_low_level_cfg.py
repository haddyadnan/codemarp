import ast
from pathlib import Path

from codemarp.analyzers.low_level import ControlFlowBuilder, build_low_level_mode


def test_low_level_builds_linear_flow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n    x = 1\n    return x\n",
        encoding="utf-8",
    )

    result = build_low_level_mode(repo, "app.main:run")

    labels = [node.label for node in result.nodes]
    assert labels[0] == "Start"
    assert "x = 1" in labels
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

    result = build_low_level_mode(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "flag" in labels
    assert "Then" not in labels
    assert "Else" not in labels
    assert "Merge" not in labels
    assert "Return" in labels

    labeled_edges = {(edge.label, edge.kind) for edge in result.edges}
    assert ("True", "control_flow") in labeled_edges
    assert ("False", "control_flow") in labeled_edges
    assert "True" not in labels
    assert "False" not in labels


def test_low_level_builds_loop_flow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run(items):\n    for item in items:\n        x = item\n    return 1\n",
        encoding="utf-8",
    )

    result = build_low_level_mode(repo, "app.main:run")

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

    result = build_low_level_mode(repo, "app.main:Service.run")
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

    result = build_low_level_mode(repo, "app.main:run")
    assert result.function_id == "app.main:run"
    assert any(node.label == "Return" for node in result.nodes)


def test_low_level_if_without_else_does_not_create_false_node(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run(flag):\n    if flag:\n        x = 1\n    return 2\n",
        encoding="utf-8",
    )

    result = build_low_level_mode(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "False" not in labels
    assert "True" not in labels

    labeled_edges = {(edge.label, edge.kind) for edge in result.edges}
    assert ("True", "control_flow") in labeled_edges
    assert ("False", "control_flow") in labeled_edges


def test_low_level_simplifies_call_statement_labels(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n"
        "    print('hello', 1, 2, 3)\n"
        "    export_low_level(build_result='x', low_view='y', out_dir='z')\n",
        encoding="utf-8",
    )

    result = build_low_level_mode(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "print(...)" in labels
    assert "export_low_level(...)" in labels


def test_low_level_simplifies_assignment_call_labels(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n    value = make_value(a=1, b=2)\n",
        encoding="utf-8",
    )

    result = build_low_level_mode(repo, "app.main:run")

    labels = {node.label for node in result.nodes}
    assert "value = make_value(...)" in labels
    assert "Assign" not in labels


def test_low_level_compacts_long_call_labels() -> None:
    builder = ControlFlowBuilder()
    expr = ast.parse(
        "print('this is a very long message that should be compacted')"
    ).body[0]

    label = builder._statement_label(expr)

    assert label.startswith("print(")
    assert "..." in label
