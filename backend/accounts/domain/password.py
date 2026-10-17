from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, raw_password: str) -> str:
        pass

    @abstractmethod
    def verify(self, raw_password: str, hashed: str) -> bool:
        pass
