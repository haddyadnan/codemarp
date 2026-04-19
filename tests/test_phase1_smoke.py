from pathlib import Path

from codemarp.pipeline.discovery import discover_source_files
from codemarp.pipeline.module_ids import module_id_from_path


def test_module_id_from_path() -> None:
    root = Path("repo")
    path = root / "pkg" / "subpkg" / "file.py"
    assert module_id_from_path(root, path) == "pkg.subpkg.file"


def test_discover_source_files_ignores_virtualenv(tmp_path: Path) -> None:
    good = tmp_path / "app.py"
    good.write_text("print('ok')", encoding="utf-8")

    ignored = tmp_path / ".venv" / "lib.py"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("print('ignore')", encoding="utf-8")

    files = discover_source_files(tmp_path)
    assert good in files
    assert ignored not in files


def test_discover_source_files_includes_python_and_typescript(tmp_path: Path) -> None:
    py_file = tmp_path / "app.py"
    ts_file = tmp_path / "app.ts"
    tsx_file = tmp_path / "view.tsx"

    py_file.write_text("", encoding="utf-8")
    ts_file.write_text("", encoding="utf-8")
    tsx_file.write_text("", encoding="utf-8")

    assert discover_source_files(tmp_path) == [py_file, ts_file, tsx_file]
