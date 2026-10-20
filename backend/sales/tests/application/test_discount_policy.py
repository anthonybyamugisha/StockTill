from decimal import Decimal
from uuid import uuid4

import pytest

from sales.application.commands import LineItem
from sales.application.discount_policy import (
    assert_discount_within_limit,
    discount_percent,
    discount_total,
)
from sales.domain.entities import DiscountType
from sales.domain.errors import DiscountLimitExceededError
from shared.domain.money import Money


def _line(*, discount_type=None, discount_value=None) -> LineItem:
    return LineItem(
        product_id=uuid4(),
        quantity=2,
        unit_price=Money(Decimal("100.00")),
        unit_cost=Money(Decimal("60.00")),
        discount_type=discount_type,
        discount_value=discount_value,
    )


def test_no_discounts_have_no_percentage():
    assert discount_total([_line()]) == Money.zero()
    assert discount_percent([_line()]) == Decimal("0")


def test_percentage_discount_is_reported_as_a_percentage_of_the_sale():
    line = _line(discount_type=DiscountType.PERCENTAGE, discount_value=Decimal("10"))

    assert discount_total([line]) == Money(Decimal("20.00"))
    assert discount_percent([line]) == Decimal("10.0")


def test_cashier_limit_allows_a_discount_at_the_limit():
    line = _line(discount_type=DiscountType.PERCENTAGE, discount_value=Decimal("10"))

    assert_discount_within_limit([line], Decimal("10"))


def test_cashier_limit_rejects_a_discount_above_the_limit():
    line = _line(discount_type=DiscountType.PERCENTAGE, discount_value=Decimal("11"))

    with pytest.raises(DiscountLimitExceededError, match="limited to 10%"):
        assert_discount_within_limit([line], Decimal("10"))
