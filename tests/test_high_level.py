from pathlib import Path

from codemarp.analyzers.high_level import aggregate_module_id, build_high_level_edges
from codemarp.exporters.mermaid import export_module_graph
from codemarp.graph.models import ModuleNode
from codemarp.parser.contracts import ImportFact, ParsedModule


def _parsed_module(module_id: str, path: str, imports: list[str]) -> ParsedModule:
    return ParsedModule(
        module_id=module_id,
        file_path=Path(path),
        language="python",
        imports=[
            ImportFact(
                raw_module=import_name,
                imported_name=None,
                alias=None,
                is_from_import=False,
                relative_level=0,
                lineno=1,
            )
            for import_name in imports
        ],
        functions=[],
        calls=[],
        control_flow_roots=[],
    )


def test_high_level_aggregates_to_group_edges() -> None:
    modules = [
        ModuleNode(
            id="codemarp.cli.main",
            path=Path("codemarp/cli/main.py"),
            package="codemarp.cli",
        ),
        ModuleNode(
            id="codemarp.parser.python_parser",
            path=Path("codemarp/parser/python_parser.py"),
            package="codemarp.parser",
        ),
        ModuleNode(
            id="codemarp.graph.builder",
            path=Path("codemarp/graph/builder.py"),
            package="codemarp.graph",
        ),
    ]

    parsed_modules = [
        _parsed_module(
            "codemarp.cli.main",
            "codemarp/cli/main.py",
            ["codemarp.parser.python_parser", "codemarp.graph.builder"],
        ),
        _parsed_module(
            "codemarp.parser.python_parser",
            "codemarp/parser/python_parser.py",
            ["codemarp.graph.builder"],
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
            id="codemarp.cli.main",
            path=Path("codemarp/cli/main.py"),
            package="codemarp.cli",
        ),
        ModuleNode(
            id="codemarp.errors", path=Path("codemarp/errors.py"), package="codemarp"
        ),
        ModuleNode(
            id="codemarp.views.trace",
            path=Path("codemarp/views/trace.py"),
            package="codemarp.views",
        ),
    ]

    parsed_modules = [
        _parsed_module(
            "codemarp.cli.main",
            "codemarp/cli/main.py",
            ["codemarp.errors", "codemarp.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert "codemarp.errors" in group_ids
    assert "codemarp.cli" in group_ids
    assert "codemarp.views" in group_ids
    assert {(edge.source, edge.target) for edge in edges} == {
        ("codemarp.cli", "codemarp.errors"),
        ("codemarp.cli", "codemarp.views"),
    }


def test_high_level_dedupes_same_group_relationships() -> None:
    modules = [
        ModuleNode(id="pkg.a.one", path=Path("pkg/a/one.py"), package="pkg.a"),
        ModuleNode(id="pkg.a.two", path=Path("pkg/a/two.py"), package="pkg.a"),
        ModuleNode(id="pkg.b.core", path=Path("pkg/b/core.py"), package="pkg.b"),
    ]

    parsed_modules = [
        _parsed_module("pkg.a.one", "pkg/a/one.py", ["pkg.b.core"]),
        _parsed_module("pkg.a.two", "pkg/a/two.py", ["pkg.b.core"]),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert group_ids == ["pkg.a", "pkg.b"]
    assert len(edges) == 1
    assert edges[0].source == "pkg.a"
    assert edges[0].target == "pkg.b"


def test_export_module_graph_renders_groups_and_top_level_modules_differently() -> None:
    modules = [
        ModuleNode(
            id="codemarp.cli.main",
            path=Path("codemarp/cli/main.py"),
            package="codemarp.cli",
        ),
        ModuleNode(
            id="codemarp.errors", path=Path("codemarp/errors.py"), package="codemarp"
        ),
        ModuleNode(
            id="codemarp.views.trace",
            path=Path("codemarp/views/trace.py"),
            package="codemarp.views",
        ),
    ]

    parsed_modules = [
        _parsed_module(
            "codemarp.cli.main",
            "codemarp/cli/main.py",
            ["codemarp.errors", "codemarp.views.trace"],
        ),
    ]

    group_ids, edges = build_high_level_edges(parsed_modules, modules)
    mermaid = export_module_graph(group_ids, edges, modules)

    assert 'codemarp_cli["codemarp.cli"]' in mermaid
    assert 'codemarp_errors(["codemarp.errors"])' in mermaid
    assert "codemarp_cli -->|imports| codemarp_errors" in mermaid
    assert "codemarp_cli -->|imports| codemarp_views" in mermaid


def test_aggregate_module_id_collapses_only_deep_modules() -> None:
    assert aggregate_module_id("codemarp.views.trace") == "codemarp.views"
    assert aggregate_module_id("codemarp.cli.main") == "codemarp.cli"
    assert aggregate_module_id("codemarp.errors") == "codemarp.errors"
    assert aggregate_module_id("codemarp") == "codemarp"
