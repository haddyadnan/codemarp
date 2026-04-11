from codemarp.analyzers.mid_level import build_mid_level_edges
from codemarp.parser.python_parser import PythonParser


def test_parser_tracks_imported_symbol() -> None:
    parser = PythonParser("app.main")
    result = parser.parse_code(
        "from app.worker import work\n\ndef run():\n    work()\n"
    )

    assert len(result.imported_symbols) == 1
    imported = result.imported_symbols[0]
    assert imported.module == "app.worker"
    assert imported.name == "work"
    assert imported.alias is None


def test_parser_tracks_imported_symbol_alias() -> None:
    parser = PythonParser("app.main")
    result = parser.parse_code(
        "from app.worker import work as do_work\n\ndef run():\n    do_work()\n"
    )

    assert len(result.imported_symbols) == 1
    imported = result.imported_symbols[0]
    assert imported.module == "app.worker"
    assert imported.name == "work"
    assert imported.alias == "do_work"


def test_parser_tracks_imported_module_alias() -> None:
    parser = PythonParser("app.main")
    result = parser.parse_code("import app.worker as w\n\ndef run():\n    w.work()\n")

    assert len(result.imported_modules) == 1
    imported = result.imported_modules[0]
    assert imported.module == "app.worker"
    assert imported.alias == "w"


def test_parser_keeps_plain_imports_for_high_level_analysis() -> None:
    parser = PythonParser("app.main")
    result = parser.parse_code("import app.worker\nfrom app.service import run\n")

    assert "app.worker" in result.imports
    assert "app.service" in result.imports


def test_mid_level_resolves_imported_symbol() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code(
        "from app.worker import work\n\ndef run():\n    work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code("def work():\n    return 1\n")

    functions = main.functions + worker.functions
    edges = build_mid_level_edges([main, worker], functions)

    assert {(edge.source, edge.target) for edge in edges} == {
        ("app.main:run", "app.worker:work")
    }


def test_mid_level_resolves_imported_symbol_alias() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code(
        "from app.worker import work as do_work\n\ndef run():\n    do_work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code("def work():\n    return 1\n")

    functions = main.functions + worker.functions
    edges = build_mid_level_edges([main, worker], functions)

    assert {(edge.source, edge.target) for edge in edges} == {
        ("app.main:run", "app.worker:work")
    }


def test_mid_level_resolves_imported_module_alias() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code(
        "import app.worker as w\n\ndef run():\n    w.work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code("def work():\n    return 1\n")

    functions = main.functions + worker.functions
    edges = build_mid_level_edges([main, worker], functions)

    assert {(edge.source, edge.target) for edge in edges} == {
        ("app.main:run", "app.worker:work")
    }


def test_mid_level_prefers_imported_symbol_over_ambiguous_global_name() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code("from app.a import run\n\ndef start():\n    run()\n")

    a_parser = PythonParser("app.a")
    mod_a = a_parser.parse_code("def run():\n    return 1\n")

    b_parser = PythonParser("app.b")
    mod_b = b_parser.parse_code("def run():\n    return 2\n")

    functions = main.functions + mod_a.functions + mod_b.functions
    edges = build_mid_level_edges([main, mod_a, mod_b], functions)

    assert {(edge.source, edge.target) for edge in edges} == {
        ("app.main:start", "app.a:run")
    }


def test_mid_level_leaves_ambiguous_global_call_unresolved() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code("def start():\n    run()\n")

    a_parser = PythonParser("app.a")
    mod_a = a_parser.parse_code("def run():\n    return 1\n")

    b_parser = PythonParser("app.b")
    mod_b = b_parser.parse_code("def run():\n    return 2\n")

    functions = main.functions + mod_a.functions + mod_b.functions
    edges = build_mid_level_edges([main, mod_a, mod_b], functions)

    assert edges == []
