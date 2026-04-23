from codemarp.analyzers.low_level import LowLevelResult
from codemarp.exporters.mermaid import (
    export_function_graph,
    export_low_level_graph,
    export_module_graph,
)
from codemarp.graph.models import GraphBundle
from codemarp.pipeline.apply_mode import ModeType
from codemarp.pipeline.build_bundle import BuildResult


def render_mode_to_mermaid(
    build_result: BuildResult,
    *,
    mode: ModeType,
    graph_mode: GraphBundle | None = None,
    low_mode: LowLevelResult | None = None,
) -> str:
    if mode is ModeType.LOW:
        if low_mode is None:
            raise ValueError("low_mode is required for low mode")
        return export_low_level_graph(low_mode.nodes, low_mode.edges)

    if mode is ModeType.FULL:
        return export_module_graph(
            build_result.high_level_package_ids,
            build_result.high_level_edges,
            build_result.bundle.modules,
        )

    if graph_mode is None:
        raise ValueError("graph_mode is required for non-full graph modes")

    return export_function_graph(graph_mode.functions, graph_mode.edges)
