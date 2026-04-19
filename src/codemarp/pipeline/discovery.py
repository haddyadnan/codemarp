import os
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
    # JS/TS generated or dependency directories
    ".cache",
    ".next",
    ".nuxt",
    ".output",
    ".svelte-kit",
    ".turbo",
    ".vercel",
    "coverage",
    "out",
    "storybook-static",
}

IGNORE_FILE_NAMES = {
    "__init__.py",
}


SUPPORTED_SUFFIXES = {".py", ".ts", ".tsx"}


def discover_source_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]

        for filename in filenames:
            if filename in IGNORE_FILE_NAMES:
                continue

            suffix = Path(filename).suffix.lower()
            if suffix not in SUPPORTED_SUFFIXES:
                continue

            files.append(Path(dirpath) / filename)

    return sorted(files)
