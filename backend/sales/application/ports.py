from abc import ABC, abstractmethod
from uuid import UUID

from shared.domain.money import Money


class InventoryPort(ABC):
    @abstractmethod
    def deduct_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        pass

    @abstractmethod
    def restore_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        pass

    @abstractmethod
    def get_available_stock(self, product_id: UUID) -> int:
        pass


class CatalogPort(ABC):
    @abstractmethod
    def get_product_price(self, product_id: UUID) -> Money | None:
        pass

    @abstractmethod
    def get_product_cost(self, product_id: UUID) -> Money | None:
        pass


class ReceiptNumberPort(ABC):
    @abstractmethod
    def generate(self) -> str:
        pass
