from datetime import date, timedelta
from decimal import Decimal

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import (
    InventoryReport,
    LowStockItem,
)
from reporting.infrastructure.directories import CashierDirectory, CatalogDirectory
from reporting.infrastructure.stock_levels import StockLevels
from shared.domain.money import Money

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

    def get_inventory_report(self) -> InventoryReport:
        from inventory.infrastructure.models import StockItemModel

        products = self._products_by_id()
        total_value = Money.zero()
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product is None:
                continue
            total_value = total_value.add(
                Money(product.buying_cost).multiply(Decimal(item.quantity_on_hand))
            )

        low_stock, out_of_stock = self._stock_counts()

        return InventoryReport(
            total_products=ProductModel.objects.filter(is_active=True).count(),
            total_value=total_value.amount,
            low_stock_count=low_stock,
            out_of_stock_count=out_of_stock,
        )

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
