from codemarp.parser.python_parser import PythonParser


def test_parser_preserves_self_method_call_as_dotted_name() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code(
        "class Service:\n"
        "    def run(self):\n"
        "        self.save()\n"
        "\n"
        "    def save(self):\n"
        "        return 1\n"
    )

    assert any(call[1] == "self.save" for call in parsed.calls)


def test_parser_preserves_imported_module_alias_call_as_dotted_name() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code("import app.worker as w\n\ndef run():\n    w.work()\n")

    assert any(call[1] == "w.work" for call in parsed.calls)


def test_parser_preserves_super_method_call_as_dotted_name() -> None:
    parser = PythonParser("app.main")
    parsed = parser.parse_code(
        "class Child(Base):\n    def run(self):\n        super().run()\n"
    )

    assert any(call[1] == "super.run" for call in parsed.calls)
