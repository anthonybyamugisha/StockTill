from inventory.application.commands import ReleaseStockCommand, ReserveStockCommand
from inventory.domain.entities import StockItem
from inventory.domain.errors import InsufficientStockError
from inventory.domain.repository import StockItemRepository


class ReserveStockUseCase:
    def __init__(self, stock_item_repository: StockItemRepository):
        self._item_repo = stock_item_repository

    def execute(self, command: ReserveStockCommand) -> StockItem:
        item = self._item_repo.get_by_product(command.product_id)
        if item is None:
            raise InsufficientStockError(f"Product {command.product_id} has no stock record")

        if item.available_quantity < command.quantity:
            raise InsufficientStockError(
                f"Cannot reserve {command.quantity} of product {command.product_id}. "
                f"Available: {item.available_quantity}"
            )

        item.reserved_quantity += command.quantity
        self._item_repo.save(item)
        return item


class ReleaseStockUseCase:
    def __init__(self, stock_item_repository: StockItemRepository):
        self._item_repo = stock_item_repository

    def execute(self, command: ReleaseStockCommand) -> StockItem:
        item = self._item_repo.get_by_product(command.product_id)
        if item is None:
            return StockItem(product_id=command.product_id)

        item.reserved_quantity = max(0, item.reserved_quantity - command.quantity)
        self._item_repo.save(item)
        return item
