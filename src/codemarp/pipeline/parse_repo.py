from pathlib import Path

from codemarp.parser.contracts import ParsedModule
from codemarp.parser.factory import get_parser
from codemarp.parser.languages import detect_language
from codemarp.parser.python.ast_parser import module_id_from_path
from codemarp.pipeline.discovery import discover_python_files


def parse_repo_files(root: Path, engine: str = "ast") -> list[ParsedModule]:
    parsed_modules: list[ParsedModule] = []

    for path in discover_python_files(root):
        language = detect_language(path)
        module_id = module_id_from_path(root, path)
        parser = get_parser(language, module_id, engine=engine)
        parsed = parser.parse_file(root, path)
        parsed_modules.append(parsed)

    return parsed_modules
