from pathlib import Path

from codemarp.parser.contracts import ParsedModule
from codemarp.parser.factory import get_parser
from codemarp.parser.languages import detect_language
from codemarp.pipeline.discovery import discover_source_files
from codemarp.pipeline.module_ids import module_id_from_path


def parse_repo_files(root: Path, engine: str = "tree-sitter") -> list[ParsedModule]:
    parsed_modules: list[ParsedModule] = []

    for path in discover_source_files(root):
        language = detect_language(path)
        module_id = module_id_from_path(root, path)
        parser = get_parser(language, module_id, engine=engine)
        parsed = parser.parse_file(root, path)
        parsed_modules.append(parsed)

    return parsed_modules
