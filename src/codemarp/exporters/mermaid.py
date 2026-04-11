from codemarp.analyzers.high_level import aggregate_module_id
from codemarp.graph.models import ControlFlowNode, Edge, FunctionNode, ModuleNode


def export_module_graph(
    group_ids: list[str], edges: list[Edge], modules: list[ModuleNode]
) -> str:
    lines = ["flowchart LR"]
    collapsed_groups = _collapsed_group_ids(modules)

    for group_id in group_ids:
        if group_id in collapsed_groups:
            lines.append(f'    {_safe_id(group_id)}["{group_id}"]')
        else:
            lines.append(f'    {_safe_id(group_id)}(["{group_id}"])')

    for edge in edges:
        if edge.kind == "imports":
            if edge.label:
                lines.append(
                    f"    {_safe_id(edge.source)} -->|{edge.label}| {_safe_id(edge.target)}"
                )
            else:
                lines.append(f"    {_safe_id(edge.source)} --> {_safe_id(edge.target)}")

    return "\n".join(lines)


def export_function_graph(functions: list[FunctionNode], edges: list[Edge]) -> str:
    lines = ["flowchart LR"]
    for fn in functions:
        label = f"{fn.module_id}:{fn.name}"
        lines.append(f'    {_safe_id(fn.id)}["{label}"]')
    for edge in edges:
        if edge.kind == "calls":
            if edge.label:
                lines.append(
                    f"    {_safe_id(edge.source)} -->|{edge.label}| {_safe_id(edge.target)}"
                )
            else:
                lines.append(f"    {_safe_id(edge.source)} --> {_safe_id(edge.target)}")
    return "\n".join(lines)


def export_control_flow(nodes: list[ControlFlowNode], edges: list[Edge]) -> str:
    lines = ["flowchart TD"]
    for node in nodes:
        lines.append(f'    {_safe_id(node.id)}["{node.label}"]')
    for edge in edges:
        if edge.label:
            lines.append(
                f"    {_safe_id(edge.source)} -->|{edge.label}| {_safe_id(edge.target)}"
            )
        else:
            lines.append(f"    {_safe_id(edge.source)} --> {_safe_id(edge.target)}")
    return "\n".join(lines)


def _collapsed_group_ids(modules: list[ModuleNode]) -> set[str]:
    collapsed: set[str] = set()
    for module in modules:
        group_id = aggregate_module_id(module.id)
        if group_id != module.id:
            collapsed.add(group_id)
    return collapsed


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value)


def _shape_for_kind(kind: str) -> tuple[str, str]:
    if kind == "decision":
        return "{", "}"
    if kind in {"start", "end", "terminal"}:
        return "([", "])"
    return "[", "]"


def export_low_level_graph(nodes: list[ControlFlowNode], edges: list[Edge]) -> str:
    lines = ["flowchart TD"]
    for node in nodes:
        left, right = _shape_for_kind(node.kind)
        label = node.label.replace('"', "'")
        lines.append(f'    {_safe_id(node.id)}{left}"{label}"{right}')
    for edge in edges:
        if edge.kind != "control_flow":
            continue
        if edge.label:
            lines.append(
                f"    {_safe_id(edge.source)} -->|{edge.label}| {_safe_id(edge.target)}"
            )
        else:
            lines.append(f"    {_safe_id(edge.source)} --> {_safe_id(edge.target)}")
    return "\n".join(lines)
