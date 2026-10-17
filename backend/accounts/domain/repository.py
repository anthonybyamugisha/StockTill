from abc import ABC, abstractmethod
from uuid import UUID

from accounts.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def list_users(self, *, active_only: bool = False) -> list[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def email_exists(self, email: str) -> bool:
        pass
