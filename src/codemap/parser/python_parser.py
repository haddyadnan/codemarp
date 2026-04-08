import ast
from dataclasses import dataclass, field
from pathlib import Path

from codemap.graph.models import FunctionNode

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
    "__init__.py",
    "tests",
}


@dataclass(slots=True)
class ParsedPythonModule:
    module_id: str
    path: str
    imports: list[str] = field(default_factory=list)
    functions: list[FunctionNode] = field(default_factory=list)
    calls: list = field(default_factory=list)


class PythonParser(ast.NodeVisitor):
    def __init__(self, module_id: str) -> None:
        self.module_id = module_id
        self.imports = []
        self.functions = []
        self.calls = []
        self._function_stack = []
        self._class_stack = []

    def parse_code(
        self, code: str, *, filepath: str = "<memory>"
    ) -> ParsedPythonModule:
        tree = ast.parse(code, filename=filepath)
        self.visit(tree)

        return ParsedPythonModule(
            module_id=self.module_id,
            path=filepath,
            imports=self.imports,
            functions=self.functions,
            calls=self.calls,
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
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
            callee = self._resolve_call_name(node.func)
            if callee:
                self.calls.append((self._function_stack[-1], callee))
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
        self._function_stack.append(function_id)
        self.generic_visit(node)
        self._function_stack.pop()

    def _resolve_call_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None


def discover_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
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


def parse_python_file(root: Path, path: Path) -> ParsedPythonModule:
    module_id = module_id_from_path(root, path)
    parser = PythonParser(module_id)
    code = path.read_text(encoding="utf-8")
    return parser.parse_code(code, filepath=str(path.relative_to(root)))
