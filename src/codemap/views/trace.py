from collections import deque

from codemap.errors import TraceError
from codemap.graph.models import GraphBundle
from codemap.views.subgraph import build_function_subgraph


def _build_call_adjacency(bundle: GraphBundle) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in bundle.edges:
        if edge.kind != "calls":
            continue
        adjacency.setdefault(edge.source, set()).add(edge.target)
    return adjacency


def trace_functions_forward(
    bundle: GraphBundle, entrypoint_id: str, max_depth: int | None = None
) -> set[str]:
    _validate_entrypoint(bundle, entrypoint_id)
    adjacency = _build_call_adjacency(bundle)

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(entrypoint_id, 0)])

    while queue:
        node_id, depth = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        if max_depth is not None and depth >= max_depth:
            continue

        for neighbor in adjacency.get(node_id, set()):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))

    return visited


def trace_function_view(
    bundle: GraphBundle, entrypoint_id: str, max_depth: int | None = None
) -> GraphBundle:
    _validate_entrypoint(bundle, entrypoint_id)
    function_ids = trace_functions_forward(bundle, entrypoint_id, max_depth=max_depth)
    return build_function_subgraph(bundle, function_ids)


def trace_functions_reverse(
    bundle: GraphBundle, entrypoint_id: str, max_depth: int | None = None
) -> set[str]:
    _validate_entrypoint(bundle, entrypoint_id)
    adjacency = _build_reverse_call_adjacency(bundle)

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(entrypoint_id, 0)])

    while queue:
        node_id, depth = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        if max_depth is not None and depth >= max_depth:
            continue

        for neighbor in adjacency.get(node_id, set()):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))

    return visited


def _build_reverse_call_adjacency(bundle: GraphBundle) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in bundle.edges:
        if edge.kind != "calls":
            continue
        adjacency.setdefault(edge.target, set()).add(edge.source)
    return adjacency


def reverse_trace_function_view(
    bundle: GraphBundle,
    entrypoint_id: str,
    max_depth: int | None = None,
) -> GraphBundle:
    _validate_entrypoint(bundle, entrypoint_id)
    function_ids = trace_functions_reverse(bundle, entrypoint_id, max_depth=max_depth)
    return build_function_subgraph(bundle, function_ids)


def _validate_entrypoint(bundle: GraphBundle, entrypoint_id: str) -> None:
    if bundle.function_by_id(entrypoint_id) is None:
        raise TraceError(f"Entrypoint not found: {entrypoint_id}")
