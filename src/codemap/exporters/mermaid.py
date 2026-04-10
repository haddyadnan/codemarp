from codemap.graph.models import ControlFlowNode, Edge, FunctionNode


def export_module_graph(package_ids: list[str], edges: list[Edge]) -> str:
    lines = ["flowchart LR"]
    for package_id in package_ids:
        lines.append(f'    {_safe_id(package_id)}["{package_id}"]')
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
