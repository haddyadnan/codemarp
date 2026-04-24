from dataclasses import dataclass

from codemarp.analyzers.low_level import LowLevelResult
from codemarp.exporters.mermaid import (
    export_function_graph,
    export_low_level_graph,
    export_module_graph,
)
from codemarp.graph.models import GraphBundle
from codemarp.pipeline.apply_mode import ModeType
from codemarp.pipeline.build_bundle import BuildResult


@dataclass(frozen=True)
class ModeStats:
    node_count: int
    edge_count: int


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


def language_summary(parsed_modules) -> str:
    languages = sorted({module.language for module in parsed_modules})

    if not languages:
        return "unknown"

    if len(languages) == 1:
        return languages[0]

    return "mixed"


def stats_for_mode(
    build_result: BuildResult,
    *,
    mode: ModeType,
    graph_mode: GraphBundle | None = None,
    low_mode: LowLevelResult | None = None,
) -> ModeStats:
    if mode is ModeType.LOW:
        if low_mode is None:
            raise ValueError("low_mode is required for low mode")
        return ModeStats(
            node_count=len(low_mode.nodes),
            edge_count=len(low_mode.edges),
        )

    if mode is ModeType.FULL:
        return ModeStats(
            node_count=len(build_result.bundle.modules),
            edge_count=len(build_result.high_level_edges),
        )

    if graph_mode is None:
        raise ValueError("graph_mode is required for non-full graph modes")

    return ModeStats(
        node_count=len(graph_mode.functions),
        edge_count=len(graph_mode.edges),
    )
