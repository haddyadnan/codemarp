import ast
from pathlib import Path

from codemarp.errors import FocusFormatError, ResolutionError
from codemarp.pipeline.discovery import discover_source_files
from codemarp.pipeline.module_ids import module_id_from_path


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

    for file_path in discover_source_files(root):
        if file_path.suffix.lower() != ".py":
            continue
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
