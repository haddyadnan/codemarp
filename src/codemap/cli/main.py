import argparse
from pathlib import Path

from codemap.analyzers.high_level import build_high_level_edges
from codemap.analyzers.mid_level import build_mid_level_edges
from codemap.exporters.json_exporter import export_bundle_json
from codemap.exporters.mermaid import export_function_graph, export_module_graph
from codemap.graph.builder import GraphBuilder
from codemap.graph.models import ModuleNode
from codemap.parser.python_parser import (
    discover_python_files,
    package_from_module_id,
    parse_python_file,
)


def analyze_command(root: str, out: str) -> None:
    root_path = Path(root).resolve()
    out_path = Path(out).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    parsed_modules = []
    builder = GraphBuilder()

    for file_path in discover_python_files(root_path):
        parsed = parse_python_file(root_path, file_path)
        parsed_modules.append(parsed)
        builder.add_module(
            ModuleNode(
                id=parsed.module_id,
                path=parsed.path,
                package=package_from_module_id(parsed.module_id),
            )
        )
        builder.add_functions(parsed.functions)

    known_module_ids = {module.module_id for module in parsed_modules}
    high_edges = build_high_level_edges(parsed_modules, known_module_ids)
    mid_edges = build_mid_level_edges(parsed_modules, builder.bundle.functions)
    builder.add_edges(high_edges)
    builder.add_edges(mid_edges)

    bundle = builder.build()

    export_bundle_json(bundle, out_path / "graph.json")
    (out_path / "high_level.mmd").write_text(
        export_module_graph(bundle.modules, bundle.edges), encoding="utf-8"
    )
    (out_path / "mid_level.mmd").write_text(
        export_function_graph(bundle.functions, bundle.edges), encoding="utf-8"
    )

    print(f"Parsed {len(parsed_modules)} modules")
    print(f"Discovered {len(bundle.functions)} functions")
    print(f"Wrote {out_path / 'graph.json'}")
    print(f"Wrote {out_path / 'high_level.mmd'}")
    print(f"Wrote {out_path / 'mid_level.mmd'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codemap", description="3-level code mapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a Python codebase")
    analyze.add_argument("root", help="Path to the repository root")
    analyze.add_argument("--out", default="./codemap_out", help="Output directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        analyze_command(args.root, args.out)


if __name__ == "__main__":
    main()
