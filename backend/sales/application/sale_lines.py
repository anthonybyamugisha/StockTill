from collections.abc import Iterable

from sales.application.commands import LineItem
from sales.application.ports import CatalogPort
from sales.domain.entities import SaleLine
from sales.domain.services import calculate_discount


def build_sale_line(item: LineItem, catalog: CatalogPort) -> SaleLine:
    discount = None
    if item.discount_type and item.discount_value:
        discount = calculate_discount(
            item.unit_price, item.quantity, item.discount_type, item.discount_value
        )

    product_name = item.product_name
    if not product_name:
        product = catalog.get_product(item.product_id)
        if product is not None:
            product_name = str(product.get("name") or "")

    return SaleLine(
        product_id=item.product_id,
        product_name=product_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        unit_cost=item.unit_cost,
        discount=discount,
    )


def build_sale_lines(items: Iterable[LineItem], catalog: CatalogPort) -> list[SaleLine]:
    return [build_sale_line(item, catalog) for item in items]
