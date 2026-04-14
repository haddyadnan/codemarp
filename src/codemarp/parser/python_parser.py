import ast
from dataclasses import dataclass, field
from pathlib import Path

from codemarp.errors import FocusFormatError, ResolutionError
from codemarp.graph.models import FunctionNode
from codemarp.parser.contracts import (
    CallFact,
    ControlFlowRootFact,
    FunctionFact,
    ImportFact,
    ParsedModule,
)

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
    "tests",
}

IGNORE_FILE_NAMES = {
    "__init__.py",
}


@dataclass(slots=True)
class ImportedModule:
    module: str
    alias: str | None = None


@dataclass(slots=True)
class ImportedSymbol:
    module: str
    name: str
    alias: str | None = None


@dataclass(slots=True)
class ParsedPythonModule:
    module_id: str
    path: str
    imports: list[str] = field(default_factory=list)
    imported_modules: list[ImportedModule] = field(default_factory=list)
    imported_symbols: list[ImportedSymbol] = field(default_factory=list)
    functions: list[FunctionNode] = field(default_factory=list)
    calls: list = field(default_factory=list)


class PythonParser(ast.NodeVisitor):
    def __init__(self, module_id: str) -> None:
        self.module_id = module_id
        self._reset_state()

    def _reset_state(self) -> None:
        self.imports = []
        self.imported_modules = []
        self.imported_symbols = []
        self.functions = []
        self.calls = []

        self.import_facts = []
        self.function_facts = []
        self.call_facts = []
        self.control_flow_roots = []

        self._function_stack = []
        self._class_stack = []

    def parse_code(
        self, code: str, *, filepath: str = "<memory>"
    ) -> ParsedPythonModule:
        # Legacy parser output retained temporarily for compatibility tests.
        # New analyzer/pipeline code should use parse_code_to_facts().

        self._reset_state()
        tree = ast.parse(code, filename=filepath)
        self.visit(tree)

        return ParsedPythonModule(
            module_id=self.module_id,
            path=filepath,
            imports=self.imports,
            imported_modules=self.imported_modules,
            imported_symbols=self.imported_symbols,
            functions=self.functions,
            calls=self.calls,
        )

    def parse_code_to_facts(
        self, code: str, *, filepath: str = "<memory>"
    ) -> ParsedModule:
        self._reset_state()
        tree = ast.parse(code, filename=filepath)
        self.visit(tree)

        return ParsedModule(
            module_id=self.module_id,
            file_path=Path(filepath),
            language="python",
            imports=self.import_facts,
            functions=self.function_facts,
            calls=self.call_facts,
            control_flow_roots=self.control_flow_roots,
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
            self.imported_modules.append(
                ImportedModule(
                    module=alias.name,
                    alias=alias.asname,
                )
            )
            self.import_facts.append(
                ImportFact(
                    raw_module=alias.name,
                    imported_name=None,
                    alias=alias.asname,
                    is_from_import=False,
                    relative_level=0,
                    lineno=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)

        for alias in node.names:
            if node.module:
                self.imported_symbols.append(
                    ImportedSymbol(
                        module=node.module,
                        name=alias.name,
                        alias=alias.asname,
                    )
                )

            self.import_facts.append(
                ImportFact(
                    raw_module=node.module,
                    imported_name=alias.name,
                    alias=alias.asname,
                    is_from_import=True,
                    relative_level=node.level,
                    lineno=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_like(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_like(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._function_stack:
            caller_id = self._function_stack[-1]
            callee = self._resolve_call_name(node.func)
            if callee and callee != "super":
                self.calls.append((caller_id, callee))
                self.call_facts.append(
                    self._make_call_fact(
                        caller_id=caller_id,
                        node=node,
                    )
                )
        self.generic_visit(node)

    def _visit_function_like(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        class_name = self._class_stack[-1] if self._class_stack else None
        fn_name = f"{class_name}.{node.name}" if class_name else node.name
        function_id = f"{self.module_id}:{fn_name}"
        self.functions.append(
            FunctionNode(
                id=function_id,
                name=fn_name,
                module_id=self.module_id,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", node.lineno),
                class_name=class_name,
            )
        )

        self.function_facts.append(
            FunctionFact(
                function_id=function_id,
                module_id=self.module_id,
                qualname=fn_name,
                short_name=node.name,
                class_name=class_name,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", node.lineno),
                is_method=class_name is not None,
                is_async=isinstance(node, ast.AsyncFunctionDef),
            )
        )

        self.control_flow_roots.append(
            ControlFlowRootFact(
                function_id=function_id,
                syntax_ref=node,
            )
        )

        self._function_stack.append(function_id)
        self.generic_visit(node)
        self._function_stack.pop()

    def _resolve_call_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parts: list[str] = [node.attr]
            value = node.value

            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value

            if isinstance(value, ast.Name):
                parts.append(value.id)
                return ".".join(reversed(parts))

            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "super"
            ):
                parts.append("super")
                return ".".join(reversed(parts))

            return node.attr

        return None

    def _make_call_fact(self, caller_id: str, node: ast.Call) -> CallFact:
        raw = "<unknown>"
        leaf_name = "<unknown>"
        receiver: str | None = None
        kind = "unknown"

        func = node.func

        if isinstance(func, ast.Name):
            raw = func.id
            leaf_name = func.id
            kind = "bare"

        elif isinstance(func, ast.Attribute):
            parts: list[str] = [func.attr]
            value = func.value

            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value

            if isinstance(value, ast.Name):
                parts.append(value.id)
                raw = ".".join(reversed(parts))
                leaf_name = func.attr
                receiver = ".".join(reversed(parts[1:])) if len(parts) > 1 else None
                kind = "attribute"

            elif (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "super"
            ):
                raw = f"super.{func.attr}"
                leaf_name = func.attr
                receiver = "super"
                kind = "super"

            else:
                raw = func.attr
                leaf_name = func.attr
                kind = "attribute"

        return CallFact(
            caller_id=caller_id,
            raw=raw,
            leaf_name=leaf_name,
            receiver=receiver,
            kind=kind,
            lineno=node.lineno,
        )


def discover_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if path.name in IGNORE_FILE_NAMES:
            continue
        files.append(path)
    return sorted(files)


def module_id_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else path.stem


def package_from_module_id(module_id: str) -> str:
    if "." not in module_id:
        return ""
    return module_id.rsplit(".", 1)[0]


def parse_python_file(root: Path, path: Path) -> ParsedModule:
    module_id = module_id_from_path(root, path)
    parser = PythonParser(module_id)
    code = path.read_text(encoding="utf-8")
    return parser.parse_code_to_facts(code, filepath=str(path.relative_to(root)))


def parse_low_level_focus(focus: str) -> tuple[str, str]:
    """
    Parse a low-level focus string.

    Supported formats:
    - module:function_name
    - module:ClassName.method_name
    """
    parts = focus.split(":")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise FocusFormatError(
            "Invalid --focus format for low view. Expected:\n"
            "  module:function_name\n"
            "or\n"
            "  module:ClassName.method_name"
        )

    module_id, target_name = parts
    return module_id, target_name


def find_function_node(
    root: Path,
    focus: str,
) -> tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """
    Resolve a low-level focus string to a function/method AST node.

    Returns:
        (normalized_function_id, ast node)
    """
    module_id, target_name = parse_low_level_focus(focus)

    for file_path in discover_python_files(root):
        current_module_id = module_id_from_path(root, file_path)
        if current_module_id != module_id:
            continue

        code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(file_path))
        node = _find_function_in_tree(tree, target_name)
        if node is None:
            raise ResolutionError(f"Function or method not found: {focus}")

        normalized_function_id = f"{module_id}:{target_name}"
        return normalized_function_id, node

    raise ResolutionError(f"Module not found for low view: {module_id}")


def _find_function_in_tree(
    tree: ast.AST,
    target_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """
    Find either:
    - top-level function: function_name
    - class method: ClassName.method_name
    """
    if "." in target_name:
        class_name, method_name = target_name.split(".", 1)
        for node in tree.body if isinstance(tree, ast.Module) else []:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for child in node.body:
                    if (
                        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and child.name == method_name
                    ):
                        return child
        return None

    for node in tree.body if isinstance(tree, ast.Module) else []:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == target_name
        ):
            return node

    return None
