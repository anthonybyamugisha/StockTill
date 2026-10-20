from uuid import UUID

from inventory.application.commands import AdjustStockCommand
from inventory.application.ports import ProductInfoPort
from inventory.domain.entities import MovementType, StockItem, StockMovement
from inventory.domain.errors import InsufficientStockError
from inventory.domain.repository import StockItemRepository, StockMovementRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock
from shared.domain.money import Money


class AdjustStockUseCase:
    def __init__(
        self,
        stock_item_repository: StockItemRepository,
        movement_repository: StockMovementRepository,
        product_info_port: ProductInfoPort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._item_repo = stock_item_repository
        self._movement_repo = movement_repository
        self._product_info = product_info_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: AdjustStockCommand) -> StockMovement:
        item = self._item_repo.get_by_product(command.product_id)
        if item is None:
            item = StockItem(product_id=command.product_id)
        previous_quantity = item.quantity_on_hand

        qty = abs(command.quantity)

        if command.movement_type.reduces_stock:
            if item.available_quantity < qty:
                raise InsufficientStockError(
                    f"Insufficient stock for product {command.product_id}. "
                    f"Available: {item.available_quantity}, Requested: {qty}"
                )
            item.quantity_on_hand -= qty
        else:
            item.quantity_on_hand += qty

        movement = StockMovement(
            product_id=command.product_id,
            quantity=command.quantity if command.quantity > 0 else -qty,
            movement_type=command.movement_type,
            reason=command.reason,
            reference=command.reference,
            unit_cost=command.unit_cost or Money.zero(),
            user_id=command.user_id,
            timestamp=self._clock.now(),
            notes=command.notes,
        )

        self._movement_repo.save(movement)
        item.last_movement_id = movement.id
        self._item_repo.save(item)
        self._audit.record(
            user_id=command.user_id,
            action="stock.opening"
            if movement.movement_type == MovementType.OPENING
            else "stock.adjusted",
            entity_type="stock_item",
            entity_id=str(command.product_id),
            before={"quantity_on_hand": previous_quantity},
            after={
                "quantity_on_hand": item.quantity_on_hand,
                "movement_type": movement.movement_type.value,
                "quantity": movement.quantity,
                "reason": command.reason,
                "reference": command.reference,
            },
        )
        return movement


class RebuildStockCacheUseCase:
    def __init__(
        self,
        stock_item_repository: StockItemRepository,
        movement_repository: StockMovementRepository,
    ):
        self._item_repo = stock_item_repository
        self._movement_repo = movement_repository

    def execute(self) -> int:
        movements = self._movement_repo.list_all()
        items: dict[UUID, StockItem] = {}
        for m in movements:
            if m.product_id not in items:
                items[m.product_id] = StockItem(product_id=m.product_id)
            if m.movement_type.reduces_stock:
                items[m.product_id].quantity_on_hand -= abs(m.quantity)
            else:
                items[m.product_id].quantity_on_hand += abs(m.quantity)
            items[m.product_id].last_movement_id = m.id

        count = 0
        for item in items.values():
            self._item_repo.save(item)
            count += 1
        return count
