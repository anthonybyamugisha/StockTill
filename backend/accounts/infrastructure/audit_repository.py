from uuid import UUID

from accounts.infrastructure.models import AuditLogModel
from shared.infrastructure.audit import AuditEntry, AuditRepository


class DjangoAuditRepository(AuditRepository):
    def save(self, entry: AuditEntry) -> None:
        AuditLogModel.objects.create(
            id=entry.id,
            user_id=entry.user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            before=entry.before,
            after=entry.after,
        )

    def list_entries(
        self,
        *,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[AuditEntry]:
        qs = AuditLogModel.objects.all()
        if user_id is not None:
            qs = qs.filter(user_id=user_id)
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if action:
            qs = qs.filter(action=action)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
        return [
            AuditEntry(
                id=m.id,
                user_id=m.user_id,
                action=m.action,
                entity_type=m.entity_type,
                entity_id=m.entity_id,
                before=m.before,
                after=m.after,
                timestamp=m.timestamp,
            )
            for m in qs.order_by("-timestamp")
        ]
