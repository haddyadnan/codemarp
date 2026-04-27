import json
from pathlib import Path

from codemarp.graph.models import GraphBundle


def export_bundle_json(bundle: GraphBundle, out_path: str | Path) -> None:
    out_path = Path(out_path)

    nodes = []
    edges = []

    for module in bundle.modules:
        nodes.append(
            {
                "id": module.id,
                "label": module.id,
                "kind": "module",
                "file_path": str(module.path),
                "language": module.language,
            }
        )

    for fn in getattr(bundle, "functions", []):
        nodes.append(
            {
                "id": fn.id,
                "label": fn.name,
                "kind": "function",
                "module_id": fn.module_id,
                "file_path": str(getattr(fn, "path", "")),
                "language": getattr(fn, "language", None),
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

    data = {
        "nodes": nodes,
        "edges": edges,
    }

    out_path.write_text(json.dumps(data, indent=2))
