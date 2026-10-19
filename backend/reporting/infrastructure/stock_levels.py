from dataclasses import dataclass

from inventory.infrastructure.models import StockItemModel
from reporting.infrastructure.directories import CatalogDirectory


@dataclass(frozen=True)
class StockLevels:
    low: int
    out: int

    @classmethod
    def load(cls) -> "StockLevels":
        products = CatalogDirectory.load().products
        low = 0
        out = 0
        for item in StockItemModel.objects.all():
            if item.quantity_on_hand == 0:
                out += 1
            product = products.get(item.product_id)
            if (
                product
                and product.minimum_stock_level > 0
                and item.quantity_on_hand <= product.minimum_stock_level
            ):
                low += 1
        return cls(low=low, out=out)
