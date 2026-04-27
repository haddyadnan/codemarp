import json
from pathlib import Path

from codemarp.graph.models import GraphBundle
from codemarp.pipeline.build_bundle import BuildResult


def bundle_to_json_dict(bundle: GraphBundle) -> dict:
    nodes = []
    edges = []

    module_path_map = {module.id: module.path for module in bundle.modules}
    module_language_map = {module.id: module.language for module in bundle.modules}

    for module in bundle.modules:
        nodes.append(
            {
                "id": module.id,
                "label": module.id,
                "kind": "module",
                "file_path": str(module.path) if module.path else None,
                "language": module.language,
            }
        )

    for fn in bundle.functions:
        module_path = module_path_map.get(fn.module_id)
        module_language = module_language_map.get(fn.module_id)

        nodes.append(
            {
                "id": fn.id,
                "label": fn.name,
                "kind": "function",
                "module_id": fn.module_id,
                "file_path": str(module_path) if module_path else None,
                "language": module_language,
            }
        )

    for edge in bundle.edges:
        reason = getattr(edge, "reason", None)

        edges.append(
            {
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
                "label": edge.label,
                "resolution_kind": reason.value if reason is not None else None,
            }
        )

    return {"nodes": nodes, "edges": edges}


def full_mode_to_json_dict(build_result: BuildResult) -> dict:
    nodes = [
        {
            "id": group_id,
            "label": group_id,
            "kind": "module",
            "file_path": None,
            "language": None,
        }
        for group_id in build_result.high_level_package_ids
    ]

    edges = []
    for edge in build_result.high_level_edges:
        reason = getattr(edge, "reason", None)
        edges.append(
            {
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
                "label": edge.label,
                "resolution_kind": reason.value if reason is not None else None,
            }
        )

    return {"nodes": nodes, "edges": edges}


def export_bundle_json(bundle: GraphBundle, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.write_text(
        json.dumps(bundle_to_json_dict(bundle), indent=2),
        encoding="utf-8",
    )
