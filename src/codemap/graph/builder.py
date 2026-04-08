from codemap.graph.models import (
    ControlFlowNode,
    Edge,
    FunctionNode,
    GraphBundle,
    ModuleNode,
)


class GraphBuilder:
    def __init__(self) -> None:
        self.bundle = GraphBundle()

    def add_module(self, module: ModuleNode) -> None:
        self.bundle.modules.append(module)

    def add_modules(self, modules: list[ModuleNode]) -> None:
        self.bundle.modules.extend(modules)

    def add_function(self, function: FunctionNode) -> None:
        self.bundle.functions.append(function)

    def add_functions(self, functions: list[FunctionNode]) -> None:
        self.bundle.functions.extend(functions)

    def add_control_flow_node(self, node: ControlFlowNode) -> None:
        self.bundle.control_flow_nodes.append(node)

    def add_control_flow_nodes(self, nodes: list[ControlFlowNode]) -> None:
        self.bundle.control_flow_nodes.extend(nodes)

    def add_edge(self, edge: Edge) -> None:
        self.bundle.edges.append(edge)

    def add_edges(self, edges: list[Edge]) -> None:
        self.bundle.edges.extend(edges)

    def build(self) -> GraphBundle:
        return self.bundle
