from typing import Any

from catalog.domain.entities import Product


def product_snapshot(product: Product) -> dict[str, Any]:
    return {
        "name": product.name,
        "sku": product.sku,
        "barcode": product.barcode,
        "category_id": str(product.category_id) if product.category_id else None,
        "buying_cost": str(product.buying_cost.amount),
        "selling_price": str(product.selling_price.amount),
        "minimum_stock_level": product.minimum_stock_level,
        "is_active": product.is_active,
    }
