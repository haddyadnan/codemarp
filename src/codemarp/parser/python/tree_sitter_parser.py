from pathlib import Path

from codemarp.parser.contracts import ParsedModule


class TreeSitterPythonParser:
    def __init__(self, module_id: str) -> None:
        self.module_id = module_id

    def parse_file(self, root: Path, path: Path) -> ParsedModule:
        raise NotImplementedError
