from enum import StrEnum


class ResolutionReason(StrEnum):
    SAME_MODULE = "same_module"
    IMPORTED_SYMBOL = "imported_symbol"
    IMPORTED_MODULE = "imported_module"
    UNIQUE_GLOBAL = "unique_global"
