from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ModuleNode:
    id: str
    path: str
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


@dataclass(slots=True)
class GraphBundle:
    modules: List[ModuleNode] = field(default_factory=list)
    functions: List[FunctionNode] = field(default_factory=list)
    control_flow_nodes: List[ControlFlowNode] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "modules": [asdict(m) for m in self.modules],
            "functions": [asdict(f) for f in self.functions],
            "control_flow_nodes": [asdict(n) for n in self.control_flow_nodes],
            "edges": [asdict(e) for e in self.edges],
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
