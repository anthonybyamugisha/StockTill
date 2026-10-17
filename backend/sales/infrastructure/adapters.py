from uuid import UUID

from inventory.application.use_cases import AdjustStockUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.repository import DjangoStockItemRepository, DjangoStockMovementRepository
from sales.application.ports import InventoryPort
from shared.domain.money import Money


class InventoryAdapter(InventoryPort):
    def __init__(self):
        self._use_case = AdjustStockUseCase(
            DjangoStockItemRepository(), DjangoStockMovementRepository()
        )

    def deduct_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        self._use_case.execute(
            AdjustStockCommand(
                product_id=product_id,
                quantity=-quantity,
                movement_type=MovementType.SALE,
                reason="Sale",
                reference=reference,
            )
        )

    def restore_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        self._use_case.execute(
            AdjustStockCommand(
                product_id=product_id,
                quantity=quantity,
                movement_type=MovementType.REFUND_RETURN,
                reason="Refund return",
                reference=reference,
            )
        )

    def get_available_stock(self, product_id: UUID) -> int:
        repo = DjangoStockItemRepository()
        item = repo.get_by_product(product_id)
        return item.available_quantity if item else 0
