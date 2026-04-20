from enum import Enum

from codemarp.graph.models import GraphBundle
from codemarp.views.module_view import module_function_view
from codemarp.views.trace import reverse_trace_function_view, trace_function_view


class ModeType(str, Enum):
    FULL = "full"
    TRACE = "trace"
    MODULE = "module"
    REVERSE = "reverse"
    LOW = "low"


def apply_mode(
    bundle: GraphBundle,
    *,
    mode: ModeType,
    focus: str | None = None,
    module: str | None = None,
    max_depth: int | None = None,
) -> GraphBundle:
    if mode is ModeType.FULL:
        return bundle

    if mode is ModeType.TRACE:
        if focus is None:
            raise ValueError("focus is required for trace mode")
        return trace_function_view(bundle, focus, max_depth=max_depth)

    if mode is ModeType.MODULE:
        if module is None:
            raise ValueError("module is required for module mode")
        return module_function_view(bundle, module)

    if focus is None:
        raise ValueError("focus is required for reverse mode")

    return reverse_trace_function_view(bundle, focus, max_depth=max_depth)
