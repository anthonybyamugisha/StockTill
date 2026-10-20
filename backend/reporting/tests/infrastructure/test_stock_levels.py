import pytest

from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from reporting.infrastructure.stock_levels import StockLevels


def _product(name: str, sku: str, minimum: int) -> ProductModel:
    return ProductModel.objects.create(
        name=name,
        sku=sku,
        buying_cost="1000.00",
        selling_price="1500.00",
        minimum_stock_level=minimum,
    )


@pytest.mark.django_db
def test_counts_out_of_stock_and_low_stock_separately():
    out = _product("Out", "OUT-1", 5)
    low = _product("Low", "LOW-1", 10)
    healthy = _product("Healthy", "OK-1", 3)
    StockItemModel.objects.create(product_id=out.id, quantity_on_hand=0)
    StockItemModel.objects.create(product_id=low.id, quantity_on_hand=10)
    StockItemModel.objects.create(product_id=healthy.id, quantity_on_hand=11)

    levels = StockLevels.load()

    assert (levels.low, levels.out) == (2, 1)


@pytest.mark.django_db
def test_ignores_products_without_a_minimum_level():
    product = _product("No minimum", "NOMIN-1", 0)
    StockItemModel.objects.create(product_id=product.id, quantity_on_hand=0)

    levels = StockLevels.load()

    assert (levels.low, levels.out) == (0, 1)
