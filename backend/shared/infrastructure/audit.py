from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


class AuditEntry:
    def __init__(
        self,
        id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.before = before
        self.after = after
        self.timestamp = timestamp or datetime.now(UTC)


class AuditRepository(ABC):
    @abstractmethod
    def save(self, entry: AuditEntry) -> None:
        pass

    @abstractmethod
    def list_entries(
        self,
        *,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[AuditEntry]:
        pass


class AuditRecorder:
    def __init__(self, repository: AuditRepository):
        self._repository = repository

    def record(
        self,
        *,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None:
        from uuid import uuid4

        self._repository.save(
            AuditEntry(
                id=uuid4(),
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=after,
            )
        )


def build_audit_recorder() -> AuditRecorder:
    from accounts.infrastructure.audit_repository import DjangoAuditRepository

    return AuditRecorder(DjangoAuditRepository())
