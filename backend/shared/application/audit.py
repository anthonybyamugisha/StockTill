from typing import Any, Protocol
from uuid import UUID


class AuditPort(Protocol):
    def record(
        self,
        *,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None: ...


class NullAuditPort:
    def record(
        self,
        *,
        user_id: UUID | None = None,
        action: str = "",
        entity_type: str = "",
        entity_id: str = "",
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None:
        return None
