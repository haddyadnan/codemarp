class codemarpError(Exception):
    pass


class ParseError(codemarpError):
    pass


class ResolutionError(codemarpError):
    pass


class TraceError(ResolutionError):
    pass


class ModuleModeError(ResolutionError):
    pass


class FocusFormatError(codemarpError):
    pass
