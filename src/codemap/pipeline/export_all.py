from pathlib import Path

from codemap.exporters.json_exporter import export_bundle_json
from codemap.exporters.mermaid import export_function_graph, export_module_graph
from codemap.graph.models import GraphBundle
from codemap.pipeline.build_bundle import BuildResult


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
        ),
        encoding="utf-8",
    )

    # View-specific outputs
    (out_path / "mid_level.mmd").write_text(
        export_function_graph(view.functions, view.edges),
        encoding="utf-8",
    )
    export_bundle_json(view, out_path / "mid_level.json")
