import argparse
from collections import defaultdict
from pathlib import Path

from codemarp.analyzers.low_level import build_low_level_view
from codemarp.errors import codemarpError
from codemarp.pipeline.apply_view import ViewType, apply_view
from codemarp.pipeline.build_bundle import build_bundle
from codemarp.pipeline.export_all import export_all, export_low_level


def analyze_command(
    root: Path,
    out: Path,
    *,
    view: ViewType,
    focus: str | None = None,
    module: str | None = None,
    max_depth: int | None = None,
    debug_resolution: bool = False,
    parser_engine: str = "tree-sitter",
) -> None:
    build_result = build_bundle(root, engine=parser_engine)

    if debug_resolution:
        grouped = defaultdict(list)
        for edge in build_result.bundle.edges:
            if edge.kind != "calls" or edge.reason is None:
                continue
            print(f"{edge.source} -> {edge.target}  [{edge.reason.value}]")

            print("\n=== Resolution Debug ===\n")

            for module, edges in sorted(grouped.items()):
                print(f"{module}:")
                for edge in edges:
                    src_fn = edge.source.split(":")[1]
                    print(f"  {src_fn} -> {edge.target}  [{edge.reason.value}]")
                print()

    if view is ViewType.LOW:
        assert focus is not None
        low_view = build_low_level_view(root, focus)
        export_low_level(build_result=build_result, low_view=low_view, out_dir=out)

        print(f"Parsed {len(build_result.parsed_modules)} modules")
        print(f"Discovered {len(build_result.bundle.functions)} functions")
        print(f"View type: {view.value}")
        print(f"Low-level view for {focus}")
        print(f"Low-level view contains {len(low_view.nodes)} nodes")
        print("Wrote graph.json")
        print("Wrote high_level.mmd")
        print("Wrote low_level.mmd")
        print("Wrote low_level.json")
        return

    graph_view = apply_view(
        build_result.bundle,
        view=view,
        focus=focus,
        module=module,
        max_depth=max_depth,
    )
    export_all(build_result=build_result, view=graph_view, out_dir=out)

    print(f"Parsed {len(build_result.parsed_modules)} modules")
    print(f"Discovered {len(build_result.bundle.functions)} functions")
    print(f"View type: {view.value}")
    if view is ViewType.TRACE:
        print(f"Focused trace from {focus}")
        print(f"Trace contains {len(graph_view.functions)} functions")
    if view is ViewType.MODULE:
        print(f"Module view for {module}")
        print(f"Module view contains {len(graph_view.functions)} functions")
    if view is ViewType.REVERSE:
        print(f"Reverse trace from {focus}")
        print(f"Reverse trace contains {len(graph_view.functions)} functions")
    print("Wrote graph.json")
    print("Wrote high_level.mmd")
    print("Wrote mid_level.mmd")
    print("Wrote mid_level.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codemarp", description="3-level code mapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a Python codebase")
    analyze.add_argument("root", help="Path to the repository root")
    analyze.add_argument("--out", default="./codemarp_out", help="Output directory")
    analyze.add_argument(
        "--view",
        choices=[view.value for view in ViewType],
        default=ViewType.FULL.value,
        help="Graph view to export",
    )
    analyze.add_argument(
        "--focus",
        default=None,
        help="Entrypoint for TRACE/REVERSE view (function id: module:function)",
    )
    analyze.add_argument(
        "--module",
        default=None,
        help="Module id for MODULE view",
    )
    analyze.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum trace depth from the focused function",
    )

    analyze.add_argument(
        "--debug-resolution",
        action="store_true",
        help="Print why each mid-level call edge was resolved.",
    )

    analyze.add_argument(
        "--parser-engine",
        choices=["ast", "tree-sitter"],
        default="tree-sitter",
        help="Parser backend to use (default: tree-sitter)",
    )

    return parser


def _validate_analyze_args(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    view = ViewType(args.view)

    if view is ViewType.FULL:
        if args.focus is not None:
            parser.error("--focus cannot be used with --view full")
        if args.module is not None:
            parser.error("--module cannot be used with --view full")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --view full")

    if view is ViewType.TRACE:
        if not args.focus:
            parser.error("--focus is required with --view trace")
        if args.module is not None:
            parser.error("--module cannot be used with --view trace")

    if view is ViewType.MODULE:
        if not args.module:
            parser.error("--module is required with --view module")
        if args.focus is not None:
            parser.error("--focus cannot be used with --view module")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --view module")

    if view is ViewType.REVERSE:
        if not args.focus:
            parser.error("--focus is required with --view reverse")
        if args.module is not None:
            parser.error("--module cannot be used with --view reverse")

    if view is ViewType.LOW:
        if not args.focus:
            parser.error("--focus is required with --view low")
        if args.module is not None:
            parser.error("--module cannot be used with --view low")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --view low")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        _validate_analyze_args(args, parser)
        try:
            analyze_command(
                args.root,
                args.out,
                view=ViewType(args.view),
                focus=args.focus,
                module=args.module,
                max_depth=args.max_depth,
                debug_resolution=args.debug_resolution,
                parser_engine=args.parser_engine,
            )
        except codemarpError as exc:
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
