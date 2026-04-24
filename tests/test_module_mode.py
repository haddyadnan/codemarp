from pathlib import Path

import pytest

from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode
from codemarp.modes.module_mode import ModuleModeError, module_function_mode


def _bundle() -> GraphBundle:
    modules = [
        ModuleNode(id="app.main", path=Path("app/main.py"), package="app"),
        ModuleNode(id="app.worker", path=Path("app/worker.py"), package="app"),
    ]
    functions = [
        FunctionNode(
            id="app.main:a", module_id="app.main", name="a", lineno=1, end_lineno=2
        ),
        FunctionNode(
            id="app.main:b", module_id="app.main", name="b", lineno=4, end_lineno=5
        ),
        FunctionNode(
            id="app.worker:c", module_id="app.worker", name="c", lineno=1, end_lineno=2
        ),
    ]
    edges = [
        Edge(source="app.main:a", target="app.main:b", kind="calls", label="calls"),
        Edge(source="app.main:b", target="app.worker:c", kind="calls", label="calls"),
    ]
    return GraphBundle(modules=modules, functions=functions, edges=edges)


def test_module_mode_keeps_only_functions_in_module() -> None:
    mode = module_function_mode(_bundle(), "app.main")

    assert {function.id for function in mode.functions} == {
        "app.main:a",
        "app.main:b",
    }
    assert len(mode.edges) == 1
    assert mode.edges[0].source == "app.main:a"
    assert mode.edges[0].target == "app.main:b"


def test_module_mode_keeps_only_selected_module_node() -> None:
    mode = module_function_mode(_bundle(), "app.main")

    assert [module.id for module in mode.modules] == ["app.main"]


def test_module_mode_missing_module_raises() -> None:
    with pytest.raises(ModuleModeError, match="Module not found"):
        module_function_mode(_bundle(), "app.missing")
