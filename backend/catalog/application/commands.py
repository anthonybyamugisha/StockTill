from dataclasses import dataclass
from uuid import UUID

from shared.domain.money import Money


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    sku: str
    selling_price: Money
    buying_cost: Money
    description: str = ""
    barcode: str | None = None
    category_id: UUID | None = None
    minimum_stock_level: int = 0
    image_url: str | None = None
    opening_stock: int = 0
    user_id: UUID | None = None


@dataclass(frozen=True)
class UpdateProductCommand:
    product_id: UUID
    name: str | None = None
    sku: str | None = None
    description: str | None = None
    barcode: str | None = None
    category_id: UUID | None = None
    selling_price: Money | None = None
    buying_cost: Money | None = None
    minimum_stock_level: int | None = None
    image_url: str | None = None
    is_active: bool | None = None
    user_id: UUID | None = None


@dataclass(frozen=True)
class DeactivateProductCommand:
    product_id: UUID
    user_id: UUID | None = None


@dataclass(frozen=True)
class CreateCategoryCommand:
    name: str
    description: str = ""
    parent_id: UUID | None = None
    user_id: UUID | None = None


@dataclass(frozen=True)
class UpdateCategoryCommand:
    category_id: UUID
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    parent_set: bool = False
    is_active: bool | None = None
    user_id: UUID | None = None


@dataclass(frozen=True)
class DeactivateCategoryCommand:
    category_id: UUID
    user_id: UUID | None = None
