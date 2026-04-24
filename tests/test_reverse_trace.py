from pathlib import Path

import pytest

from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode
from codemarp.modes.trace import (
    TraceError,
    reverse_trace_function_mode,
    trace_functions_reverse,
)


def _bundle() -> GraphBundle:
    modules = [
        ModuleNode(id="app.entry", path=Path("app/entry.py"), package="app"),
        ModuleNode(id="app.service", path=Path("app/service.py"), package="app"),
        ModuleNode(id="app.worker", path=Path("app/worker.py"), package="app"),
        ModuleNode(id="app.other", path=Path("app/other.py"), package="app"),
    ]
    functions = [
        FunctionNode(
            id="app.entry:start",
            module_id="app.entry",
            name="start",
            lineno=1,
            end_lineno=2,
        ),
        FunctionNode(
            id="app.service:run",
            module_id="app.service",
            name="run",
            lineno=4,
            end_lineno=5,
        ),
        FunctionNode(
            id="app.worker:work",
            module_id="app.worker",
            name="work",
            lineno=7,
            end_lineno=8,
        ),
        FunctionNode(
            id="app.other:unused",
            module_id="app.other",
            name="unused",
            lineno=10,
            end_lineno=11,
        ),
    ]
    edges = [
        Edge(
            source="app.entry:start",
            target="app.service:run",
            kind="calls",
            label="calls",
        ),
        Edge(
            source="app.service:run",
            target="app.worker:work",
            kind="calls",
            label="calls",
        ),
        Edge(
            source="app.other:unused",
            target="app.service:run",
            kind="calls",
            label="calls",
        ),
    ]
    return GraphBundle(modules=modules, functions=functions, edges=edges)


def test_reverse_trace_finds_all_upstream_callers() -> None:
    visited = trace_functions_reverse(_bundle(), "app.worker:work")
    assert visited == {
        "app.worker:work",
        "app.service:run",
        "app.entry:start",
        "app.other:unused",
    }


def test_reverse_trace_respects_max_depth() -> None:
    visited = trace_functions_reverse(_bundle(), "app.worker:work", max_depth=1)
    assert visited == {"app.worker:work", "app.service:run"}


def test_reverse_trace_mode_builds_valid_subgraph() -> None:
    mode = reverse_trace_function_mode(_bundle(), "app.worker:work", max_depth=1)

    assert {function.id for function in mode.functions} == {
        "app.worker:work",
        "app.service:run",
    }
    assert len(mode.edges) == 1
    assert mode.edges[0].source == "app.service:run"
    assert mode.edges[0].target == "app.worker:work"


def test_reverse_trace_missing_entrypoint_raises() -> None:
    with pytest.raises(TraceError, match="Entrypoint not found"):
        reverse_trace_function_mode(_bundle(), "app.worker:missing")
