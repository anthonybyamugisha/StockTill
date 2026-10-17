from shared.domain.errors import DomainError


class ShiftError(DomainError):
    """Base class for shift domain errors."""


class ShiftAlreadyOpenError(ShiftError):
    pass


class ShiftAlreadyClosedError(ShiftError):
    pass


class NoOpenShiftError(ShiftError):
    pass
