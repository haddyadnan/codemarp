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
        self,
        statement: ast.stmt,
        incoming: list[str],
    ) -> list[str]:
        if isinstance(statement, ast.If):
            return self._handle_if(statement, incoming)

        if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            return self._handle_loop(statement, incoming)

        if isinstance(statement, ast.Try):
            node = self._new_node("Try/Except", "statement", lineno=statement.lineno)
            for source in incoming:
                self._add_edge(source, node)
            return [node]

        if isinstance(statement, ast.Return):
            node = self._new_node("Return", "terminal", lineno=statement.lineno)
            for source in incoming:
                self._add_edge(source, node)
            return [node]

        if isinstance(statement, ast.Raise):
            node = self._new_node("Raise", "terminal", lineno=statement.lineno)
            for source in incoming:
                self._add_edge(source, node)
            return [node]

        label = self._statement_label(statement)
        node = self._new_node(label, "statement", lineno=statement.lineno)
        for source in incoming:
            self._add_edge(source, node)
        return [node]

    def _handle_if(self, statement: ast.If, incoming: list[str]) -> list[str]:
        condition = self._new_node(
            self._expr_label(statement.test),
            "decision",
            lineno=statement.lineno,
        )
        for source in incoming:
            self._add_edge(source, condition)

        then_entry = self._new_node("Then", "branch", lineno=statement.lineno)
        else_entry = self._new_node("Else", "branch", lineno=statement.lineno)

        self._add_edge(condition, then_entry, label="True")
        self._add_edge(condition, else_entry, label="False")

        then_exits = (
            self._walk_statements(statement.body, [then_entry])
            if statement.body
            else [then_entry]
        )
        else_exits = (
            self._walk_statements(statement.orelse, [else_entry])
            if statement.orelse
            else [else_entry]
        )

        non_terminals = [
            node_id
            for node_id in then_exits + else_exits
            if self._node_kind(node_id) != "terminal"
        ]
        if non_terminals:
            merge = self._new_node("Merge", "merge", lineno=statement.lineno)
            for source in non_terminals:
                self._add_edge(source, merge)
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
            return "Assign"
        if isinstance(statement, ast.AnnAssign):
            return "AnnAssign"
        if isinstance(statement, ast.AugAssign):
            return "AugAssign"
        if isinstance(statement, ast.Expr):
            return self._expr_label(statement.value)
        if isinstance(statement, ast.Pass):
            return "Pass"
        try:
            return ast.unparse(statement)
        except Exception:
            return type(statement).__name__

    def _expr_label(self, expr: ast.AST) -> str:
        try:
            return ast.unparse(expr)
        except Exception:
            return type(expr).__name__

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
