from pathlib import Path

from codemarp.parser.python.ast_parser import PythonParser
from codemarp.parser.python.tree_sitter_parser import TreeSitterPythonParser
from codemarp.pipeline.build_bundle import parse_repo_files


def test_tree_sitter_parser_matches_ast_for_top_level_function() -> None:
    code = "def run():\n    return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.module_id == ast_parsed.module_id
    assert ts_parsed.language == ast_parsed.language
    assert ts_parsed.functions == ast_parsed.functions


def test_tree_sitter_parser_matches_ast_for_method() -> None:
    code = "class Service:\n    def run(self):\n        return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.functions == ast_parsed.functions


def test_tree_sitter_parser_matches_ast_for_imports() -> None:
    code = (
        "import app.worker\n"
        "import app.jobs as jobs\n"
        "from app.service import run\n"
        "from app.worker import work as do_work\n"
    )

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.imports == ast_parsed.imports


def test_tree_sitter_matches_ast_for_bare_call() -> None:
    code = "def run():\n    work()\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.calls == ast_parsed.calls


def test_tree_sitter_matches_ast_for_attribute_call() -> None:
    code = "def run():\n    worker.process()\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.calls == ast_parsed.calls


def test_tree_sitter_matches_ast_for_chained_attribute_call() -> None:
    code = "def run():\n    app.worker.process()\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.calls == ast_parsed.calls


def test_tree_sitter_matches_ast_for_super_call() -> None:
    code = "class Service:\n    def run(self):\n        super().save()\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.calls == ast_parsed.calls


def test_parse_repo_files_supports_tree_sitter_engine(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "app"
    pkg.mkdir(parents=True)

    (pkg / "main.py").write_text(
        "def run():\n    work()\n",
        encoding="utf-8",
    )

    parsed = parse_repo_files(repo, engine="tree-sitter")

    assert len(parsed) == 1
    assert parsed[0].module_id == "app.main"
    assert parsed[0].language == "python"


def test_tree_sitter_matches_ast_for_decorated_class_methods() -> None:
    code = (
        "@dataclass(slots=True)\n"
        "class GraphBundle:\n"
        "    def function_by_id(self):\n"
        "        return None\n"
        "\n"
        "    def to_dict(self):\n"
        "        return {}\n"
    )

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.functions == ast_parsed.functions


def test_tree_sitter_matches_ast_for_decorated_function() -> None:
    code = "@cache\ndef run():\n    return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.functions == ast_parsed.functions


def test_tree_sitter_matches_ast_for_async_method_in_decorated_class() -> None:
    code = "@decorator\nclass Service:\n    async def run(self):\n        return 1\n"

    ast_parsed = PythonParser("app.main").parse_code_to_facts(code)
    ts_parsed = TreeSitterPythonParser("app.main").parse_code_to_facts(code)

    assert ts_parsed.functions == ast_parsed.functions
