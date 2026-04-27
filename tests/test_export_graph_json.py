import json
from pathlib import Path

from codemarp.exporters.json_exporter import export_bundle_json
from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode


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
