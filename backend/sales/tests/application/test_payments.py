from decimal import Decimal

from sales.application.commands import PaymentInput
from sales.application.payments import build_payment
from sales.domain.entities import PaymentMethod
from shared.domain.money import Money


def test_cash_payments_record_the_change_due():
    payment = build_payment(
        PaymentInput(
            method=PaymentMethod.CASH,
            amount=Money(Decimal("5000.00")),
            tendered=Money(Decimal("6000.00")),
        )
    )

    assert payment.change is not None
    assert payment.change.amount == Decimal("1000.00")


def test_cash_payments_without_enough_tendered_get_no_change():
    payment = build_payment(
        PaymentInput(
            method=PaymentMethod.CASH,
            amount=Money(Decimal("5000.00")),
            tendered=Money(Decimal("4000.00")),
        )
    )

    assert payment.change is not None
    assert payment.change.amount == Decimal("0.00")


def test_mobile_money_keeps_the_reference_and_omits_the_change():
    payment = build_payment(
        PaymentInput(
            method=PaymentMethod.MOBILE_MONEY,
            amount=Money(Decimal("5000.00")),
            reference="MM-123",
            provider="MTN",
        )
    )

    assert payment.change is None
    assert payment.reference == "MM-123"
    assert payment.provider == "MTN"
