from pathlib import Path

from tree_sitter import Language, Node, Parser
from tree_sitter_python import language as python_language

from codemarp.parser.contracts import CallFact, FunctionFact, ImportFact, ParsedModule


class TreeSitterPythonParser:
    def __init__(self, module_id: str) -> None:
        self.module_id = module_id
        self._parser = Parser(Language(python_language()))

    def parse_file(self, root: Path, path: Path) -> ParsedModule:
        code = path.read_text(encoding="utf-8")
        return self.parse_code_to_facts(
            code,
            filepath=str(path.relative_to(root)),
        )

    def parse_code_to_facts(
        self,
        code: str,
        *,
        filepath: str = "<memory>",
    ) -> ParsedModule:
        tree = self._parser.parse(code.encode("utf-8"))
        root_node = tree.root_node

        functions = self._extract_functions(root_node, code)
        imports = self._extract_imports(root_node, code)
        calls = self._extract_calls(root_node, code)

        return ParsedModule(
            module_id=self.module_id,
            file_path=Path(filepath),
            language="python",
            imports=imports,
            functions=functions,
            calls=calls,
            control_flow_roots=[],
        )

    def _extract_functions(self, root_node: Node, code: str) -> list[FunctionFact]:
        functions: list[FunctionFact] = []

        for child in root_node.children:
            if child.type in {"function_definition", "async_function_definition"}:
                fn = self._make_function_fact(child, code, class_name=None)
                if fn is not None:
                    functions.append(fn)

            elif child.type == "class_definition":
                class_name = self._node_text(child.child_by_field_name("name"), code)
                if class_name is None:
                    continue

                body = child.child_by_field_name("body")
                if body is None:
                    continue

                for class_child in body.children:
                    if class_child.type in {
                        "function_definition",
                        "async_function_definition",
                    }:
                        fn = self._make_function_fact(
                            class_child,
                            code,
                            class_name=class_name,
                        )
                        if fn is not None:
                            functions.append(fn)

        return functions

    def _make_function_fact(
        self,
        node: Node,
        code: str,
        *,
        class_name: str | None,
    ) -> FunctionFact | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None

        short_name = self._node_text(name_node, code)
        if short_name is None:
            return None

        qualname = f"{class_name}.{short_name}" if class_name else short_name
        function_id = f"{self.module_id}:{qualname}"

        return FunctionFact(
            function_id=function_id,
            module_id=self.module_id,
            qualname=qualname,
            short_name=short_name,
            class_name=class_name,
            lineno=node.start_point[0] + 1,
            end_lineno=node.end_point[0] + 1,
            is_method=class_name is not None,
            is_async=node.type == "async_function_definition",
        )

    def _node_text(self, node: Node | None, code: str) -> str | None:
        if node is None:
            return None
        source = code.encode("utf-8")
        return source[node.start_byte : node.end_byte].decode("utf-8")

    def _extract_imports(self, root_node: Node, code: str) -> list[ImportFact]:
        imports: list[ImportFact] = []

        for child in root_node.children:
            if child.type == "import_statement":
                imports.extend(self._extract_import_statement(child, code))
            elif child.type == "import_from_statement":
                imports.extend(self._extract_import_from_statement(child, code))

        return imports

    def _extract_import_statement(self, node: Node, code: str) -> list[ImportFact]:
        imports: list[ImportFact] = []

        for child in node.children:
            if child.type == "dotted_name":
                imports.append(
                    ImportFact(
                        raw_module=self._node_text(child, code),
                        imported_name=None,
                        alias=None,
                        is_from_import=False,
                        relative_level=0,
                        lineno=node.start_point[0] + 1,
                    )
                )
            elif child.type == "aliased_import":
                module_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")

                imports.append(
                    ImportFact(
                        raw_module=self._node_text(module_node, code),
                        imported_name=None,
                        alias=self._node_text(alias_node, code),
                        is_from_import=False,
                        relative_level=0,
                        lineno=node.start_point[0] + 1,
                    )
                )

        return imports

    def _extract_import_from_statement(self, node: Node, code: str) -> list[ImportFact]:
        imports: list[ImportFact] = []

        relative_level = 0
        module_name: str | None = None
        seen_module = False

        for child in node.children:
            if child.type == "relative_import":
                text = self._node_text(child, code)
                if text is not None:
                    relative_level = text.count(".")

            elif child.type == "dotted_name" and not seen_module:
                module_name = self._node_text(child, code)
                seen_module = True

            elif child.type == "dotted_name":
                imports.append(
                    ImportFact(
                        raw_module=module_name,
                        imported_name=self._node_text(child, code),
                        alias=None,
                        is_from_import=True,
                        relative_level=relative_level,
                        lineno=node.start_point[0] + 1,
                    )
                )

            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")

                imports.append(
                    ImportFact(
                        raw_module=module_name,
                        imported_name=self._node_text(name_node, code),
                        alias=self._node_text(alias_node, code),
                        is_from_import=True,
                        relative_level=relative_level,
                        lineno=node.start_point[0] + 1,
                    )
                )

        return imports

    def _extract_calls(self, root_node: Node, code: str) -> list[CallFact]:
        calls: list[CallFact] = []

        for child in root_node.children:
            if child.type in {"function_definition", "async_function_definition"}:
                calls.extend(
                    self._extract_calls_for_function(
                        child,
                        code,
                        class_name=None,
                    )
                )

            elif child.type == "class_definition":
                class_name = self._node_text(child.child_by_field_name("name"), code)
                if class_name is None:
                    continue

                body = child.child_by_field_name("body")
                if body is None:
                    continue

                for class_child in body.children:
                    if class_child.type in {
                        "function_definition",
                        "async_function_definition",
                    }:
                        calls.extend(
                            self._extract_calls_for_function(
                                class_child,
                                code,
                                class_name=class_name,
                            )
                        )

        return calls

    def _extract_calls_for_function(
        self,
        node: Node,
        code: str,
        *,
        class_name: str | None,
    ) -> list[CallFact]:
        name_node = node.child_by_field_name("name")
        short_name = self._node_text(name_node, code)
        if short_name is None:
            return []

        qualname = f"{class_name}.{short_name}" if class_name else short_name
        caller_id = f"{self.module_id}:{qualname}"

        calls: list[CallFact] = []

        body = node.child_by_field_name("body")
        if body is None:
            return calls

        for call_node in self._iter_call_nodes(body):
            call = self._make_call_fact(
                caller_id=caller_id,
                node=call_node,
                code=code,
            )
            if call.kind == "unknown":
                continue
            if call.kind == "bare" and call.raw == "super":
                continue
            calls.append(call)

        return calls

    def _iter_call_nodes(self, node: Node):
        for child in node.children:
            if child.type in {
                "function_definition",
                "async_function_definition",
                "class_definition",
            }:
                continue

            if child.type == "call":
                yield child

            yield from self._iter_call_nodes(child)

    def _make_call_fact(self, caller_id: str, node: Node, code: str) -> CallFact:
        raw = "<unknown>"
        leaf_name = "<unknown>"
        receiver: str | None = None
        kind = "unknown"

        func = node.child_by_field_name("function")

        if func is not None and func.type == "identifier":
            raw = self._node_text(func, code) or "<unknown>"
            leaf_name = raw
            kind = "bare"

        elif func is not None and func.type == "attribute":
            attribute_node = func.child_by_field_name("attribute")
            object_node = func.child_by_field_name("object")

            leaf_name = self._node_text(attribute_node, code) or "<unknown>"

            if object_node is not None and self._is_super_call(object_node, code):
                raw = f"super.{leaf_name}"
                receiver = "super"
                kind = "super"
            else:
                object_text = self._expression_text(object_node, code)
                if object_text is not None:
                    raw = f"{object_text}.{leaf_name}"
                    receiver = object_text
                    kind = "attribute"
                else:
                    raw = leaf_name
                    kind = "attribute"

        return CallFact(
            caller_id=caller_id,
            raw=raw,
            leaf_name=leaf_name,
            receiver=receiver,
            kind=kind,
            lineno=node.start_point[0] + 1,
        )

    def _is_super_call(self, node: Node, code: str) -> bool:
        if node.type != "call":
            return False

        func = node.child_by_field_name("function")
        return (
            func is not None
            and func.type == "identifier"
            and self._node_text(func, code) == "super"
        )

    def _expression_text(self, node: Node | None, code: str) -> str | None:
        if node is None:
            return None

        if node.type == "identifier":
            return self._node_text(node, code)

        if node.type == "attribute":
            attribute_node = node.child_by_field_name("attribute")
            object_node = node.child_by_field_name("object")

            attribute = self._node_text(attribute_node, code)
            object_text = self._expression_text(object_node, code)

            if attribute is None:
                return None
            if object_text is None:
                return attribute

            return f"{object_text}.{attribute}"

        if self._is_super_call(node, code):
            return "super"

        return None
