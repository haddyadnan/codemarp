from codemarp.analyzers.mid_level import build_mid_level_edges
from codemarp.contracts import ResolutionReason
from codemarp.exporters.mermaid import export_function_graph
from codemarp.graph.models import FunctionNode, GraphBundle
from codemarp.parser.python_parser import PythonParser


def _function_nodes(*parsed_modules) -> list[FunctionNode]:
    out: list[FunctionNode] = []
    for parsed in parsed_modules:
        for fn in parsed.functions:
            out.append(
                FunctionNode(
                    id=fn.function_id,
                    name=fn.qualname,
                    module_id=fn.module_id,
                    lineno=fn.lineno,
                    end_lineno=fn.end_lineno or fn.lineno,
                    class_name=fn.class_name,
                )
            )
    return out


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
    main = main_parser.parse_code_to_facts(
        "from app.worker import work\n\ndef run():\n    work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code_to_facts("def work():\n    return 1\n")

    functions = _function_nodes(main, worker)
    edges = build_mid_level_edges([main, worker], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:run", "app.worker:work")
    assert edge.reason == ResolutionReason.IMPORTED_SYMBOL


def test_mid_level_resolves_imported_symbol_alias() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts(
        "from app.worker import work as do_work\n\ndef run():\n    do_work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code_to_facts("def work():\n    return 1\n")

    functions = _function_nodes(main, worker)
    edges = build_mid_level_edges([main, worker], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:run", "app.worker:work")
    assert edge.reason == ResolutionReason.IMPORTED_SYMBOL


def test_mid_level_resolves_imported_module_alias() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts(
        "import app.worker as w\n\ndef run():\n    w.work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code_to_facts("def work():\n    return 1\n")

    functions = _function_nodes(main, worker)
    edges = build_mid_level_edges([main, worker], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:run", "app.worker:work")
    assert edge.reason == ResolutionReason.IMPORTED_MODULE


def test_mid_level_prefers_imported_symbol_over_ambiguous_global_name() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts(
        "from app.a import run\n\ndef start():\n    run()\n"
    )

    a_parser = PythonParser("app.a")
    mod_a = a_parser.parse_code_to_facts("def run():\n    return 1\n")

    b_parser = PythonParser("app.b")
    mod_b = b_parser.parse_code_to_facts("def run():\n    return 2\n")

    functions = _function_nodes(main, mod_a, mod_b)
    edges = build_mid_level_edges([main, mod_a, mod_b], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:start", "app.a:run")
    assert edge.reason == ResolutionReason.IMPORTED_SYMBOL


def test_mid_level_leaves_ambiguous_global_call_unresolved() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts("def start():\n    run()\n")

    a_parser = PythonParser("app.a")
    mod_a = a_parser.parse_code_to_facts("def run():\n    return 1\n")

    b_parser = PythonParser("app.b")
    mod_b = b_parser.parse_code_to_facts("def run():\n    return 2\n")

    functions = _function_nodes(main, mod_a, mod_b)
    edges = build_mid_level_edges([main, mod_a, mod_b], functions)

    assert edges == []


def test_mid_level_does_not_resolve_self_method_call_by_short_name_fallback() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts(
        "class Service:\n"
        "    def run(self):\n"
        "        self.save()\n"
        "\n"
        "def save():\n"
        "    return 1\n"
    )

    functions = _function_nodes(main)
    edges = build_mid_level_edges([main], functions)

    assert {(edge.source, edge.target) for edge in edges} == set()


def test_mid_level_still_resolves_imported_module_alias_call() -> None:
    main_parser = PythonParser("app.main")
    main = main_parser.parse_code_to_facts(
        "import app.worker as w\n\ndef run():\n    w.work()\n"
    )

    worker_parser = PythonParser("app.worker")
    worker = worker_parser.parse_code_to_facts("def work():\n    return 1\n")

    functions = _function_nodes(main, worker)
    edges = build_mid_level_edges([main, worker], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:run", "app.worker:work")
    assert edge.reason == ResolutionReason.IMPORTED_MODULE


def test_mid_level_resolves_same_module_call() -> None:
    parser = PythonParser("app.main")
    main = parser.parse_code_to_facts(
        "def helper():\n    return 1\n\ndef run():\n    helper()\n"
    )

    functions = _function_nodes(main)
    edges = build_mid_level_edges([main], functions)

    assert len(edges) == 1
    edge = edges[0]
    assert (edge.source, edge.target) == ("app.main:run", "app.main:helper")
    assert edge.reason == ResolutionReason.SAME_MODULE


def test_export_function_graph_dedupes_function_nodes() -> None:
    fn = FunctionNode(
        id="app.main:run",
        name="run",
        module_id="app.main",
        lineno=1,
        end_lineno=2,
        class_name=None,
    )

    mermaid = export_function_graph(
        functions=[fn, fn],
        edges=[],
    )

    assert mermaid.count('app_main_run["app.main:run"]') == 1


def test_graph_bundle_to_dict_dedupes_functions() -> None:
    fn = FunctionNode(
        id="app.main:run",
        name="run",
        module_id="app.main",
        lineno=1,
        end_lineno=1,
        class_name=None,
    )

    bundle = GraphBundle(functions=[fn, fn])
    data = bundle.to_dict()

    assert len(data["functions"]) == 1
