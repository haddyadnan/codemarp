from codemarp.analyzers.high_level import aggregate_module_id, build_high_level_edges
from codemarp.exporters.mermaid import export_module_graph
from codemarp.graph.models import ModuleNode
from codemarp.parser.python_parser import ParsedPythonModule


def test_aggregate_module_id() -> None:
    assert aggregate_module_id("codemarp.views.trace") == "codemarp.views"
    assert aggregate_module_id("codemarp.graph.models.extras") == "codemarp.graph"
    assert aggregate_module_id("codemarp.errors") == "codemarp.errors"
    assert aggregate_module_id("codemarp.cli") == "codemarp.cli"
    assert aggregate_module_id("mypackage") == "mypackage"


def test_high_level_aggregates_to_group_edges() -> None:
    modules = [
        ModuleNode(
            id="codemarp.cli.main", path="codemarp/cli/main.py", package="codemarp.cli"
        ),
        ModuleNode(
            id="codemarp.parser.python_parser",
            path="codemarp/parser/python_parser.py",
            package="codemarp.parser",
        ),
        ModuleNode(
            id="codemarp.graph.builder",
            path="codemarp/graph/builder.py",
            package="codemarp.graph",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemarp.cli.main",
            path="codemarp/cli/main.py",
            imports=["codemarp.parser.python_parser", "codemarp.graph.builder"],
        ),
        ParsedPythonModule(
            module_id="codemarp.parser.python_parser",
            path="codemarp/parser/python_parser.py",
            imports=["codemarp.graph.builder"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert group_ids == ["codemarp.cli", "codemarp.graph", "codemarp.parser"]
    assert {(edge.source, edge.target) for edge in edges} == {
        ("codemarp.cli", "codemarp.parser"),
        ("codemarp.cli", "codemarp.graph"),
        ("codemarp.parser", "codemarp.graph"),
    }


def test_high_level_keeps_top_level_modules_distinct() -> None:
    modules = [
        ModuleNode(
            id="codemarp.cli.main", path="codemarp/cli/main.py", package="codemarp.cli"
        ),
        ModuleNode(id="codemarp.errors", path="codemarp/errors.py", package="codemarp"),
        ModuleNode(
            id="codemarp.views.trace",
            path="codemarp/views/trace.py",
            package="codemarp.views",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemarp.cli.main",
            path="codemarp/cli/main.py",
            imports=["codemarp.errors", "codemarp.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert "codemarp.errors" in group_ids
    assert "codemarp.views" in group_ids
    assert "codemarp" not in group_ids

    assert {(edge.source, edge.target) for edge in edges} == {
        ("codemarp.cli", "codemarp.errors"),
        ("codemarp.cli", "codemarp.views"),
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
            id="codemarp.cli.main", path="codemarp/cli/main.py", package="codemarp.cli"
        ),
        ModuleNode(id="codemarp.errors", path="codemarp/errors.py", package="codemarp"),
        ModuleNode(
            id="codemarp.views.trace",
            path="codemarp/views/trace.py",
            package="codemarp.views",
        ),
    ]

    parsed_modules = [
        ParsedPythonModule(
            module_id="codemarp.cli.main",
            path="codemarp/cli/main.py",
            imports=["codemarp.errors", "codemarp.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)
    mermaid = export_module_graph(group_ids, edges, modules)

    assert 'codemarp_views["codemarp.views"]' in mermaid
    assert 'codemarp_errors(["codemarp.errors"])' in mermaid
    assert "codemarp -->" not in mermaid
