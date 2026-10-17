from typing import Any
from uuid import UUID

from settings.domain.repository import SettingsRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.settings import BusinessSettings


def _snapshot(settings: BusinessSettings) -> dict[str, Any]:
    return {
        "business_name": settings.business_name,
        "address": settings.address,
        "phone": settings.phone,
        "email": settings.email,
        "currency": settings.currency,
        "receipt_header": settings.receipt_header,
        "receipt_footer": settings.receipt_footer,
        "cashier_discount_limit": float(settings.cashier_discount_limit),
        "tax_rate": float(settings.tax_rate),
        "logo_url": settings.logo_url,
    }


class GetSettingsUseCase:
    def __init__(self, repository: SettingsRepository):
        self._repo = repository

    def execute(self) -> BusinessSettings:
        return self._repo.get()


class UpdateSettingsUseCase:
    def __init__(self, repository: SettingsRepository, audit: AuditPort | None = None):
        self._repo = repository
        self._audit = audit or NullAuditPort()

    def execute(self, settings: BusinessSettings, actor_id: UUID | None = None) -> BusinessSettings:
        before = _snapshot(self._repo.get())
        self._repo.save(settings)
        after = _snapshot(settings)
        changed = {key: value for key, value in after.items() if value != before[key]}
        if changed:
            self._audit.record(
                user_id=actor_id,
                action="settings.updated",
                entity_type="settings",
                entity_id="main",
                before={key: before[key] for key in changed},
                after=changed,
            )
        return settings
