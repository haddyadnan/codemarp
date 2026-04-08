from codemap.graph.models import Edge, ModuleNode
from codemap.parser.python_parser import ParsedPythonModule, package_from_module_id


def build_high_level_edges(
    parsed_modules: list[ParsedPythonModule],
    modules: list[ModuleNode],
) -> tuple:
    module_to_package = {module.id: module.package for module in modules}
    package_ids = sorted({module.package for module in modules if module.package})

    known_module_ids = set(module_to_package.keys())
    edges: list[Edge] = []

    for parsed in parsed_modules:
        source_package = module_to_package.get(
            parsed.module_id, package_from_module_id(parsed.module_id)
        )
        if not source_package:
            continue

        for imported in parsed.imports:
            target_module = _resolve_local_import(imported, known_module_ids)
            if not target_module:
                continue

            target_package = module_to_package.get(
                target_module, package_from_module_id(target_module)
            )
            if not target_package:
                continue

            if source_package != target_package:
                edges.append(
                    Edge(
                        source=source_package,
                        target=target_package,
                        kind="imports",
                        label="imports",
                    )
                )

    return package_ids, _dedupe_edges(edges)


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
