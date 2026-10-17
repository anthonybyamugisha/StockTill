from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AuditEntry:
    id: UUID
    user_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    timestamp: datetime


class AuditRecorder:
    def __init__(self, repository):
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
        self._repository.save(
            AuditEntry(
                id=UUID(int=0),
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=after,
                timestamp=datetime.utcnow(),
            )
        )
