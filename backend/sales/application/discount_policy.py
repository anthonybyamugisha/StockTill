from decimal import Decimal

from sales.application.commands import LineItem
from sales.domain.errors import DiscountLimitExceededError
from sales.domain.services import calculate_discount
from shared.domain.money import Money


def discount_total(items: list[LineItem]) -> Money:
    total = Money.zero()
    for item in items:
        if item.discount_type is not None and item.discount_value is not None:
            total += calculate_discount(
                item.unit_price, item.quantity, item.discount_type, item.discount_value
            ).amount
    return total


def discount_percent(items: list[LineItem]) -> Decimal:
    subtotal = sum(
        (item.unit_price.multiply(Decimal(item.quantity)) for item in items), Money.zero()
    )
    if subtotal.amount <= 0:
        return Decimal("0")
    return (discount_total(items).amount / subtotal.amount) * Decimal("100")


def assert_discount_within_limit(items: list[LineItem], max_percent: Decimal) -> None:
    if max_percent < 0:
        max_percent = Decimal("0")
    actual = discount_percent(items)
    if actual > max_percent:
        raise DiscountLimitExceededError(
            f"Discounts are limited to {max_percent}% for cashiers "
            f"(this sale has {actual.quantize(Decimal('0.01'))}%)"
        )
