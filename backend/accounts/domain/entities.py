from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID

from shared.domain.base import Entity


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"


LOCKOUT_DURATION_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5


@dataclass
class User(Entity):
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: Role = Role.CASHIER
    is_active: bool = True
    last_login: datetime | None = None
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    password_hash: str = field(default="", repr=False)

    def set_password(self, raw_password: str, hasher) -> None:
        self.password_hash = hasher.hash(raw_password)

    def check_password(self, raw_password: str, hasher) -> bool:
        return hasher.verify(raw_password, self.password_hash)

    def register_failed_login(self, max_attempts: int = MAX_FAILED_ATTEMPTS) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    def register_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.now(timezone.utc)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
