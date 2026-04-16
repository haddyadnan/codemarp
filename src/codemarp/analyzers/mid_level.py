from codemarp.graph.models import Edge, FunctionNode
from codemarp.parser.contracts import CallFact, ParsedModule


def build_mid_level_edges(
    parsed_modules: list[ParsedModule], functions: list[FunctionNode]
) -> list[Edge]:
    edges = []
    by_name = {}
    by_id = {fn.id: fn for fn in functions}
    by_module_and_name = {}

    for fn in functions:
        by_name.setdefault(fn.name, []).append(fn)
        by_name.setdefault(fn.name.split(".")[-1], []).append(fn)
        by_module_and_name[(fn.module_id, fn.name)] = fn
        by_module_and_name[(fn.module_id, fn.name.split(".")[-1])] = fn

    parsed_by_module = {parsed.module_id: parsed for parsed in parsed_modules}

    for module in parsed_modules:
        for call in module.calls:
            target = _resolve_callee(
                caller_module_id=module.module_id,
                call=call,
                parsed_by_module=parsed_by_module,
                by_module_and_name=by_module_and_name,
                by_name=by_name,
                by_id=by_id,
            )
            if target:
                edges.append(
                    Edge(
                        source=call.caller_id,
                        target=target.id,
                        kind="calls",
                        label="calls",
                    )
                )
    return _dedupe_edges(edges)


def _resolve_callee(
    caller_module_id: str,
    call: CallFact,
    parsed_by_module: dict,
    by_module_and_name: dict,
    by_name: dict,
    by_id: dict,
) -> FunctionNode | None:
    parsed_module = parsed_by_module[caller_module_id]

    if call.kind == "bare":
        same_module = _resolve_same_module_call(
            caller_module_id=caller_module_id,
            callee_name=call.leaf_name,
            by_module_and_name=by_module_and_name,
        )

        if same_module:
            return same_module

    imported_symbol = _resolve_imported_symbol_call(
        parsed_module=parsed_module,
        callee_name=call.leaf_name,
        by_id=by_id,
        by_module_and_name=by_module_and_name,
    )

    if imported_symbol:
        return imported_symbol

    imported_module = _resolve_imported_module_call(
        parsed_module=parsed_module,
        callee_name=call.raw,
        by_module_and_name=by_module_and_name,
    )

    if imported_module:
        return imported_module

    if call.kind != "bare":
        return None

    return _resolve_unique_global_call(callee_name=call.leaf_name, by_name=by_name)


def _resolve_same_module_call(
    *,
    caller_module_id: str,
    callee_name: str,
    by_module_and_name: dict[tuple[str, str], FunctionNode],
) -> FunctionNode | None:
    return by_module_and_name.get((caller_module_id, callee_name))


def _resolve_imported_symbol_call(
    parsed_module: ParsedModule,
    callee_name: str,
    by_id: dict,
    by_module_and_name: dict,
) -> FunctionNode | None:
    if "." in callee_name:
        return None

    for imported in parsed_module.imports:
        if not imported.is_from_import or imported.imported_name is None:
            continue

        visible_name = imported.alias or imported.imported_name
        if visible_name != callee_name:
            continue

        direct_id = f"{imported.raw_module}:{imported.imported_name}"
        if direct_id in by_id:
            return by_id[direct_id]

        candidate = by_module_and_name.get(
            (imported.raw_module, imported.imported_name)
        )
        if candidate:
            return candidate

    return None


def _resolve_imported_module_call(
    parsed_module: ParsedModule,
    callee_name: str,
    by_module_and_name: dict,
) -> FunctionNode | None:
    if "." not in callee_name:
        return None

    prefix, member = callee_name.split(".", 1)

    for imported in parsed_module.imports:
        if imported.is_from_import or imported.raw_module is None:
            continue

        visible_name = imported.alias or imported.raw_module.split(".")[-1]
        if visible_name != prefix:
            continue

        return by_module_and_name.get((imported.raw_module, member))

    return None


def _resolve_unique_global_call(
    *,
    callee_name: str,
    by_name: dict[str, list[FunctionNode]],
) -> FunctionNode | None:
    if _is_dotted_call(callee_name):
        return None

    matches = by_name.get(callee_name, [])
    unique = {fn.id: fn for fn in matches if fn.class_name is None}

    if len(unique) == 1:
        return next(iter(unique.values()))

    return None


def _is_dotted_call(callee_name: str) -> bool:
    return "." in callee_name


def _dedupe_edges(edges: list[Edge]) -> list[Edge]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Edge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.kind)
        if key not in seen:
            seen.add(key)
            out.append(edge)
    return out
