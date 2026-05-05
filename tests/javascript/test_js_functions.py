from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


def test_tree_sitter_javascript_extracts_functions_and_methods() -> None:
    code = """
export function run() {}

const helper = () => run();

class Worker {
  start() {
    return helper();
  }
}
"""

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    function_ids = {fn.function_id for fn in parsed.functions}

    assert function_ids == {
        "app.main:run",
        "app.main:helper",
        "app.main:Worker.start",
    }


def test_tree_sitter_javascript_extracts_function_expression() -> None:
    code = """
const fn = function () {};
"""

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    assert {fn.function_id for fn in parsed.functions} == {"app.main:fn"}
