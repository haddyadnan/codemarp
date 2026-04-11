import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from codemap.exporters.json_exporter import export_bundle_json
from codemap.exporters.mermaid import (
    export_function_graph,
    export_low_level_graph,
    export_module_graph,
)
from codemap.graph.models import GraphBundle
from codemap.pipeline.build_bundle import BuildResult

if TYPE_CHECKING:
    from codemap.analyzers.low_level import LowLevelResult


def export_all(
    *,
    build_result: BuildResult,
    view: GraphBundle,
    out_dir: str | Path,
) -> None:
    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    # Full-analysis outputs
    export_bundle_json(build_result.bundle, out_path / "graph.json")
    (out_path / "high_level.mmd").write_text(
        export_module_graph(
            build_result.high_level_package_ids,
            build_result.high_level_edges,
            build_result.bundle.modules,
        ),
        encoding="utf-8",
    )

    # View-specific outputs
    (out_path / "mid_level.mmd").write_text(
        export_function_graph(view.functions, view.edges),
        encoding="utf-8",
    )
    export_bundle_json(view, out_path / "mid_level.json")


def export_low_level(
    *,
    build_result: BuildResult,
    low_view: "LowLevelResult",
    out_dir: str | Path,
) -> None:
    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    export_bundle_json(build_result.bundle, out_path / "graph.json")
    (out_path / "high_level.mmd").write_text(
        export_module_graph(
            build_result.high_level_package_ids,
            build_result.high_level_edges,
            build_result.bundle.modules,
        ),
        encoding="utf-8",
    )

    (out_path / "low_level.mmd").write_text(
        export_low_level_graph(low_view.nodes, low_view.edges),
        encoding="utf-8",
    )
    (out_path / "low_level.json").write_text(
        json.dumps(
            {
                "function_id": low_view.function_id,
                "nodes": [asdict(node) for node in low_view.nodes],
                "edges": [asdict(edge) for edge in low_view.edges],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
