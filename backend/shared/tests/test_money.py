from decimal import Decimal

from shared.domain.money import Money


def test_money_add():
    assert Money(Decimal("1.00")) + Money(Decimal("2.00")) == Money(Decimal("3.00"))


def test_money_subtract_operator():
    assert Money(Decimal("5.00")) - Money(Decimal("2.00")) == Money(Decimal("3.00"))


def test_money_sum_over_iterable():
    total = sum([Money(Decimal("1.50")), Money(Decimal("2.25"))], Money.zero())
    assert total == Money(Decimal("3.75"))


def test_money_with_different_currencies_not_equal():
    assert Money(Decimal("1.00"), "UGX") != Money(Decimal("1.00"), "USD")
