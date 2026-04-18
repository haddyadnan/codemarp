from pathlib import Path
from typing import Protocol

from codemarp.parser.contracts import ParsedModule


class LanguageParser(Protocol):
    def parse_file(self, root: Path, path: Path) -> ParsedModule: ...
