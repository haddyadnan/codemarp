import tempfile
import webbrowser
from pathlib import Path


def _template_path() -> Path:
    return Path(__file__).parent / "templates" / "mermaid.html"


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


#     return f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="utf-8">
#   <meta name="viewport" content="width=device-width, initial-scale=1">
#   <title>{title}</title>
#   <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
#   <style>
#     body {{
#       margin: 0;
#       padding: 16px;
#       font-family: sans-serif;
#       background: #fff;
#     }}
#     .mermaid {{
#       max-width: 100%;
#     }}
#   </style>
# </head>
# <body>
#   <div class="mermaid">
# {mermaid_code}
#   </div>

#   <script>
#     mermaid.initialize({{
#       startOnLoad: true,
#       maxTextSize: 100000
#     }});
#   </script>
# </body>
# </html>
# """


def open_mermaid_view(
    mermaid_code: str,
    title: str = "Codemarp",
    subtitle: str = "",
    mode: str = "",
    language: str = "",
    node_count: int = 0,
    edge_count: int = 0,
) -> Path:
    html = wrap_mermaid_html(
        mermaid_code,
        title=title,
        subtitle=subtitle,
        mode=mode,
        language=language,
        node_count=node_count,
        edge_count=edge_count,
    )

    tmp_dir = Path(tempfile.gettempdir())
    output_path = tmp_dir / "codemarp_view.html"
    output_path.write_text(html, encoding="utf-8")

    webbrowser.open(output_path.as_uri())
    return output_path
