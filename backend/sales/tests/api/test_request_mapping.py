from decimal import Decimal
from uuid import uuid4

from sales.domain.entities import DiscountType, PaymentMethod
from sales.interfaces.api.request_mapping import (
    to_complete_sale_command,
    to_line_item,
    to_payment_input,
    to_refund_sale_command,
    to_void_sale_command,
)


def _line(**overrides):
    values = {
        "product_id": uuid4(),
        "quantity": 2,
        "unit_price": Decimal("1500.00"),
        "unit_cost": Decimal("1000.00"),
        "product_name": "Sugar 1kg",
    }
    values.update(overrides)
    return values


def test_maps_a_line_with_a_percentage_discount():
    line = to_line_item(_line(discount_type="percentage", discount_value=Decimal("10")))

    assert line.unit_price.amount == Decimal("1500.00")
    assert line.discount_type == DiscountType.PERCENTAGE
    assert line.discount_value == Decimal("10")


def test_leaves_the_discount_empty_when_none_is_given():
    line = to_line_item(_line())

    assert line.discount_type is None
    assert line.discount_value is None
    assert line.product_name == "Sugar 1kg"


def test_maps_a_cash_payment_with_its_tendered_amount():
    payment = to_payment_input(
        {"method": "cash", "amount": Decimal("3000.00"), "tendered": Decimal("5000.00")}
    )

    assert payment.method == PaymentMethod.CASH
    assert payment.tendered is not None
    assert payment.tendered.amount == Decimal("5000.00")


def test_maps_a_mobile_money_payment_without_tendered_amount():
    payment = to_payment_input(
        {
            "method": "mobile_money",
            "amount": Decimal("3000.00"),
            "reference": "MM-1",
            "provider": "MTN",
        }
    )

    assert payment.method == PaymentMethod.MOBILE_MONEY
    assert payment.tendered is None
    assert payment.reference == "MM-1"


def test_complete_sale_command_uses_the_logged_in_cashier():
    cashier_id = uuid4()
    shift_id = uuid4()

    command = to_complete_sale_command(
        {
            "lines": [_line()],
            "payments": [{"method": "cash", "amount": Decimal("3000.00")}],
            "idempotency_key": "checkout-1",
            "notes": "",
        },
        cashier_id=cashier_id,
        shift_id=shift_id,
    )

    assert command.cashier_id == cashier_id
    assert command.shift_id == shift_id
    assert command.idempotency_key == "checkout-1"
    assert len(command.lines) == 1
    assert len(command.payments) == 1


def test_refund_and_void_commands_carry_the_user():
    user_id = uuid4()
    sale_id = uuid4()

    refund = to_refund_sale_command(
        {
            "sale_id": sale_id,
            "line_id": None,
            "quantity": 1,
            "reason": "Damaged",
            "restock": True,
        },
        user_id=user_id,
    )
    void = to_void_sale_command({"sale_id": sale_id, "reason": "Wrong item"}, user_id=user_id)

    assert (refund.user_id, void.user_id) == (user_id, user_id)
    assert (refund.sale_id, void.sale_id) == (sale_id, sale_id)
