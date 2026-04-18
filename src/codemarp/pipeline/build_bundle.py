from dataclasses import dataclass
from pathlib import Path

from codemarp.analyzers.high_level import build_high_level_edges
from codemarp.analyzers.mid_level import build_mid_level_edges
from codemarp.graph.builder import GraphBuilder
from codemarp.graph.models import Edge, FunctionNode, GraphBundle, ModuleNode
from codemarp.parser.contracts import ParsedModule
from codemarp.parser.python_parser import (
    package_from_module_id,
)
from codemarp.pipeline.parse_repo import parse_repo_files


@dataclass(slots=True)
class BuildResult:
    bundle: GraphBundle
    parsed_modules: list[ParsedModule]
    high_level_package_ids: list[str]
    high_level_edges: list[Edge]


def build_bundle(repo_path: str | Path) -> BuildResult:
    root_path = Path(repo_path).resolve()

    parsed_modules = parse_repo_files(root_path)
    builder = GraphBuilder()

    for parsed in parsed_modules:
        # parsed_modules = parse_repo_files(root_path)
        # parsed_modules.append(parsed)
        builder.add_module(
            ModuleNode(
                id=parsed.module_id,
                path=parsed.file_path,
                package=package_from_module_id(parsed.module_id),
            )
        )
        builder.add_functions(
            [
                FunctionNode(
                    id=fn.function_id,
                    name=fn.qualname,
                    module_id=fn.module_id,
                    lineno=fn.lineno,
                    end_lineno=fn.end_lineno or fn.lineno,
                    class_name=fn.class_name,
                )
                for fn in parsed.functions
            ]
        )

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
