from datetime import date, timedelta

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import (
    LowStockItem,
)
from reporting.infrastructure.directories import CashierDirectory, CatalogDirectory
from reporting.infrastructure.stock_levels import StockLevels

_MAX_FILLED_DAYS = 366


def _date_range(date_from: date, date_to: date) -> list[date]:
    return [date_from + timedelta(days=offset) for offset in range((date_to - date_from).days + 1)]


class SalesQueryBuilder:
    def _cashier_names(self) -> dict:
        return CashierDirectory.load().labels

    def _products_by_id(self) -> dict:
        return CatalogDirectory.load().products

    def _stock_counts(self) -> tuple[int, int]:
        levels = StockLevels.load()
        return levels.low, levels.out

    def get_low_stock_items(self) -> list[LowStockItem]:
        from inventory.infrastructure.models import StockItemModel

        products = {p.id: p for p in ProductModel.objects.filter(minimum_stock_level__gt=0)}
        items = []
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product and item.quantity_on_hand <= product.minimum_stock_level:
                items.append(
                    LowStockItem(
                        product_id=item.product_id,
                        product_name=product.name,
                        sku=product.sku,
                        quantity_on_hand=item.quantity_on_hand,
                        minimum_level=product.minimum_stock_level,
                    )
                )
        return items
