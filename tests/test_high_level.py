from codemap.analyzers.high_level import aggregate_module_id, build_high_level_edges
from codemap.exporters.mermaid import export_module_graph
from codemap.graph.models import ModuleNode
from codemap.parser.python_parser import ParsedPythonModule


def test_aggregate_module_id() -> None:
    assert aggregate_module_id("codemap.views.trace") == "codemap.views"
    assert aggregate_module_id("codemap.graph.models.extras") == "codemap.graph"
    assert aggregate_module_id("codemap.errors") == "codemap.errors"
    assert aggregate_module_id("codemap.cli") == "codemap.cli"
    assert aggregate_module_id("mypackage") == "mypackage"


def test_high_level_aggregates_to_group_edges() -> None:
    modules = [
        ModuleNode(
            id="codemap.cli.main", path="codemap/cli/main.py", package="codemap.cli"
        ),
        ModuleNode(
            id="codemap.parser.python_parser",
            path="codemap/parser/python_parser.py",
            package="codemap.parser",
        ),
        ModuleNode(
            id="codemap.graph.builder",
            path="codemap/graph/builder.py",
            package="codemap.graph",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemap.cli.main",
            path="codemap/cli/main.py",
            imports=["codemap.parser.python_parser", "codemap.graph.builder"],
        ),
        ParsedPythonModule(
            module_id="codemap.parser.python_parser",
            path="codemap/parser/python_parser.py",
            imports=["codemap.graph.builder"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert group_ids == ["codemap.cli", "codemap.graph", "codemap.parser"]
    assert {(edge.source, edge.target) for edge in edges} == {
        ("codemap.cli", "codemap.parser"),
        ("codemap.cli", "codemap.graph"),
        ("codemap.parser", "codemap.graph"),
    }


def test_high_level_keeps_top_level_modules_distinct() -> None:
    modules = [
        ModuleNode(
            id="codemap.cli.main", path="codemap/cli/main.py", package="codemap.cli"
        ),
        ModuleNode(id="codemap.errors", path="codemap/errors.py", package="codemap"),
        ModuleNode(
            id="codemap.views.trace",
            path="codemap/views/trace.py",
            package="codemap.views",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemap.cli.main",
            path="codemap/cli/main.py",
            imports=["codemap.errors", "codemap.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert "codemap.errors" in group_ids
    assert "codemap.views" in group_ids
    assert "codemap" not in group_ids

    assert {(edge.source, edge.target) for edge in edges} == {
        ("codemap.cli", "codemap.errors"),
        ("codemap.cli", "codemap.views"),
    }


def test_high_level_dedupes_same_group_relationships() -> None:
    modules = [
        ModuleNode(id="pkg.a.one", path="pkg/a/one.py", package="pkg.a"),
        ModuleNode(id="pkg.a.two", path="pkg/a/two.py", package="pkg.a"),
        ModuleNode(id="pkg.b.core", path="pkg/b/core.py", package="pkg.b"),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="pkg.a.one", path="pkg/a/one.py", imports=["pkg.b.core"]
        ),
        ParsedPythonModule(
            module_id="pkg.a.two", path="pkg/a/two.py", imports=["pkg.b.core"]
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert group_ids == ["pkg.a", "pkg.b"]
    assert len(edges) == 1
    assert edges[0].source == "pkg.a"
    assert edges[0].target == "pkg.b"


def test_export_module_graph_renders_groups_and_top_level_modules_differently() -> None:
    modules = [
        ModuleNode(
            id="codemap.cli.main", path="codemap/cli/main.py", package="codemap.cli"
        ),
        ModuleNode(id="codemap.errors", path="codemap/errors.py", package="codemap"),
        ModuleNode(
            id="codemap.views.trace",
            path="codemap/views/trace.py",
            package="codemap.views",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemap.cli.main",
            path="codemap/cli/main.py",
            imports=["codemap.errors", "codemap.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)
    mermaid = export_module_graph(group_ids, edges, modules)

    assert 'codemap_views["codemap.views"]' in mermaid
    assert 'codemap_errors(["codemap.errors"])' in mermaid
    assert "codemap -->" not in mermaid
