import json
import tempfile
import webbrowser
from pathlib import Path


def _template_path() -> Path:
    return Path(__file__).parent / "templates" / "mermaid.html"


def _cytoscape_template_path() -> Path:
    return Path(__file__).parent / "templates" / "cytoscape.html"


def compute_cytoscape_layout_params(node_count: int, edge_count: int) -> dict:

    density = edge_count / max(node_count, 1)

    # node repulsion -scale mostly with nodes, slightly with density
    node_repulsion = max(4000, min(20000, node_count * 120 + density * 2000))

    # edge length -density matters more here
    ideal_edge_length = max(60, min(180, 50 + node_count * 0.8 + density * 15))

    # iterations -mostly node count
    num_iter = max(1000, min(5000, node_count * 30))

    return {
        "node_repulsion": int(node_repulsion),
        "ideal_edge_length": int(ideal_edge_length),
        "num_iter": int(num_iter),
    }


def wrap_mermaid_html(
    mermaid_code: str,
    *,
    title: str = "Codemarp,",
    subtitle: str = "",
    mode: str = "",
    language: str = "",
    node_count: int = 0,
    edge_count: int = 0,
) -> str:

    template = _template_path().read_text(encoding="utf-8")

    return (
        template.replace("{{title}}", title)
        .replace("{{mermaid}}", mermaid_code)
        .replace("{{subtitle}}", subtitle)
        .replace("{{mode}}", mode)
        .replace("{{language}}", language)
        .replace("{{node_count}}", str(node_count))
        .replace("{{edge_count}}", str(edge_count))
    )


def wrap_cytoscape_html(
    graph_json: dict,
    *,
    title: str,
    subtitle: str = "",
    mode: str = "",
    language: str = "",
    node_count: int = 0,
    edge_count: int = 0,
) -> str:
    template = _cytoscape_template_path().read_text(encoding="utf-8")
    layout = compute_cytoscape_layout_params(node_count, edge_count)

    return (
        template.replace("{{title}}", title)
        .replace("{{subtitle}}", subtitle)
        .replace("{{graph_json}}", json.dumps(graph_json))
        .replace("{{mode}}", mode)
        .replace("{{language}}", language)
        .replace("{{node_count}}", str(node_count))
        .replace("{{edge_count}}", str(edge_count))
        .replace("{{node_repulsion}}", str(layout["node_repulsion"]))
        .replace("{{ideal_edge_length}}", str(layout["ideal_edge_length"]))
        .replace("{{num_iter}}", str(layout["num_iter"]))
    )


def open_mermaid_view(html: str, output_path: Path | None = None) -> Path:
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        path = Path(tmp.name)
        path.write_text(html, encoding="utf-8")
    else:
        path = output_path

    webbrowser.open(f"file://{path}")
    return path
