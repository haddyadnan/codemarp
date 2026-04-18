from codemarp.parser.base import LanguageParser
from codemarp.parser.python.ast_parser import PythonParser


def get_parser(language: str, module_id: str) -> LanguageParser:
    if language == "python":
        return PythonParser(module_id)

    raise ValueError(f"Unsupported language: {language}")
