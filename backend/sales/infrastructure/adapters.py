from uuid import UUID

from catalog.infrastructure.models import ProductModel
from inventory.application.commands import AdjustStockCommand
from inventory.application.use_cases import AdjustStockUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.adapters import CatalogProductInfoAdapter
from inventory.infrastructure.repository import (
    DjangoStockItemRepository,
    DjangoStockMovementRepository,
)
from sales.application.ports import CatalogPort, InventoryPort
from shared.domain.clock import SystemClock


class InventoryAdapter(InventoryPort):
    def __init__(self):
        self._use_case = AdjustStockUseCase(
            DjangoStockItemRepository(),
            DjangoStockMovementRepository(),
            CatalogProductInfoAdapter(),
            SystemClock(),
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


class CatalogAdapter(CatalogPort):
    def get_product(self, product_id: UUID) -> dict | None:
        try:
            p = ProductModel.objects.get(id=product_id)
            return {
                "id": str(p.id),
                "name": p.name,
                "sku": p.sku,
                "selling_price": str(p.selling_price),
                "buying_cost": str(p.buying_cost),
                "is_active": p.is_active,
            }
        except ProductModel.DoesNotExist:
            return None
