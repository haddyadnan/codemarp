import ast
from dataclasses import dataclass
from pathlib import Path

from codemap.graph.models import ControlFlowNode, Edge
from codemap.parser.python_parser import find_function_node


@dataclass(slots=True)
class LowLevelResult:
    function_id: str
    nodes: list[ControlFlowNode]
    edges: list[Edge]


def build_low_level_view(root: str | Path, focus: str) -> LowLevelResult:
    function_id, function_node = find_function_node(Path(root), focus)
    builder = ControlFlowBuilder()
    nodes, edges = builder.build_for_function(function_node)
    return LowLevelResult(function_id=function_id, nodes=nodes, edges=edges)


class ControlFlowBuilder:
    def __init__(self) -> None:
        self.nodes: list[ControlFlowNode] = []
        self.edges: list[Edge] = []
        self._counter = 0

    def build_for_function(
        self,
        function_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> tuple[list[ControlFlowNode], list[Edge]]:
        start = self._new_node("Start", "start", lineno=function_node.lineno)
        exits = self._walk_statements(function_node.body, [start])
        end = self._new_node(
            "End",
            "end",
            lineno=getattr(function_node, "end_lineno", function_node.lineno),
        )

        for exit_node in exits:
            self._add_edge(exit_node, end)

        return self.nodes, self.edges

    def _walk_statements(
        self,
        statements: list[ast.stmt],
        incoming: list[str],
    ) -> list[str]:
        exits = incoming
        for statement in statements:
            exits = self._handle_statement(statement, exits)
        return exits

    def _handle_statement(
        self, statement: ast.stmt, incoming: list[str], edge_label: str | None = None
    ) -> list[str]:
        if isinstance(statement, ast.If):
            return self._handle_if(statement, incoming)

        if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            return self._handle_loop(statement, incoming)

        if isinstance(statement, ast.Try):
            node = self._new_node("Try/Except", "statement", lineno=statement.lineno)
            for index, source in enumerate(incoming):
                self._add_edge(source, node, label=edge_label if index == 0 else None)
            return [node]

        if isinstance(statement, ast.Return):
            node = self._new_node("Return", "terminal", lineno=statement.lineno)
            for index, source in enumerate(incoming):
                self._add_edge(source, node, label=edge_label if index == 0 else None)
            return [node]

        if isinstance(statement, ast.Raise):
            node = self._new_node("Raise", "terminal", lineno=statement.lineno)
            for index, source in enumerate(incoming):
                self._add_edge(source, node, label=edge_label if index == 0 else None)
            return [node]

        label = self._statement_label(statement)
        node = self._new_node(label, "statement", lineno=statement.lineno)
        for index, source in enumerate(incoming):
            self._add_edge(source, node, label=edge_label if index == 0 else None)
        return [node]

    def _walk_branch_statements(
        self,
        statements: list[ast.stmt],
        condition_node: str,
        *,
        branch_label: str,
    ) -> list[str]:
        # if not statements:
        #     empty_branch = self._new_node(branch_label, "branch")
        #     self._add_edge(condition_node, empty_branch, label=branch_label)
        #     return [empty_branch]

        if not statements:
            return [condition_node]

        first_exits = self._handle_statement(
            statements[0], [condition_node], edge_label=branch_label
        )
        if len(statements) == 1:
            return first_exits
        return self._walk_statements(statements[1:], first_exits)

    def _handle_if(self, statement: ast.If, incoming: list[str]) -> list[str]:
        condition = self._new_node(
            self._expr_label(statement.test),
            "decision",
            lineno=statement.lineno,
        )
        for source in incoming:
            self._add_edge(source, condition)

        # then_entry = self._new_node("Then", "branch", lineno=statement.lineno)
        # else_entry = self._new_node("Else", "branch", lineno=statement.lineno)

        # self._add_edge(condition, then_entry, label="True")
        # self._add_edge(condition, else_entry, label="False")

        then_exits = self._walk_branch_statements(
            statement.body, condition, branch_label="True"
        )

        else_exits = self._walk_branch_statements(
            statement.orelse, condition, branch_label="False"
        )

        then_empty = condition in then_exits
        else_empty = condition in else_exits

        non_terminals = [
            node_id
            for node_id in then_exits + else_exits
            if node_id != condition and self._node_kind(node_id) != "terminal"
        ]
        if non_terminals or then_empty or else_empty:
            merge = self._new_node("Merge", "merge", lineno=statement.lineno)

            for source in non_terminals:
                self._add_edge(source, merge)

            if then_empty:
                self._add_edge(condition, merge, label="True")
            if else_empty:
                self._add_edge(condition, merge, label="False")

            return [merge]

        return []

    def _handle_loop(
        self,
        statement: ast.For | ast.AsyncFor | ast.While,
        incoming: list[str],
    ) -> list[str]:
        loop_label = type(statement).__name__
        loop = self._new_node(loop_label, "loop", lineno=statement.lineno)
        for source in incoming:
            self._add_edge(source, loop)

        body_entry = self._new_node("Loop Body", "branch", lineno=statement.lineno)
        self._add_edge(loop, body_entry, label="Iterate")

        body_exits = (
            self._walk_statements(statement.body, [body_entry])
            if statement.body
            else [body_entry]
        )
        for source in body_exits:
            self._add_edge(source, loop, label="Next")

        after_loop = self._new_node("After Loop", "merge", lineno=statement.lineno)
        self._add_edge(loop, after_loop, label="Exit")

        return [after_loop]

    def _statement_label(self, statement: ast.stmt) -> str:
        if isinstance(statement, ast.Assign):
            if isinstance(statement.value, ast.Call):  # simplify calls
                return self._call_label(statement.value)
            return "Assign"

        if isinstance(statement, ast.AnnAssign):
            if isinstance(statement.value, ast.Call):
                return self._call_label(statement.value)
            return "AnnAssign"

        if isinstance(statement, ast.AugAssign):
            return "AugAssign"

        if isinstance(statement, ast.Expr):
            if isinstance(statement.value, ast.Call):
                return self._call_label(statement.value)
            return self._expr_label(statement.value)

        if isinstance(statement, ast.Pass):
            return "Pass"

        try:
            return ast.unparse(statement)
        except Exception:
            return type(statement).__name__

    def _expr_label(self, expr: ast.AST) -> str:
        if isinstance(expr, ast.Call):
            return self._call_label(expr)

        try:
            return ast.unparse(expr)
        except Exception:
            return type(expr).__name__

    def _call_label(self, call: ast.Call) -> str:
        callee = self._callable_name(call.func)
        return f"{callee}(...)"

    def _callable_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parts: list[str] = []
            current: ast.AST = node

            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            if isinstance(current, ast.Name):
                parts.append(current.id)

            return ".".join(reversed(parts))

        try:
            return ast.unparse(node)
        except Exception:
            return type(node).__name__

    def _new_node(self, label: str, kind: str, *, lineno: int | None = None) -> str:
        self._counter += 1
        node_id = f"n{self._counter}"
        self.nodes.append(
            ControlFlowNode(
                id=node_id,
                label=label,
                kind=kind,
                lineno=lineno,
            )
        )
        return node_id

    def _add_edge(self, source: str, target: str, *, label: str | None = None) -> None:
        self.edges.append(
            Edge(
                source=source,
                target=target,
                kind="control_flow",
                label=label,
            )
        )

    def _node_kind(self, node_id: str) -> str:
        for node in self.nodes:
            if node.id == node_id:
                return node.kind
        raise KeyError(f"Unknown control-flow node id: {node_id}")
