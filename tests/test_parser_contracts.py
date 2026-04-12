from codemarp.parser.contracts import CallFact, FunctionFact, ImportFact, ParsedModule
from codemarp.parser.python_parser import PythonParser


def test_parse_code_to_facts_returns_parsed_module() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code_to_facts("def run():\n    return 1\n")

    assert isinstance(parsed, ParsedModule)
    assert parsed.module_id == "app.main"
    assert parsed.language == "python"
    assert len(parsed.functions) == 1
    assert parsed.functions[0].function_id == "app.main:run"
    assert parsed.functions[0].qualname == "run"


def test_parse_code_to_facts_captures_relative_from_import_without_module() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code_to_facts("from . import utils\n")

    assert parsed.imports == [
        ImportFact(
            raw_module=None,
            imported_name="utils",
            alias=None,
            is_from_import=True,
            relative_level=1,
            lineno=1,
        )
    ]


def test_parse_code_to_facts_captures_method_function_fact() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code_to_facts(
        "class Service:\n    def run(self):\n        return 1\n"
    )

    assert parsed.functions == [
        FunctionFact(
            function_id="app.main:Service.run",
            module_id="app.main",
            qualname="Service.run",
            short_name="run",
            class_name="Service",
            lineno=2,
            end_lineno=3,
            is_method=True,
            is_async=False,
        )
    ]


def test_parse_code_to_facts_captures_attribute_call_fact() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code_to_facts(
        "class Service:\n    def run(self):\n        self.save()\n"
    )

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:Service.run",
            raw="self.save",
            leaf_name="save",
            receiver="self",
            kind="attribute",
            lineno=3,
        )
    ]


def test_parse_code_to_facts_captures_super_call_fact() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code_to_facts(
        "class Child(Base):\n    def run(self):\n        super().run()\n"
    )

    assert parsed.calls == [
        CallFact(
            caller_id="app.main:Child.run",
            raw="super.run",
            leaf_name="run",
            receiver="super",
            kind="super",
            lineno=3,
        )
    ]
