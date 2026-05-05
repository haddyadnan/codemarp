from codemarp.parser.typescript.tree_sitter_parser import TreeSitterTypeScriptParser


def test_tree_sitter_javascript_extracts_call_edges() -> None:
    code = """
function run() {
  add(1, 2);
}
"""

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    calls = {(c.caller_id, c.raw, c.kind) for c in parsed.calls}

    assert ("app.main:run", "add", "bare") in calls


def test_tree_sitter_javascript_extracts_member_calls() -> None:
    code = """
function run() {
  legacy.double(2);
}
"""

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    calls = {(c.caller_id, c.raw, c.receiver, c.kind) for c in parsed.calls}

    assert ("app.main:run", "legacy.double", "legacy", "attribute") in calls


def test_tree_sitter_javascript_extracts_nested_calls() -> None:
    code = """
const helper = () => run();

function run() {
  helper();
}
"""

    parsed = TreeSitterTypeScriptParser(
        "app.main",
        language="javascript",
    ).parse_code_to_facts(code)

    calls = {(c.caller_id, c.raw) for c in parsed.calls}

    assert ("app.main:helper", "run") in calls
    assert ("app.main:run", "helper") in calls
