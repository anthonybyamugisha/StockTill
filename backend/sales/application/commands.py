from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sales.domain.entities import DiscountType, PaymentMethod
from shared.domain.money import Money


@dataclass(frozen=True)
class LineItem:
    product_id: UUID
    quantity: int
    unit_price: Money
    unit_cost: Money
    product_name: str = ""
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None


@dataclass(frozen=True)
class PaymentInput:
    method: PaymentMethod
    amount: Money
    tendered: Money | None = None
    reference: str | None = None
    provider: str | None = None


@dataclass(frozen=True)
class CompleteSaleCommand:
    cashier_id: UUID
    lines: list[LineItem]
    payments: list[PaymentInput]
    idempotency_key: str
    notes: str = ""
    shift_id: UUID | None = None
    expected_total: Money | None = None
    max_discount_percent: Decimal | None = None


@dataclass(frozen=True)
class RefundSaleCommand:
    sale_id: UUID
    line_id: UUID | None
    quantity: int
    reason: str
    restock: bool
    user_id: UUID


@dataclass(frozen=True)
class VoidSaleCommand:
    sale_id: UUID
    reason: str
    user_id: UUID
