from pathlib import Path

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
    "tests",
}

IGNORE_FILE_NAMES = {
    "__init__.py",
}


def discover_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if path.name in IGNORE_FILE_NAMES:
            continue
        files.append(path)
    return sorted(files)
