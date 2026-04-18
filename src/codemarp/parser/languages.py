from pathlib import Path


def detect_language(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return "python"

    raise ValueError(f"Unsupported file type: {path}")
