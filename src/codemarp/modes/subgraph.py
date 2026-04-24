from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode


def build_function_subgraph(bundle: GraphBundle, function_ids: set[str]) -> GraphBundle:
    functions = [fn for fn in bundle.functions if fn.id in function_ids]
    modules = _modules_for_functions(functions, bundle.modules)
    edges = _filter_edges_for_nodes(bundle.edges, function_ids, kind="calls")
    return GraphBundle(modules=modules, functions=functions, edges=edges)


def _filter_edges_for_nodes(
    edges: list[Edge], allowed_node_ids: set[str], *, kind: str
) -> list[Edge]:
    return [
        edge
        for edge in edges
        if edge.kind == kind
        and edge.source in allowed_node_ids
        and edge.target in allowed_node_ids
    ]


def _modules_for_functions(
    functions: list[FunctionNode], all_modules: list[ModuleNode]
) -> list[ModuleNode]:
    module_ids = {fn.module_id for fn in functions}
    return [module for module in all_modules if module.id in module_ids]
