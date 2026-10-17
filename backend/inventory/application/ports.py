from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProductLabel:
    name: str
    sku: str


class ProductInfoPort(ABC):
    @abstractmethod
    def get_product_name(self, product_id: UUID) -> str | None:
        pass

    @abstractmethod
    def get_minimum_stock_level(self, product_id: UUID) -> int:
        pass

    @abstractmethod
    def get_product_labels(self, product_ids: Iterable[UUID]) -> dict[UUID, ProductLabel]:
        pass
