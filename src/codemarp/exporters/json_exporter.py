import json
from pathlib import Path

from codemarp.graph.models import GraphBundle


def export_bundle_json(bundle: GraphBundle, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.write_text(json.dumps(bundle.to_dict(), default=str))
