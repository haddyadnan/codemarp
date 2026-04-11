from enum import Enum

from codemarp.graph.models import GraphBundle
from codemarp.views.module_view import module_function_view
from codemarp.views.trace import reverse_trace_function_view, trace_function_view


class ViewType(str, Enum):
    FULL = "full"
    TRACE = "trace"
    MODULE = "module"
    REVERSE = "reverse"
    LOW = "low"


def apply_view(
    bundle: GraphBundle,
    *,
    view: ViewType,
    focus: str | None = None,
    module: str | None = None,
    max_depth: int | None = None,
) -> GraphBundle:
    if view is ViewType.FULL:
        return bundle

    if view is ViewType.TRACE:
        if focus is None:
            raise ValueError("focus is required for trace view")
        return trace_function_view(bundle, focus, max_depth=max_depth)

    if view is ViewType.MODULE:
        if module is None:
            raise ValueError("module is required for module view")
        return module_function_view(bundle, module)

    if focus is None:
        raise ValueError("focus is required for reverse view")

    return reverse_trace_function_view(bundle, focus, max_depth=max_depth)
