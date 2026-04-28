import json
import tempfile
import webbrowser
from pathlib import Path


def _template_path() -> Path:
    return Path(__file__).parent / "templates" / "mermaid.html"


def _cytoscape_template_path() -> Path:
    return Path(__file__).parent / "templates" / "cytoscape.html"


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

    return (
        template.replace("{{title}}", title)
        .replace("{{subtitle}}", subtitle)
        .replace("{{graph_json}}", json.dumps(graph_json))
        .replace("{{mode}}", mode)
        .replace("{{language}}", language)
        .replace("{{node_count}}", str(node_count))
        .replace("{{edge_count}}", str(edge_count))
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
