from codemarp.parser.base import LanguageParser
from codemarp.parser.python.ast_parser import PythonParser
from codemarp.parser.python.tree_sitter_parser import TreeSitterPythonParser


def get_parser(
    language: str, module_id: str, engine: str = "tree-sitter"
) -> LanguageParser:
    if language == "python":
        if engine == "tree-sitter":
            return TreeSitterPythonParser(module_id)
        if engine == "ast":
            return PythonParser(module_id)
        raise ValueError(f"Unsupported parser engine: {engine}")

    raise ValueError(f"Unsupported language: {language}")
