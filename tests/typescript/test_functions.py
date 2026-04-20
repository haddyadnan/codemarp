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


def test_tree_sitter_typescript_extracts_arrow_function_assigned_to_variable() -> None:
    code = "const run = () => {\n  return 1;\n};\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:run"]


def test_tree_sitter_typescript_extracts_function_expression_assigned_to_variable() -> (
    None
):
    code = "const run = function () {\n  return 1;\n};\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:run"]


def test_tree_sitter_typescript_extracts_arrow_function_class_field() -> None:
    code = "class Service {\n  save = () => {\n    work();\n  };\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:Service.save"]


def test_tree_sitter_typescript_extracts_function_expression_class_field() -> None:
    code = "class Service {\n  save = function() {\n    work();\n  };\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:Service.save"]


def test_tree_sitter_typescript_ignores_non_function_variable_declarations() -> None:
    code = "const x = 42;\nconst y = 'hello';\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.functions == []
    assert parsed.calls == []


def test_tree_sitter_typescript_extracts_async_arrow_function() -> None:
    code = "const run = async () => {\n  return 1;\n};\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:run"]
    assert parsed.functions[0].is_async is True


def test_tree_sitter_typescript_extracts_multiple_arrow_functions_in_one_declaration() -> (
    None
):
    code = "const run = () => {}, save = () => {};\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == [
        "app.main:run",
        "app.main:save",
    ]
