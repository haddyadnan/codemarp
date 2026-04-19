from pathlib import Path

from codemarp.analyzers.high_level import ModuleNode, build_high_level_edges
from codemarp.parser.contracts import CallFact, ImportFact, ParsedModule
from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


def test_tree_sitter_typescript_extracts_top_level_function_and_method() -> None:
    code = (
        "function run() {\n"
        "  return 1;\n"
        "}\n"
        "\n"
        "class Service {\n"
        "  save() {\n"
        "    return 2;\n"
        "  }\n"
        "}\n"
    )

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.language == "typescript"
    assert [fn.function_id for fn in parsed.functions] == [
        "app.main:run",
        "app.main:Service.save",
    ]
    assert [fn.is_method for fn in parsed.functions] == [False, True]


def test_tree_sitter_typescript_extracts_exported_function_and_class_method() -> None:
    code = (
        "export function run() {\n"
        "  return 1;\n"
        "}\n"
        "\n"
        "export class Service {\n"
        "  save() {\n"
        "    return 2;\n"
        "  }\n"
        "}\n"
    )

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == [
        "app.main:run",
        "app.main:Service.save",
    ]


def test_tree_sitter_typescript_extracts_async_function() -> None:
    code = "export async function run() {\n  return 1;\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:run"]
    assert [fn.is_async for fn in parsed.functions] == [True]


def test_tree_sitter_typescript_extracts_async_method() -> None:
    code = "class Service {\n  async save() {\n    return 2;\n  }\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:Service.save"]
    assert [fn.is_async for fn in parsed.functions] == [True]


def test_tree_sitter_typescript_extracts_default_and_named_imports() -> None:
    code = 'import foo from "mod"\nimport { run, save as persist } from "app/service"\n'

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="mod",
            imported_name=None,
            alias="foo",
            is_from_import=False,
            relative_level=0,
            lineno=1,
        ),
        ImportFact(
            raw_module="app/service",
            imported_name="run",
            alias=None,
            is_from_import=True,
            relative_level=0,
            lineno=2,
        ),
        ImportFact(
            raw_module="app/service",
            imported_name="save",
            alias="persist",
            is_from_import=True,
            relative_level=0,
            lineno=2,
        ),
    ]


def test_tree_sitter_typescript_extracts_namespace_import() -> None:
    code = 'import * as utils from "app/utils"\n'

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="app/utils",
            imported_name=None,
            alias="utils",
            is_from_import=False,
            relative_level=0,
            lineno=1,
        )
    ]


def test_tree_sitter_typescript_extracts_bare_call() -> None:
    code = "function run() {\n  work();\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:run",
            raw="work",
            leaf_name="work",
            receiver=None,
            kind="bare",
            lineno=2,
        )
    ]


def test_tree_sitter_typescript_extracts_attribute_and_chained_calls() -> None:
    code = "function run() {\n  worker.process();\n  app.worker.save();\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:run",
            raw="worker.process",
            leaf_name="process",
            receiver="worker",
            kind="attribute",
            lineno=2,
        ),
        CallFact(
            caller_id="app.main:run",
            raw="app.worker.save",
            leaf_name="save",
            receiver="app.worker",
            kind="attribute",
            lineno=3,
        ),
    ]


def test_tree_sitter_typescript_extracts_super_call() -> None:
    code = "class Service extends Base {\n  save() {\n    super.save();\n  }\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:Service.save",
            raw="super.save",
            leaf_name="save",
            receiver="super",
            kind="super",
            lineno=3,
        )
    ]


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


def test_high_level_resolves_typescript_relative_js_specifier() -> None:
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
                    alias="z",
                    is_from_import=False,
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

    group_ids, edges = build_high_level_edges(parsed_modules, modules)

    assert "index" in group_ids
    assert "v4.classic" in group_ids
    assert {(edge.source, edge.target) for edge in edges} == {("index", "v4.classic")}


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
