import json
from pathlib import Path

from codemarp.exporters.json_exporter import export_bundle_json
from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode
from codemarp.pipeline.apply_mode import ModeType, apply_mode
from codemarp.pipeline.build_bundle import build_bundle
from codemarp.pipeline.render_mode import render_mode_to_json


def test_export_bundle_json_structure(tmp_path: Path) -> None:
    bundle = GraphBundle(
        modules=[
            ModuleNode(
                id="app.main",
                path=Path("app/main.py"),
                package="app",
                language="python",
            )
        ],
        functions=[
            FunctionNode(
                id="app.main:run",
                module_id="app.main",
                name="run",
                lineno=1,
                end_lineno=3,
            )
        ],
        edges=[
            Edge(
                source="app.main:run",
                target="app.main:helper",
                kind="calls",
                label="calls",
            )
        ],
    )

    out = tmp_path / "graph.json"
    export_bundle_json(bundle, out)

    data = json.loads(out.read_text())

    assert set(data) == {"nodes", "edges"}

    module_node = next(node for node in data["nodes"] if node["kind"] == "module")
    assert module_node == {
        "id": "app.main",
        "label": "app.main",
        "kind": "module",
        "file_path": "app/main.py",
        "language": "python",
    }

    function_node = next(node for node in data["nodes"] if node["kind"] == "function")
    assert function_node["id"] == "app.main:run"
    assert function_node["label"] == "run"
    assert function_node["kind"] == "function"
    assert function_node["module_id"] == "app.main"
    assert function_node["file_path"] == "app/main.py"
    assert function_node["language"] == "python"

    edge = data["edges"][0]
    assert edge["source"] == "app.main:run"
    assert edge["target"] == "app.main:helper"
    assert edge["kind"] == "calls"
    assert edge["label"] == "calls"
    assert edge["resolution_kind"] is None


def test_render_mode_to_json_matches_function_graph_edges() -> None:
    build_result = build_bundle(Path("src"))
    graph_mode = apply_mode(
        build_result.bundle,
        mode=ModeType.TRACE,
        focus="codemarp.cli.main:analyze_command",
    )

    graph_json = render_mode_to_json(
        build_result,
        mode=ModeType.TRACE,
        graph_mode=graph_mode,
    )

    json_node_ids = {node["id"] for node in graph_json["nodes"]}
    json_edges = {
        (edge["source"], edge["target"], edge["kind"]) for edge in graph_json["edges"]
    }

    mermaid_node_ids = {fn.id for fn in graph_mode.functions}
    mermaid_edges = {
        (edge.source, edge.target, edge.kind)
        for edge in graph_mode.edges
        if edge.kind == "calls"
    }

    assert json_node_ids == mermaid_node_ids
    assert json_edges == mermaid_edges


def test_render_mode_to_json_matches_full_graph_edges() -> None:
    build_result = build_bundle(Path("src"))

    graph_json = render_mode_to_json(
        build_result,
        mode=ModeType.FULL,
    )

    json_node_ids = {node["id"] for node in graph_json["nodes"]}
    json_edges = {
        (edge["source"], edge["target"], edge["kind"]) for edge in graph_json["edges"]
    }

    expected_node_ids = set(build_result.high_level_package_ids)
    expected_edges = {
        (edge.source, edge.target, edge.kind) for edge in build_result.high_level_edges
    }

    assert json_node_ids == expected_node_ids
    assert json_edges == expected_edges
