from abc import ABC, abstractmethod
from uuid import UUID

from inventory.domain.entities import StockItem, StockMovement


class StockMovementRepository(ABC):
    @abstractmethod
    def save(self, movement: StockMovement) -> None:
        pass

    @abstractmethod
    def get_by_id(self, movement_id: UUID) -> StockMovement | None:
        pass

    @abstractmethod
    def list_by_product(self, product_id: UUID) -> list[StockMovement]:
        pass

    @abstractmethod
    def list_all(
        self,
        *,
        movement_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[StockMovement]:
        pass


class StockItemRepository(ABC):
    @abstractmethod
    def get_by_product(self, product_id: UUID) -> StockItem | None:
        pass

    @abstractmethod
    def save(self, item: StockItem) -> None:
        pass

    @abstractmethod
    def list_all(self) -> list[StockItem]:
        pass

    @abstractmethod
    def list_low_stock(self) -> list[StockItem]:
        pass

    @abstractmethod
    def list_out_of_stock(self) -> list[StockItem]:
        pass

    @abstractmethod
    def get_valuation(self) -> dict[str, object]:
        pass
