from collections.abc import Iterable

from purchasing.application.commands import PurchaseOrderLineInput
from purchasing.domain.entities import PurchaseOrderLine


def build_order_line(line: PurchaseOrderLineInput) -> PurchaseOrderLine:
    return PurchaseOrderLine(
        product_id=line.product_id,
        product_name=line.product_name,
        quantity=line.quantity,
        unit_cost=line.unit_cost,
    )


def build_order_lines(lines: Iterable[PurchaseOrderLineInput]) -> list[PurchaseOrderLine]:
    return [build_order_line(line) for line in lines]
