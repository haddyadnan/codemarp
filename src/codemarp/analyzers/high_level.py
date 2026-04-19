from pathlib import PurePosixPath

from codemarp.graph.models import Edge, ModuleNode
from codemarp.parser.contracts import ImportFact, ParsedModule


def build_high_level_edges(
    parsed_modules: list[ParsedModule],
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
            target_module = _resolve_local_import(
                parsed.module_id, imported, known_module_ids
            )
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
      codemarp.views.trace -> codemarp.views
    - 1–2 segments stay as-is:
      codemarp.errors -> codemarp.errors
      codemarp.cli -> codemarp.cli
    """
    segments = module_id.split(".")
    if len(segments) >= 3:
        return ".".join(segments[:2])
    return module_id


def _resolve_local_import(
    current_module_id: str, imported: ImportFact, known_module_ids: set[str]
) -> str | None:
    # if imported.relative_level != 0:
    #     return None

    import_name = imported.raw_module

    if import_name is None:
        return None

    # if import_name in known_module_ids:
    #     return import_name

    for candidate in _import_name_candidates(current_module_id, import_name):
        if candidate in known_module_ids:
            return candidate

        for module_id in sorted(known_module_ids, key=len, reverse=True):
            if candidate.startswith(module_id + "."):
                return module_id
            if module_id.startswith(candidate + "."):
                return module_id
    return None


def _import_name_candidates(current_module_id: str, import_name: str) -> list[str]:
    candidates = []

    normalized = import_name
    for suffix in (".js", ".ts", ".tsx", ".jsx", ".mjs", ".mts", ".cjs", ".cts"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    candidates.append(normalized)

    if normalized.startswith("./") or normalized.startswith("../"):
        current_parts = current_module_id.split(".")
        base_parts = current_parts[:-1]

        resolved_path = PurePosixPath("/".join(base_parts)) / normalized
        normalized_path = resolved_path.as_posix()

        while normalized_path.startswith("./"):
            normalized_path = normalized_path[2:]

        candidates.append(normalized_path.replace("/", "."))

    seen: set[str] = set()
    out: list[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            out.append(candidate)

    return out


def _dedupe_edges(edges: list[Edge]) -> list[Edge]:
    seen = set()
    out = []
    for edge in edges:
        key = (edge.source, edge.target, edge.kind)
        if key not in seen:
            seen.add(key)
            out.append(edge)
    return out
