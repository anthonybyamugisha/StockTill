from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from reporting.application.queries import LowStockItem


class DjangoLowStockQuery:
    def execute(self) -> list[LowStockItem]:
        products = {
            product.id: product
            for product in ProductModel.objects.filter(minimum_stock_level__gt=0)
        }
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
