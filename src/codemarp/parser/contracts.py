from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------- Imports ----------


@dataclass(frozen=True)
class ImportFact:
    raw_module: str | None
    imported_name: str | None
    alias: str | None
    is_from_import: bool
    relative_level: int
    lineno: int


# ---------- Functions ----------


@dataclass(frozen=True)
class FunctionFact:
    function_id: str
    module_id: str
    qualname: str
    short_name: str
    class_name: str | None
    lineno: int
    end_lineno: int | None
    is_method: bool
    is_async: bool


# ---------- Calls ----------


@dataclass(frozen=True)
class CallFact:
    caller_id: str
    raw: str
    leaf_name: str
    receiver: str | None
    kind: str  # "bare", "attribute", "super", "unknown"
    lineno: int


# ---------- Control Flow ----------


@dataclass(frozen=True)
class ControlFlowRootFact:
    function_id: str
    syntax_ref: Any  # AST node for now (transitional)


# ---------- Module ----------


@dataclass(frozen=True)
class ParsedModule:
    module_id: str
    file_path: Path
    language: str
    imports: list[ImportFact]
    functions: list[FunctionFact]
    calls: list[CallFact]
    control_flow_roots: list[ControlFlowRootFact]
