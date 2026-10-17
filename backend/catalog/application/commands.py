from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from shared.domain.money import Money


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    description: str
    sku: str
    barcode: str | None
    category_id: UUID | None
    buying_cost: Money
    selling_price: Money
    minimum_stock_level: int
    image_url: str | None = None


@dataclass(frozen=True)
class UpdateProductCommand:
    product_id: UUID
    name: str | None = None
    description: str | None = None
    barcode: str | None = None
    category_id: UUID | None = None
    buying_cost: Money | None = None
    selling_price: Money | None = None
    minimum_stock_level: int | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class DeactivateProductCommand:
    product_id: UUID
