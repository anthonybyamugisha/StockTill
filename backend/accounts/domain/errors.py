from shared.domain.errors import DomainError, InvalidCredentialsError


class InvalidCurrentPasswordError(DomainError):
    pass


__all__ = ["DomainError", "InvalidCredentialsError", "InvalidCurrentPasswordError"]
