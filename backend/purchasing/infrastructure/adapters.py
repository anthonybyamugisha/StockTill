from uuid import UUID

from inventory.application.commands import AdjustStockCommand
from inventory.application.use_cases import AdjustStockUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.adapters import CatalogProductInfoAdapter
from inventory.infrastructure.repository import (
    DjangoStockItemRepository,
    DjangoStockMovementRepository,
)
from purchasing.application.ports import StockIntakePort
from shared.domain.clock import SystemClock
from shared.domain.money import Money


class InventoryStockIntakeAdapter(StockIntakePort):
    """Feeds received purchase-order lines into the inventory stock ledger."""

    def receive_stock(
        self,
        *,
        product_id: UUID,
        quantity: int,
        unit_cost: Money,
        reference: str,
        user_id: UUID | None,
    ) -> None:
        use_case = AdjustStockUseCase(
            DjangoStockItemRepository(),
            DjangoStockMovementRepository(),
            CatalogProductInfoAdapter(),
            SystemClock(),
        )
        use_case.execute(
            AdjustStockCommand(
                product_id=product_id,
                quantity=quantity,
                movement_type=MovementType.PURCHASE,
                reason="Purchase order received",
                reference=reference,
                unit_cost=unit_cost,
                user_id=user_id,
            )
        )
