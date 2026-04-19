"""
## Known Limitations

- Arrow functions assigned to variables are not yet extracted as FunctionFact.
- Function expressions assigned to variables are not yet extracted as FunctionFact.
- Re-export forms such as `export { foo } from "./foo"` and `export * from "./bar"` are not yet normalized as imports.
- CommonJS `require()` calls are not yet normalized as imports.
- Template-literal import sources are not specially handled.
- Only declarations that normalize cleanly into the shared facts contract are extracted.
- If a TypeScript construct has no clear equivalent in the shared facts, it is omitted rather than guessed.
"""

from pathlib import Path

import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Node, Parser

from codemarp.parser.contracts import FunctionFact, ImportFact, ParsedModule


class TreeSitterTypeScriptParser:
    def __init__(self, module_id: str) -> None:
        self.module_id = module_id
        self._parser = Parser(Language(tstypescript.language_typescript()))

    def parse_file(self, root: Path, path: Path) -> ParsedModule:
        code = path.read_text(encoding="utf-8")
        return self.parse_code_to_facts(
            code,
            filepath=str(path.relative_to(root)),
        )

    def parse_code_to_facts(
        self, code: str, filepath: str = "<memory>"
    ) -> ParsedModule:
        tree = self._parser.parse(code.encode("utf-8"))
        root_node = tree.root_node

        return ParsedModule(
            module_id=self.module_id,
            file_path=Path(filepath),
            language="typescript",
            imports=self._extract_imports(root_node, code),
            functions=self._extract_functions(root_node, code),
            calls=[],
            control_flow_roots=[],
        )

    def _extract_functions(self, root_node: Node, code: str) -> list[FunctionFact]:
        functions: list[FunctionFact] = []

        for child in root_node.children:
            target = self._unwrap_definition(child)

            if target is None:
                continue

            if target.type == "function_declaration":
                fn = self._make_function_fact(target, code, class_name=None)
                if fn is not None:
                    functions.append(fn)

            elif target.type == "class_declaration":
                class_name = self._node_text(target.child_by_field_name("name"), code)
                if class_name is None:
                    continue

                body = target.child_by_field_name("body")
                if body is None:
                    continue

                for class_child in body.children:
                    if class_child.type == "method_definition":
                        fn = self._make_method_fact(
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
            is_async=any(child.type == "async" for child in node.children),
        )

    def _make_method_fact(
        self,
        node: Node,
        code: str,
        *,
        class_name: str,
    ) -> FunctionFact | None:
        name_node = node.child_by_field_name("name")
        short_name = self._node_text(name_node, code)
        if short_name is None:
            return None

        qualname = f"{class_name}.{short_name}"
        function_id = f"{self.module_id}:{qualname}"

        return FunctionFact(
            function_id=function_id,
            module_id=self.module_id,
            qualname=qualname,
            short_name=short_name,
            class_name=class_name,
            lineno=node.start_point[0] + 1,
            end_lineno=node.end_point[0] + 1,
            is_method=True,
            is_async=any(child.type == "async" for child in node.children),
        )

    def _node_text(self, node: Node | None, code: str) -> str | None:
        if node is None:
            return None
        source = code.encode("utf-8")
        return source[node.start_byte : node.end_byte].decode("utf-8")

    def _unwrap_definition(self, node: Node) -> Node | None:
        if node.type in {"export_statement", "export_default_declaration"}:
            for child in node.children:
                if child.type in {"function_declaration", "class_declaration"}:
                    return child
            return None

        return node

    def _extract_imports(self, root_node: Node, code: str) -> list[ImportFact]:
        imports: list[ImportFact] = []

        for child in root_node.children:
            if child.type == "import_statement":
                imports.extend(self._extract_import_statement(child, code))

        return imports

    def _extract_import_statement(self, node: Node, code: str) -> list[ImportFact]:
        imports: list[ImportFact] = []

        source_node = node.child_by_field_name("source")
        if source_node is None:
            source_node = self._first_child_of_type(node, "string")

        raw_module = self._string_text(source_node, code)
        if raw_module is None:
            return imports

        clause_node = node.child_by_field_name("import_clause")
        if clause_node is None:
            clause_node = self._first_child_of_type(node, "import_clause")
        if clause_node is None:
            return imports

        for child in clause_node.children:
            # Default TS imports are normalized as module imports with an alias.
            # They do not map cleanly to Python-style "from x import y".
            if child.type == "identifier":
                imports.append(
                    ImportFact(
                        raw_module=raw_module,
                        imported_name=None,
                        alias=self._node_text(child, code),
                        is_from_import=False,
                        relative_level=0,
                        lineno=node.start_point[0] + 1,
                    )
                )

            elif child.type == "named_imports":
                imports.extend(
                    self._extract_named_imports(
                        child,
                        code,
                        raw_module=raw_module,
                        lineno=node.start_point[0] + 1,
                    )
                )

            elif child.type == "namespace_import":
                identifiers = self._children_of_type(child, "identifier")
                alias_node = identifiers[0] if identifiers else None

                imports.append(
                    ImportFact(
                        raw_module=raw_module,
                        imported_name=None,
                        alias=self._node_text(alias_node, code),
                        is_from_import=False,
                        relative_level=0,
                        lineno=node.start_point[0] + 1,
                    )
                )

        return imports

    def _extract_named_imports(
        self,
        node: Node,
        code: str,
        *,
        raw_module: str,
        lineno: int,
    ) -> list[ImportFact]:
        imports: list[ImportFact] = []

        for child in node.children:
            if child.type != "import_specifier":
                continue

            name_node = child.child_by_field_name("name")
            alias_node = child.child_by_field_name("alias")

            if name_node is None:
                identifiers = self._children_of_type(child, "identifier")
                # first identifier = imported name
                # second identifier = alias (if present)
                name_node = identifiers[0] if identifiers else None
                alias_node = identifiers[1] if len(identifiers) > 1 else None

            imported_name = self._node_text(name_node, code)
            if imported_name is None:
                continue

            imports.append(
                ImportFact(
                    raw_module=raw_module,
                    imported_name=imported_name,
                    alias=self._node_text(alias_node, code),
                    is_from_import=True,
                    relative_level=0,
                    lineno=lineno,
                )
            )

        return imports

    def _string_text(self, node: Node | None, code: str) -> str | None:
        text = self._node_text(node, code)
        if text is None:
            return None

        if len(text) >= 2 and text[0] in {"'", '"'} and text[-1] == text[0]:
            return text[1:-1]

        return text

    def _first_child_of_type(self, node: Node, type_: str) -> Node | None:
        for child in node.children:
            if child.type == type_:
                return child
        return None

    def _children_of_type(self, node: Node, type_: str) -> list[Node]:
        return [child for child in node.children if child.type == type_]
