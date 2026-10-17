from decimal import Decimal

from sales.domain.entities import Discount, DiscountType, Payment, PaymentMethod
from shared.domain.money import Money


def calculate_discount(
    unit_price: Money, quantity: int, discount_type: DiscountType, value: Decimal
) -> Discount:
    line_total = unit_price.multiply(Decimal(quantity))

    if discount_type == DiscountType.PERCENTAGE:
        discount_amount = line_total.multiply(value / Decimal(100))
    else:
        discount_amount = Money(value)

    discount_amount = min(discount_amount, line_total)
    discount_amount = max(discount_amount, Money.zero())

    return Discount(type=discount_type, value=value, amount=discount_amount)


def calculate_change(payment: Payment) -> Money:
    if payment.method != PaymentMethod.CASH:
        return Money.zero()
    if payment.tendered is None:
        return Money.zero()
    return max(payment.tendered.subtract(payment.amount), Money.zero())
