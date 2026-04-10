from pathlib import Path

from codemap.pipeline.apply_view import ViewType, apply_view
from codemap.pipeline.build_bundle import build_bundle
from codemap.pipeline.export_all import export_all


def test_build_bundle_returns_full_graph_result(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text(
        "from app.worker import work\n\ndef run():\n    work()\n",
        encoding="utf-8",
    )
    (pkg / "worker.py").write_text(
        "def work():\n    return 1\n",
        encoding="utf-8",
    )

    result = build_bundle(repo)

    assert len(result.bundle.modules) == 2
    assert any(fn.id == "app.main:run" for fn in result.bundle.functions)
    assert any(edge.kind == "calls" for edge in result.bundle.edges)
    assert (
        "app.main" in result.high_level_package_ids
        or "app" in result.high_level_package_ids
    )


def test_apply_view_returns_full_bundle_without_focus(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text(
        "def run():\n    return 1\n",
        encoding="utf-8",
    )

    result = build_bundle(repo)
    view = apply_view(result.bundle, view=ViewType.FULL)

    assert view is result.bundle


def test_apply_view_traces_when_focus_is_given(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text(
        "from app.worker import work\n\ndef run():\n    work()\n",
        encoding="utf-8",
    )
    (pkg / "worker.py").write_text(
        "def work():\n    return 1\n",
        encoding="utf-8",
    )

    result = build_bundle(repo)
    view = apply_view(
        result.bundle,
        view=ViewType.TRACE,
        focus="app.main:run",
        max_depth=1,
    )

    assert {fn.id for fn in view.functions} == {"app.main:run", "app.worker:work"}


def test_export_all_writes_full_and_view_outputs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    out_dir = tmp_path / "out"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text(
        "from app.worker import work\n\ndef run():\n    work()\n",
        encoding="utf-8",
    )
    (pkg / "worker.py").write_text(
        "def work():\n    return 1\n",
        encoding="utf-8",
    )

    result = build_bundle(repo)
    view = apply_view(
        result.bundle,
        view=ViewType.TRACE,
        focus="app.main:run",
        max_depth=1,
    )
    export_all(build_result=result, view=view, out_dir=out_dir)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "mid_level.mmd").exists()
    assert (out_dir / "mid_level.json").exists()
