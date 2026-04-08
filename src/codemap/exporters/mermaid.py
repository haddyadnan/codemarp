from codemap.graph.models import ControlFlowNode, Edge, FunctionNode, ModuleNode


def export_module_graph(modules: list[ModuleNode], edges: list[Edge]) -> str:
    lines = ["flowchart LR"]
    for module in modules:
        lines.append(f'    {_safe_id(module.id)}["{module.id}"]')
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
