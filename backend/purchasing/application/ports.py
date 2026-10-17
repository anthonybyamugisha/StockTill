from abc import ABC, abstractmethod
from uuid import UUID

from shared.domain.money import Money


class StockIntakePort(ABC):
    """Records stock received from a supplier into the inventory context."""

    @abstractmethod
    def receive_stock(
        self,
        *,
        product_id: UUID,
        quantity: int,
        unit_cost: Money,
        reference: str,
        user_id: UUID | None,
    ) -> None:
        pass
