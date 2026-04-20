from codemarp.parser.contracts import CallFact
from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


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


def test_tree_sitter_typescript_attributes_calls_inside_arrow_function() -> None:
    code = "const run = () => {\n  work();\n};\n"

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


def test_tree_sitter_typescript_attributes_calls_inside_arrow_expression_body() -> None:
    code = "const run = () => work();\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert [fn.function_id for fn in parsed.functions] == ["app.main:run"]
    assert parsed.calls == [
        CallFact(
            caller_id="app.main:run",
            raw="work",
            leaf_name="work",
            receiver=None,
            kind="bare",
            lineno=1,
        )
    ]


def test_tree_sitter_typescript_attributes_calls_inside_class_field_arrow() -> None:
    code = "class Service {\n  save = () => {\n    work();\n  };\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:Service.save",
            raw="work",
            leaf_name="work",
            receiver=None,
            kind="bare",
            lineno=3,
        )
    ]


def test_tree_sitter_typescript_attributes_calls_inside_class_field_function() -> None:
    code = "class Service {\n  save = function() {\n    work();\n  };\n}\n"

    parsed = TreeSitterTypeScriptParser("app.main").parse_code_to_facts(code)

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:Service.save",
            raw="work",
            leaf_name="work",
            receiver=None,
            kind="bare",
            lineno=3,
        )
    ]


def test_tree_sitter_typescript_attributes_calls_inside_function_expression() -> None:
    code = "const run = function() {\n  work();\n};\n"

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
