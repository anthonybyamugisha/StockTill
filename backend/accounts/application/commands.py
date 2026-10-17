from dataclasses import dataclass
from uuid import UUID

from accounts.domain.entities import Role


@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    first_name: str
    last_name: str
    role: Role
    password: str


@dataclass(frozen=True)
class UpdateUserCommand:
    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    role: Role | None = None


@dataclass(frozen=True)
class DeactivateUserCommand:
    user_id: UUID
