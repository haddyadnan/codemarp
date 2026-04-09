class CodemapError(Exception):
    pass


class ParseError(CodemapError):
    pass


class ResolutionError(CodemapError):
    pass


class TraceError(ResolutionError):
    pass


class ModuleViewError(ResolutionError):
    pass
