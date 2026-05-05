from codemarp.parser.contracts import ImportFact
from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


def test_tree_sitter_javascript_extracts_esm_named_imports() -> None:
    code = 'import { add, sub as minus } from "./math";\n'

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="./math",
            imported_name="add",
            alias=None,
            is_from_import=True,
            relative_level=0,
            lineno=1,
        ),
        ImportFact(
            raw_module="./math",
            imported_name="sub",
            alias="minus",
            is_from_import=True,
            relative_level=0,
            lineno=1,
        ),
    ]


def test_tree_sitter_javascript_extracts_require_import_with_alias() -> None:
    code = 'const legacy = require("./legacy");\n'

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    assert parsed.imports == [
        ImportFact(
            raw_module="./legacy",
            imported_name=None,
            alias="legacy",
            is_from_import=False,
            relative_level=0,
            lineno=1,
        )
    ]


def test_tree_sitter_javascript_ignores_dynamic_require_import() -> None:
    code = "const x = require(someVar);\n"

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    assert parsed.imports == []
