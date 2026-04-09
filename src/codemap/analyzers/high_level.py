from codemap.graph.models import Edge, ModuleNode
from codemap.parser.python_parser import ParsedPythonModule


def build_high_level_edges(
    parsed_modules: list[ParsedPythonModule],
    modules: list[ModuleNode],
) -> tuple:
    module_to_group = {module.id: aggregate_module_id(module.id) for module in modules}
    group_ids = sorted(set(module_to_group.values()))

    known_module_ids = set(module_to_group.keys())
    edges: list[Edge] = []

    for parsed in parsed_modules:
        source_group = module_to_group.get(
            parsed.module_id, aggregate_module_id(parsed.module_id)
        )

        for imported in parsed.imports:
            target_module = _resolve_local_import(imported, known_module_ids)
            if not target_module:
                continue

            target_group = module_to_group.get(
                target_module, aggregate_module_id(target_module)
            )

            if source_group != target_group:
                edges.append(
                    Edge(
                        source=source_group,
                        target=target_group,
                        kind="imports",
                        label="imports",
                    )
                )

    return group_ids, _dedupe_edges(edges)


def aggregate_module_id(module_id: str) -> str:
    """
    Collapse deep module paths for the high-level graph.

    - 3+ segments collapse to the first 2 segments:
      codemap.views.trace -> codemap.views
    - 1–2 segments stay as-is:
      codemap.errors -> codemap.errors
      codemap.cli -> codemap.cli
    """
    segments = module_id.split(".")
    if len(segments) >= 3:
        return ".".join(segments[:2])
    return module_id


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
