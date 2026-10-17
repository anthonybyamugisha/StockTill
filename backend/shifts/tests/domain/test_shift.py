from decimal import Decimal

import pytest

from shared.domain.money import Money
from shifts.domain.entities import CashMovement, CashMovementType, Shift
from shifts.domain.errors import ShiftAlreadyClosedError


def money(value: str) -> Money:
    return Money(Decimal(value))


def test_expected_cash_is_float_plus_cash_sales_minus_refunds():
    shift = Shift(opening_float=money("100000.00"))

    expected = shift.expected_cash(money("50000.00"), money("20000.00"))

    assert expected.amount == money("130000.00").amount


def test_expected_cash_includes_net_cash_movements():
    shift = Shift(
        opening_float=money("100000.00"),
        cash_movements=[
            CashMovement(type=CashMovementType.PAYOUT, amount=money("30000.00")),
            CashMovement(type=CashMovementType.CASH_IN, amount=money("5000.00")),
        ],
    )

    expected = shift.expected_cash(money("0.00"), money("0.00"))

    assert expected.amount == money("75000.00").amount


def test_variance_is_counted_minus_expected():
    shift = Shift(opening_float=money("100000.00"), counted_cash=money("98000.00"))

    variance = shift.variance(money("0.00"), money("0.00"))

    assert variance is not None
    assert variance.amount == money("-2000.00").amount


def test_variance_is_none_before_the_drawer_is_counted():
    shift = Shift(opening_float=money("100000.00"))
    assert shift.variance(money("0.00"), money("0.00")) is None


def test_closing_sets_status_and_counted_cash():
    shift = Shift(opening_float=money("100000.00"))

    shift.close(money("99500.00"), at=None, notes="till balanced")  # type: ignore[arg-type]

    assert shift.status.value == "closed"
    assert shift.counted_cash is not None
    assert shift.counted_cash.amount == money("99500.00").amount
    assert shift.is_open is False


def test_closing_twice_is_rejected():
    shift = Shift(opening_float=money("0.00"))
    shift.close(money("0.00"), at=None)  # type: ignore[arg-type]

    with pytest.raises(ShiftAlreadyClosedError):
        shift.close(money("0.00"), at=None)  # type: ignore[arg-type]


def test_cash_movement_signed_amounts():
    payout = CashMovement(type=CashMovementType.PAYOUT, amount=money("1000.00"))
    cash_in = CashMovement(type=CashMovementType.CASH_IN, amount=money("1000.00"))

    assert payout.signed_amount().amount == money("-1000.00").amount
    assert cash_in.signed_amount().amount == money("1000.00").amount
