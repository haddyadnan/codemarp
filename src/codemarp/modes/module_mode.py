from codemarp.errors import ModuleModeError
from codemarp.graph.models import GraphBundle
from codemarp.modes.subgraph import build_function_subgraph


def module_function_mode(bundle: GraphBundle, module_id: str) -> GraphBundle:
    _validate_module(bundle, module_id)
    function_ids = {
        function.id for function in bundle.functions if function.module_id == module_id
    }
    return build_function_subgraph(bundle, function_ids)


def _validate_module(bundle: GraphBundle, module_id: str) -> None:
    if bundle.module_by_id(module_id) is None:
        raise ModuleModeError(f"Module not found: {module_id}")
