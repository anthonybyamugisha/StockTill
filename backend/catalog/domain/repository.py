from abc import ABC, abstractmethod
from uuid import UUID

from catalog.domain.entities import Category, Product


class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Product | None:
        pass

    @abstractmethod
    def get_by_sku(self, sku: str) -> Product | None:
        pass

    @abstractmethod
    def get_by_barcode(self, barcode: str) -> Product | None:
        pass

    @abstractmethod
    def search(self, query: str, *, active_only: bool = True) -> list[Product]:
        pass

    @abstractmethod
    def list_products(self, *, active_only: bool = True) -> list[Product]:
        pass

    @abstractmethod
    def save(self, product: Product) -> None:
        pass


class CategoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, category_id: UUID) -> Category | None:
        pass

    @abstractmethod
    def list_categories(self) -> list[Category]:
        pass

    @abstractmethod
    def save(self, category: Category) -> None:
        pass
