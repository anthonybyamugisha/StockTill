from decimal import Decimal
from uuid import uuid4

from purchasing.application.commands import PurchaseOrderLineInput
from purchasing.application.order_lines import build_order_line, build_order_lines
from shared.domain.money import Money


def _input(product_name: str = "Sugar 1kg") -> PurchaseOrderLineInput:
    return PurchaseOrderLineInput(
        product_id=uuid4(),
        product_name=product_name,
        quantity=12,
        unit_cost=Money(Decimal("1000.00")),
    )


def test_copies_every_field_onto_the_order_line():
    source = _input()

    line = build_order_line(source)

    assert line.product_id == source.product_id
    assert line.product_name == "Sugar 1kg"
    assert line.quantity == 12
    assert line.unit_cost.amount == Decimal("1000.00")


def test_keeps_the_input_order():
    lines = build_order_lines([_input("A"), _input("B")])

    assert [line.product_name for line in lines] == ["A", "B"]
