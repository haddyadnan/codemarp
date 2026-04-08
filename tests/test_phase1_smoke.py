from pathlib import Path

from src.codemap.parser.python_parser import (
    discover_python_files,
    module_id_from_path,
    package_from_module_id,
)


def test_module_id_from_path() -> None:
    root = Path("repo")
    path = root / "pkg" / "subpkg" / "file.py"
    assert module_id_from_path(root, path) == "pkg.subpkg.file"


def test_package_from_module_id() -> None:
    assert package_from_module_id("pkg.subpkg.file") == "pkg.subpkg"
    assert package_from_module_id("main") == ""


def test_discover_python_files_ignores_virtualenv(tmp_path: Path) -> None:
    good = tmp_path / "app.py"
    good.write_text("print('ok')", encoding="utf-8")

    ignored = tmp_path / ".venv" / "lib.py"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("print('ignore')", encoding="utf-8")

    files = discover_python_files(tmp_path)
    assert good in files
    assert ignored not in files
