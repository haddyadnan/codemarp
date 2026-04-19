from codemarp.parser.contracts import ImportFact
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
