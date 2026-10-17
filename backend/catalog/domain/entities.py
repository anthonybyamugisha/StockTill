from dataclasses import dataclass, field
from uuid import UUID

from shared.domain.base import Entity
from shared.domain.money import Money


@dataclass
class Category(Entity):
    name: str = ""
    description: str = ""


@dataclass
class Product(Entity):
    name: str = ""
    description: str = ""
    sku: str = ""
    barcode: str | None = None
    category_id: UUID | None = None
    buying_cost: Money = field(default_factory=Money.zero)
    selling_price: Money = field(default_factory=Money.zero)
    minimum_stock_level: int = 0
    image_url: str | None = None
    is_active: bool = True
