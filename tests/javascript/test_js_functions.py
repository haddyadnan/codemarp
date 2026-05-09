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


def test_tree_sitter_javascript_extracts_property_assigned_function() -> None:
    code = """
exports.createApplication = function () {
  init();
};

Router.prototype.handle = function () {
  dispatch();
};

app.use = () => {
  mount();
};
"""

    parsed = TreeSitterTypeScriptParser(
        "express",
        language="javascript",
    ).parse_code_to_facts(code)

    assert {fn.function_id for fn in parsed.functions} == {
        "express:exports.createApplication",
        "express:Router.prototype.handle",
        "express:app.use",
    }

    calls = {(c.caller_id, c.raw) for c in parsed.calls}

    assert ("express:exports.createApplication", "init") in calls
    assert ("express:Router.prototype.handle", "dispatch") in calls
    assert ("express:app.use", "mount") in calls


def test_tree_sitter_javascript_ignores_dynamic_property_assignment() -> None:
    code = """
obj[name] = function () {};
obj[prefix + key] = () => {};
factory().method = function () {};
"""

    parsed = TreeSitterTypeScriptParser(
        "app",
        language="javascript",
    ).parse_code_to_facts(code)

    assert parsed.functions == []


def test_tree_sitter_javascript_normalizes_module_exports_property_assignment() -> None:
    code = """
module.exports.createApplication = function () {};
"""

    parsed = TreeSitterTypeScriptParser(
        "app",
        language="javascript",
    ).parse_code_to_facts(code)

    assert {fn.function_id for fn in parsed.functions} == {
        "app:exports.createApplication",
    }


def test_tree_sitter_javascript_keeps_regular_and_property_functions_distinct() -> None:
    code = """
function run() {}

exports.run = function () {};
"""

    parsed = TreeSitterTypeScriptParser(
        "app",
        language="javascript",
    ).parse_code_to_facts(code)

    assert {fn.function_id for fn in parsed.functions} == {
        "app:run",
        "app:exports.run",
    }
