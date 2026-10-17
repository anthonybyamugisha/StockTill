from uuid import UUID

from catalog.application.ports import OpeningStockPort
from inventory.application.commands import AdjustStockCommand
from inventory.application.use_cases import AdjustStockUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.adapters import CatalogProductInfoAdapter
from inventory.infrastructure.repository import (
    DjangoStockItemRepository,
    DjangoStockMovementRepository,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money
from shared.infrastructure.audit import build_audit_recorder


class InventoryOpeningStockAdapter(OpeningStockPort):
    def record_opening_stock(
        self, *, product_id: UUID, quantity: int, unit_cost: Money, user_id: UUID | None
    ) -> None:
        use_case = AdjustStockUseCase(
            DjangoStockItemRepository(),
            DjangoStockMovementRepository(),
            CatalogProductInfoAdapter(),
            SystemClock(),
            build_audit_recorder(),
        )
        use_case.execute(
            AdjustStockCommand(
                product_id=product_id,
                quantity=quantity,
                movement_type=MovementType.OPENING,
                reason="Opening stock",
                user_id=user_id,
                unit_cost=unit_cost,
            )
        )
