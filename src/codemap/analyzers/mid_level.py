from codemap.graph.models import Edge, FunctionNode
from codemap.parser.python_parser import ParsedPythonModule


def build_mid_level_edges(
    parsed_modules: list[ParsedPythonModule], functions: list[FunctionNode]
) -> list[Edge]:
    edges = []
    by_name = {}
    for fn in functions:
        by_name.setdefault(fn.name, []).append(fn)
        by_name.setdefault(fn.name.split(".")[-1], []).append(fn)

    for module in parsed_modules:
        for caller_id, callee_name in module.calls:
            target = _resolve_callee(module.module_id, callee_name, by_name)
            if target:
                edges.append(
                    Edge(
                        source=caller_id, target=target.id, kind="calls", label="calls"
                    )
                )
    return _dedupe_edges(edges)


def _resolve_callee(
    module_id: str, callee_name: str, by_name: dict
) -> FunctionNode | None:
    matches = by_name.get(callee_name, [])
    if not matches and "." in callee_name:
        matches = by_name.get(callee_name.split(".")[-1], [])
    same_module = [fn for fn in matches if fn.module_id == module_id]
    if same_module:
        return same_module[0]
    unique = list({fn.id: fn for fn in matches}.values())
    if len(unique) == 1:
        return unique[0]
    return None


def _dedupe_edges(edges: list[Edge]) -> list[Edge]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Edge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.kind)
        if key not in seen:
            seen.add(key)
            out.append(edge)
    return out
