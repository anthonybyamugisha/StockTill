from decimal import Decimal

import pytest

from purchasing.domain.entities import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
)
from purchasing.domain.errors import (
    EmptyPurchaseOrderError,
    InvalidPurchaseOrderStateError,
    InvalidSupplierError,
)
from shared.domain.money import Money


def money(value: str) -> Money:
    return Money(Decimal(value))


def line(quantity: int, unit_cost: str) -> PurchaseOrderLine:
    return PurchaseOrderLine(quantity=quantity, unit_cost=money(unit_cost))


def test_supplier_requires_a_name():
    with pytest.raises(InvalidSupplierError):
        Supplier(name="   ")


def test_purchase_order_total_is_the_sum_of_line_totals():
    order = PurchaseOrder(lines=[line(3, "2000.00"), line(2, "5000.00")])

    assert order.total.amount == money("16000.00").amount


def test_cannot_order_a_purchase_order_with_no_lines():
    order = PurchaseOrder()
    with pytest.raises(EmptyPurchaseOrderError):
        order.mark_ordered(at=None)  # type: ignore[arg-type]


def test_ordering_moves_a_draft_to_ordered():
    order = PurchaseOrder(lines=[line(1, "1000.00")])

    order.mark_ordered(at=None)  # type: ignore[arg-type]

    assert order.status == PurchaseOrderStatus.ORDERED


def test_cannot_order_twice():
    order = PurchaseOrder(lines=[line(1, "1000.00")])
    order.mark_ordered(at=None)  # type: ignore[arg-type]

    with pytest.raises(InvalidPurchaseOrderStateError):
        order.mark_ordered(at=None)  # type: ignore[arg-type]


def test_receiving_marks_the_order_received():
    order = PurchaseOrder(lines=[line(1, "1000.00")])
    order.mark_ordered(at=None)  # type: ignore[arg-type]

    order.receive(at=None)  # type: ignore[arg-type]

    assert order.is_received is True


def test_cannot_receive_a_cancelled_order():
    order = PurchaseOrder(lines=[line(1, "1000.00")])
    order.cancel("supplier out of stock")

    with pytest.raises(InvalidPurchaseOrderStateError):
        order.receive(at=None)  # type: ignore[arg-type]


def test_cannot_receive_twice():
    order = PurchaseOrder(lines=[line(1, "1000.00")])
    order.receive(at=None)  # type: ignore[arg-type]

    with pytest.raises(InvalidPurchaseOrderStateError):
        order.receive(at=None)  # type: ignore[arg-type]


def test_cannot_cancel_a_received_order():
    order = PurchaseOrder(lines=[line(1, "1000.00")])
    order.receive(at=None)  # type: ignore[arg-type]

    with pytest.raises(InvalidPurchaseOrderStateError):
        order.cancel("too late")
