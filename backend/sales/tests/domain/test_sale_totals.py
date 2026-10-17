from decimal import Decimal
from uuid import uuid4

from sales.domain.entities import Sale, SaleLine
from shared.domain.money import Money


def _line(quantity: int, price: str, cost: str) -> SaleLine:
    return SaleLine(
        product_id=uuid4(),
        product_name="Item",
        quantity=quantity,
        unit_price=Money(Decimal(price)),
        unit_cost=Money(Decimal(cost)),
    )


def test_sale_totals_aggregate_lines():
    sale = Sale(
        lines=[
            _line(2, "25000.00", "20000.00"),
            _line(1, "3000.00", "2000.00"),
        ]
    )

    assert sale.subtotal == Money(Decimal("53000.00"))
    assert sale.total == Money(Decimal("53000.00"))
    assert sale.cost_total == Money(Decimal("42000.00"))
    assert sale.gross_profit == Money(Decimal("11000.00"))


def test_sale_with_no_lines_totals_to_zero():
    sale = Sale()

    assert sale.subtotal == Money.zero()
    assert sale.total == Money.zero()
    assert sale.gross_profit == Money.zero()
