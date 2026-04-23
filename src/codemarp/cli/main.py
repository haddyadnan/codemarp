import argparse
from collections import defaultdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from codemarp.analyzers.low_level import build_low_level_mode
from codemarp.errors import codemarpError
from codemarp.pipeline.apply_mode import ModeType, apply_mode
from codemarp.pipeline.build_bundle import build_bundle
from codemarp.pipeline.export_all import export_all, export_low_level
from codemarp.pipeline.render_mode import render_mode_to_mermaid
from codemarp.viewer import open_mermaid_view


def package_version() -> str:
    try:
        return version("codemarp")
    except PackageNotFoundError:
        return "unknown"


def _build_low_mode(
    root: Path,
    *,
    focus: str,
):
    return build_low_level_mode(root, focus)


def _build_graph_mode(
    build_result,
    *,
    mode: ModeType,
    focus: str | None = None,
    module: str | None = None,
    max_depth: int | None = None,
):
    return apply_mode(
        build_result.bundle,
        mode=mode,
        focus=focus,
        module=module,
        max_depth=max_depth,
    )


def analyze_command(
    root: Path,
    out: Path,
    *,
    mode: ModeType,
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

    if mode is ModeType.LOW:
        assert focus is not None
        low_mode = _build_low_mode(root, focus=focus)
        export_low_level(build_result=build_result, low_mode=low_mode, out_dir=out)

        print(f"Parsed {len(build_result.parsed_modules)} modules")
        print(f"Discovered {len(build_result.bundle.functions)} functions")
        print(f"Mode type: {mode.value}")
        print(f"Low-level mode for {focus}")
        print(f"Low-level mode contains {len(low_mode.nodes)} nodes")
        print("Wrote graph.json")
        print("Wrote high_level.mmd")
        print("Wrote low_level.mmd")
        print("Wrote low_level.json")
        return

    graph_mode = _build_graph_mode(
        build_result,
        mode=mode,
        focus=focus,
        module=module,
        max_depth=max_depth,
    )
    export_all(build_result=build_result, mode=graph_mode, out_dir=out)

    print(f"Parsed {len(build_result.parsed_modules)} modules")
    print(f"Discovered {len(build_result.bundle.functions)} functions")
    print(f"mode type: {mode.value}")
    if mode is ModeType.TRACE:
        print(f"Focused trace from {focus}")
        print(f"Trace contains {len(graph_mode.functions)} functions")
    if mode is ModeType.MODULE:
        print(f"Module mode for {module}")
        print(f"Module mode contains {len(graph_mode.functions)} functions")
    if mode is ModeType.REVERSE:
        print(f"Reverse trace from {focus}")
        print(f"Reverse trace contains {len(graph_mode.functions)} functions")
    print("Wrote graph.json")
    print("Wrote high_level.mmd")
    print("Wrote mid_level.mmd")
    print("Wrote mid_level.json")


def view_command(
    root: Path,
    *,
    mode: ModeType,
    focus: str | None = None,
    module: str | None = None,
    max_depth: int | None = None,
    parser_engine: str = "tree-sitter",
) -> None:
    build_result = build_bundle(root, engine=parser_engine)

    graph_mode, low_mode = None, None

    if mode is ModeType.LOW:
        assert focus is not None
        low_mode = _build_low_mode(root, focus=focus)
    else:
        graph_mode = _build_graph_mode(
            build_result,
            mode=mode,
            focus=focus,
            module=module,
            max_depth=max_depth,
        )

    mermaid = render_mode_to_mermaid(
        build_result,
        mode=mode,
        graph_mode=graph_mode,
        low_mode=low_mode,
    )

    output_path = open_mermaid_view(mermaid, title=f"Codemarp - {mode.value}")

    print(f"Parsed {len(build_result.parsed_modules)} modules")
    print(f"Discovered {len(build_result.bundle.functions)} functions")
    print(f"mode type: {mode.value}")
    print(f"Opened viewer: {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codemarp",
        description="CLI for generating multi-level code architecture graphs",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a Python codebase")
    analyze.add_argument("root", help="Path to the repository root")
    analyze.add_argument("--out", default="./codemarp_out", help="Output directory")
    analyze.add_argument(
        "--mode",
        choices=[mode.value for mode in ModeType],
        default=ModeType.FULL.value,
        help="Graph mode to export",
    )
    analyze.add_argument(
        "--focus",
        default=None,
        help="Entrypoint for TRACE/REVERSE mode (function id: module:function)",
    )
    analyze.add_argument(
        "--module",
        default=None,
        help="Module id for MODULE mode",
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

    view = subparsers.add_parser("view", help="Open a graph in the browser")
    view.add_argument("root", help="Path to the repository root")
    view.add_argument(
        "--mode",
        choices=[mode.value for mode in ModeType],
        default=ModeType.FULL.value,
        help="Graph mode to render",
    )
    view.add_argument(
        "--focus",
        default=None,
        help="Entrypoint for TRACE/REVERSE/LOW mode (function id: module:function)",
    )
    view.add_argument(
        "--module",
        default=None,
        help="Module id for MODULE mode",
    )
    view.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum trace depth from the focused function",
    )
    view.add_argument(
        "--parser-engine",
        choices=["ast", "tree-sitter"],
        default="tree-sitter",
        help="Parser backend to use (default: tree-sitter)",
    )

    return parser


def _validate_mode_args(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    mode = ModeType(args.mode)

    if mode is ModeType.FULL:
        if args.focus is not None:
            parser.error("--focus cannot be used with --mode full")
        if args.module is not None:
            parser.error("--module cannot be used with --mode full")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --mode full")

    if mode is ModeType.TRACE:
        if not args.focus:
            parser.error("--focus is required with --mode trace")
        if args.module is not None:
            parser.error("--module cannot be used with --mode trace")

    if mode is ModeType.MODULE:
        if not args.module:
            parser.error("--module is required with --mode module")
        if args.focus is not None:
            parser.error("--focus cannot be used with --mode module")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --mode module")

    if mode is ModeType.REVERSE:
        if not args.focus:
            parser.error("--focus is required with --mode reverse")
        if args.module is not None:
            parser.error("--module cannot be used with --mode reverse")

    if mode is ModeType.LOW:
        if not args.focus:
            parser.error("--focus is required with --mode low")
        if args.module is not None:
            parser.error("--module cannot be used with --mode low")
        if args.max_depth is not None:
            parser.error("--max-depth cannot be used with --mode low")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        _validate_mode_args(args, parser)
        try:
            analyze_command(
                args.root,
                args.out,
                mode=ModeType(args.mode),
                focus=args.focus,
                module=args.module,
                max_depth=args.max_depth,
                debug_resolution=args.debug_resolution,
                parser_engine=args.parser_engine,
            )

        except codemarpError as exc:
            raise SystemExit(str(exc)) from exc

    elif args.command == "view":
        _validate_mode_args(args, parser)
        try:
            view_command(
                args.root,
                mode=ModeType(args.mode),
                focus=args.focus,
                module=args.module,
                max_depth=args.max_depth,
                parser_engine=args.parser_engine,
            )
        except codemarpError as exc:
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
