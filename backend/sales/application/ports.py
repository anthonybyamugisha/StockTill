from abc import ABC, abstractmethod
from uuid import UUID


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
    def get_product(self, product_id: UUID) -> dict[str, object] | None:
        pass


class ReceiptNumberPort(ABC):
    @abstractmethod
    def generate(self) -> str:
        pass


class IdempotencyPort(ABC):
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def store(self, key: str, sale_id: UUID) -> None:
        pass


class ShiftPort(ABC):
    @abstractmethod
    def open_shift_id(self, cashier_id: UUID) -> UUID | None:
        pass
