from pathlib import Path


def detect_language(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return "python"

    if suffix in [".ts", ".tsx"]:
        return "typescript"

    raise ValueError(f"Unsupported file type: {path}")
