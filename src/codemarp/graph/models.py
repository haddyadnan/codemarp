from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from codemarp.contracts import ResolutionReason


@dataclass(slots=True)
class ModuleNode:
    id: str
    path: Path
    package: str
    language: str = "python"


@dataclass(slots=True)
class FunctionNode:
    id: str
    module_id: str
    name: str
    lineno: int
    end_lineno: int
    class_name: Optional[str] = None


@dataclass(slots=True)
class ControlFlowNode:
    id: str
    label: str
    kind: str
    lineno: Optional[int] = None


@dataclass(slots=True)
class Edge:
    source: str
    target: str
    kind: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    label: Optional[str] = None
    reason: ResolutionReason | None = None


@dataclass(slots=True)
class GraphBundle:
    modules: List[ModuleNode] = field(default_factory=list)
    functions: List[FunctionNode] = field(default_factory=list)
    control_flow_nodes: List[ControlFlowNode] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def to_dict(self) -> dict:
        unique_modules = {m.id: m for m in self.modules}
        unique_functions = {f.id: f for f in self.functions}
        unique_cf_nodes = {n.id: n for n in self.control_flow_nodes}

        sorted_edges = sorted(self.edges, key=lambda e: (e.source, e.target, e.kind))

        return {
            "modules": [asdict(m) for m in unique_modules.values()],
            "functions": [
                asdict(unique_functions[k]) for k in sorted(unique_functions)
            ],
            "control_flow_nodes": [asdict(n) for n in unique_cf_nodes.values()],
            "edges": [asdict(e) for e in sorted_edges],
        }

    def functions_in_module(self, module_id: str) -> List[FunctionNode]:
        return [f for f in self.functions if f.module_id == module_id]

    def module_by_id(self, module_id: str) -> Optional[ModuleNode]:
        for module in self.modules:
            if module.id == module_id:
                return module
        return None

    def function_by_id(self, function_id: str) -> Optional[FunctionNode]:
        for function in self.functions:
            if function.id == function_id:
                return function
        return None

    def edges_by_kind(self, kind: str) -> List[Edge]:
        return [e for e in self.edges if e.kind == kind]
