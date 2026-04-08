from codemap.graph.models import Edge
from codemap.parser.python_parser import ParsedPythonModule


def build_high_level_edges(
    parsed_modules: list[ParsedPythonModule], known_module_ids: set[str]
) -> list[Edge]:
    edges = []
    for module in parsed_modules:
        for imported in module.imports:
            target = _resolve_local_import(imported, known_module_ids)
            if target and target != module.module_id:
                edges.append(
                    Edge(
                        source=module.module_id,
                        target=target,
                        kind="imports",
                        label="imports",
                    )
                )
    return _dedupe_edges(edges)


def _resolve_local_import(import_name: str, known_module_ids: set[str]) -> str | None:
    if import_name in known_module_ids:
        return import_name
    for module_id in sorted(known_module_ids, key=len, reverse=True):
        if import_name.startswith(module_id + "."):
            return module_id
        if module_id.startswith(import_name + "."):
            return module_id
    return None


def _dedupe_edges(edges: list[Edge]) -> list[Edge]:
    seen = set()
    out = []
    for edge in edges:
        key = (edge.source, edge.target, edge.kind)
        if key not in seen:
            seen.add(key)
            out.append(edge)
    return out
