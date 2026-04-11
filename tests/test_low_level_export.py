from pathlib import Path

from codemarp.analyzers.low_level import build_low_level_view
from codemarp.pipeline.build_bundle import build_bundle
from codemarp.pipeline.export_all import export_low_level


def test_export_low_level_writes_expected_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    out_dir = tmp_path / "out"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run(flag):\n    if flag:\n        return 1\n    return 2\n",
        encoding="utf-8",
    )

    build_result = build_bundle(repo)
    low_view = build_low_level_view(repo, "app.main:run")
    export_low_level(build_result=build_result, low_view=low_view, out_dir=out_dir)

    assert (out_dir / "graph.json").exists()
    assert (out_dir / "high_level.mmd").exists()
    assert (out_dir / "low_level.mmd").exists()
    assert (out_dir / "low_level.json").exists()
