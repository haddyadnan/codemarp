from codemarp.parser.python.ast_parser import PythonParser
from codemarp.parser.python.tree_sitter_parser import TreeSitterPythonParser


def test_tree_sitter_parser_matches_ast_for_top_level_function() -> None:
    code = "def run():\n    return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.module_id == ast_parsed.module_id
    assert ts_parsed.language == ast_parsed.language
    assert ts_parsed.functions == ast_parsed.functions


def test_tree_sitter_parser_matches_ast_for_method() -> None:
    code = "class Service:\n    def run(self):\n        return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.functions == ast_parsed.functions
