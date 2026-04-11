from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode
from codemarp.views.trace import TraceError, trace_function_view, trace_functions_forward


def _bundle() -> GraphBundle:
    modules = [
        ModuleNode(id="app.main", path="app/main.py", package="app"),
        ModuleNode(id="app.worker", path="app/worker.py", package="app"),
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


def test_trace_forward_reachable_functions() -> None:
    visited = trace_functions_forward(_bundle(), "app.main:a")
    assert visited == {"app.main:a", "app.main:b", "app.worker:c"}


def test_trace_respects_max_depth() -> None:
    visited = trace_functions_forward(_bundle(), "app.main:a", max_depth=1)
    assert visited == {"app.main:a", "app.main:b"}


def test_trace_missing_entrypoint_raises() -> None:
    try:
        trace_function_view(_bundle(), "app.main:missing")
    except TraceError as exc:
        assert "Entrypoint not found" in str(exc)
    else:
        raise AssertionError("Expected TraceError")


def test_subgraph_filters_edges_with_missing_nodes() -> None:
    subgraph = trace_function_view(_bundle(), "app.main:a", max_depth=1)
    assert {fn.id for fn in subgraph.functions} == {"app.main:a", "app.main:b"}
    assert len(subgraph.edges) == 1
    assert subgraph.edges[0].source == "app.main:a"
    assert subgraph.edges[0].target == "app.main:b"
