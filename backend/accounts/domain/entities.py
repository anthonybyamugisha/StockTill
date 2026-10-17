from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from shared.domain.base import Entity


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"


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
