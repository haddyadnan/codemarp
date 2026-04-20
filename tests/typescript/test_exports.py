from pathlib import Path

from codemarp.analyzers.high_level import ModuleNode, build_high_level_edges
from codemarp.parser.contracts import ImportFact, ParsedModule
from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


def test_tree_sitter_typescript_extracts_named_re_export() -> None:
    code = 'export { run, save as persist } from "app/service"\n'

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="app/service",
            imported_name="run",
            alias=None,
            is_from_import=True,
            relative_level=0,
            lineno=1,
        ),
        ImportFact(
            raw_module="app/service",
            imported_name="save",
            alias="persist",
            is_from_import=True,
            relative_level=0,
            lineno=1,
        ),
    ]


def test_tree_sitter_typescript_extracts_star_re_export() -> None:
    code = 'export * from "app/service"\n'

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="app/service",
            imported_name=None,
            alias=None,
            is_from_import=True,
            relative_level=0,
            lineno=1,
        )
    ]


def test_high_level_resolves_typescript_relative_re_export_specifier() -> None:
    modules = [
        ModuleNode(id="index", path=Path("index.ts"), package=""),
        ModuleNode(
            id="v4.classic.external",
            path=Path("v4/classic/external.ts"),
            package="v4.classic",
        ),
    ]

    parsed_modules = [
        ParsedModule(
            module_id="index",
            file_path=Path("index.ts"),
            language="typescript",
            imports=[
                ImportFact(
                    raw_module="./v4/classic/external.js",
                    imported_name=None,
                    alias=None,
                    is_from_import=True,
                    relative_level=0,
                    lineno=1,
                )
            ],
            functions=[],
            calls=[],
            control_flow_roots=[],
        ),
        ParsedModule(
            module_id="v4.classic.external",
            file_path=Path("v4/classic/external.ts"),
            language="typescript",
            imports=[],
            functions=[],
            calls=[],
            control_flow_roots=[],
        ),
    ]

    _, edges = build_high_level_edges(parsed_modules, modules)

    assert {(edge.source, edge.target) for edge in edges} == {("index", "v4.classic")}
