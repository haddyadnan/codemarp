from dataclasses import dataclass
from pathlib import Path

from codemarp.analyzers.high_level import build_high_level_edges
from codemarp.analyzers.mid_level import build_mid_level_edges
from codemarp.graph.builder import GraphBuilder
from codemarp.graph.models import Edge, GraphBundle, ModuleNode
from codemarp.parser.python_parser import (
    ParsedPythonModule,
    discover_python_files,
    package_from_module_id,
    parse_python_file,
)


@dataclass(slots=True)
class BuildResult:
    bundle: GraphBundle
    parsed_modules: list[ParsedPythonModule]
    high_level_package_ids: list[str]
    high_level_edges: list[Edge]


def build_bundle(repo_path: str | Path) -> BuildResult:
    root_path = Path(repo_path).resolve()

    parsed_modules: list[ParsedPythonModule] = []
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

    package_ids, high_level_edges = build_high_level_edges(
        parsed_modules, builder.bundle.modules
    )
    mid_level_edges = build_mid_level_edges(parsed_modules, builder.bundle.functions)
    builder.add_edges(high_level_edges)
    builder.add_edges(mid_level_edges)

    return BuildResult(
        bundle=builder.build(),
        parsed_modules=parsed_modules,
        high_level_package_ids=package_ids,
        high_level_edges=high_level_edges,
    )
