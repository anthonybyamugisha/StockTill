from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from accounts.domain.password import PasswordHasher
from shared.domain.base import Entity


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"


LOCKOUT_DURATION_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5


@dataclass(eq=False)
class User(Entity):
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: Role = Role.CASHIER
    is_active: bool = True
    last_login: datetime | None = None
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    must_change_password: bool = False
    password_hash: str = field(default="", repr=False)

    def set_password(self, raw_password: str, hasher: PasswordHasher) -> None:
        self.password_hash = hasher.hash(raw_password)

    def check_password(self, raw_password: str, hasher: PasswordHasher) -> bool:
        return hasher.verify(raw_password, self.password_hash)

    def register_failed_login(self, max_attempts: int = MAX_FAILED_ATTEMPTS) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    def register_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.now(UTC)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until
