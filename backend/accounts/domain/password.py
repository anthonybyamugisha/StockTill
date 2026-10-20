from abc import ABC, abstractmethod

from accounts.domain.errors import WeakPasswordError

MIN_PASSWORD_LENGTH = 8


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, raw_password: str) -> str:
        pass

    @abstractmethod
    def verify(self, raw_password: str, hashed: str) -> bool:
        pass


def validate_password_strength(raw_password: str) -> None:
    if len(raw_password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    has_letter = any(character.isalpha() for character in raw_password)
    has_digit = any(character.isdigit() for character in raw_password)
    if not has_letter or not has_digit:
        raise WeakPasswordError("Password must contain at least one letter and one number")
