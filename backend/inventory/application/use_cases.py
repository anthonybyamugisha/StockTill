from inventory.application.commands import AdjustStockCommand
from inventory.domain.entities import MovementType, StockItem, StockMovement
from inventory.domain.errors import InsufficientStockError
from inventory.domain.repository import StockItemRepository, StockMovementRepository


class AdjustStockUseCase:
    def __init__(
        self,
        stock_item_repository: StockItemRepository,
        movement_repository: StockMovementRepository,
    ):
        self._item_repo = stock_item_repository
        self._movement_repo = movement_repository

    def execute(self, command: AdjustStockCommand) -> StockMovement:
        item = self._item_repo.get_by_product(command.product_id)
        if item is None:
            item = StockItem(product_id=command.product_id)

        if command.movement_type in (
            MovementType.SALE,
            MovementType.ADJUSTMENT_OUT,
            MovementType.WRITE_OFF,
        ):
            if item.available_quantity < abs(command.quantity):
                raise InsufficientStockError(
                    f"Insufficient stock for product {command.product_id}"
                )
            item.quantity_on_hand -= abs(command.quantity)
        else:
            item.quantity_on_hand += abs(command.quantity)

        movement = StockMovement(
            product_id=command.product_id,
            quantity=command.quantity,
            movement_type=command.movement_type,
            reason=command.reason,
            reference=command.reference,
            unit_cost=command.unit_cost,
            user_id=command.user_id,
        )

        self._movement_repo.save(movement)
        self._item_repo.save(item)
        return movement
