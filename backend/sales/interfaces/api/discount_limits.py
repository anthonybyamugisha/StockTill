from decimal import Decimal

from accounts.domain.entities import Role
from settings.infrastructure.repository import DjangoSettingsRepository


def cashier_discount_limit(user) -> Decimal | None:
    if getattr(user, "role", None) != Role.CASHIER.value:
        return None
    limit = DjangoSettingsRepository().get().cashier_discount_limit
    return Decimal(str(limit))
