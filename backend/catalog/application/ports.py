from abc import ABC, abstractmethod
from uuid import UUID

from shared.domain.money import Money


class OpeningStockPort(ABC):
    """Records the initial stock quantity when a product is first created."""

    @abstractmethod
    def record_opening_stock(
        self, *, product_id: UUID, quantity: int, unit_cost: Money, user_id: UUID | None
    ) -> None:
        pass
