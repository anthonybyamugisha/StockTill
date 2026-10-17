from abc import ABC, abstractmethod
from uuid import UUID


class ProductInfoPort(ABC):
    @abstractmethod
    def get_product_name(self, product_id: UUID) -> str | None:
        pass

    @abstractmethod
    def get_minimum_stock_level(self, product_id: UUID) -> int:
        pass
