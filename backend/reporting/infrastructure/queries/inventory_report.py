from decimal import Decimal

from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from reporting.application.queries import InventoryReport
from reporting.infrastructure.directories import CatalogDirectory
from reporting.infrastructure.stock_levels import StockLevels
from shared.domain.money import Money


class DjangoInventoryReportQuery:
    def execute(self) -> InventoryReport:
        products = CatalogDirectory.load().products
        total_value = Money.zero()
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product is None:
                continue
            total_value = total_value.add(
                Money(product.buying_cost).multiply(Decimal(item.quantity_on_hand))
            )

        levels = StockLevels.load()

        return InventoryReport(
            total_products=ProductModel.objects.filter(is_active=True).count(),
            total_value=total_value.amount,
            low_stock_count=levels.low,
            out_of_stock_count=levels.out,
        )
