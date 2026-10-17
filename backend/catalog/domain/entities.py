from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from shared.domain.base import Entity
from shared.domain.money import Money

if TYPE_CHECKING:
    pass


@dataclass(eq=False)
class Category(Entity):
    name: str = ""
    description: str = ""
    parent_id: UUID | None = None
    is_active: bool = True


@dataclass(eq=False)
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

    @property
    def profit_margin(self) -> Money:
        return self.selling_price.subtract(self.buying_cost)

    def update_price(self, new_price: Money, user_id: UUID) -> dict[str, str]:
        old_price = self.selling_price
        self.selling_price = new_price
        return {
            "product_id": str(self.id),
            "field": "selling_price",
            "old_value": str(old_price.amount),
            "new_value": str(new_price.amount),
            "user_id": str(user_id),
        }

    def update_cost(self, new_cost: Money, user_id: UUID) -> dict[str, str]:
        old_cost = self.buying_cost
        self.buying_cost = new_cost
        return {
            "product_id": str(self.id),
            "field": "buying_cost",
            "old_value": str(old_cost.amount),
            "new_value": str(new_cost.amount),
            "user_id": str(user_id),
        }
