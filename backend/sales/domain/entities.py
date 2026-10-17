from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from shared.domain.base import AggregateRoot, Entity
from shared.domain.money import Money


class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PaymentMethod(StrEnum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class SaleStatus(StrEnum):
    COMPLETED = "completed"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"


@dataclass(frozen=True)
class Discount:
    type: DiscountType
    value: Decimal
    amount: Money


@dataclass(eq=False)
class SaleLine(Entity):
    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity: int = 0
    unit_price: Money = field(default_factory=Money.zero)
    unit_cost: Money = field(default_factory=Money.zero)
    discount: Discount | None = None

    @property
    def gross_total(self) -> Money:
        return self.unit_price.multiply(Decimal(self.quantity))

    @property
    def total(self) -> Money:
        if self.discount:
            return self.gross_total.subtract(self.discount.amount)
        return self.gross_total

    @property
    def cost_total(self) -> Money:
        return self.unit_cost.multiply(Decimal(self.quantity))

    @property
    def profit(self) -> Money:
        return self.total.subtract(self.cost_total)


@dataclass(eq=False)
class Payment(Entity):
    method: PaymentMethod = PaymentMethod.CASH
    amount: Money = field(default_factory=Money.zero)
    tendered: Money | None = None
    change: Money | None = None
    reference: str | None = None
    provider: str | None = None

    def calculate_change(self) -> Money:
        if self.method != PaymentMethod.CASH or self.tendered is None:
            return Money.zero()
        change = self.tendered.subtract(self.amount)
        return max(change, Money.zero())


@dataclass(eq=False)
class Refund(Entity):
    sale_id: UUID = field(default_factory=uuid4)
    line_id: UUID | None = None
    quantity: int = 0
    amount: Money = field(default_factory=Money.zero)
    reason: str = ""
    restock: bool = False
    user_id: UUID | None = None
    created_at: datetime | None = None


@dataclass(eq=False)
class Sale(AggregateRoot):
    receipt_number: str = ""
    cashier_id: UUID | None = None
    shift_id: UUID | None = None
    lines: list[SaleLine] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    refunds: list[Refund] = field(default_factory=list)
    status: SaleStatus = SaleStatus.COMPLETED
    created_at: datetime | None = None
    notes: str = ""
    idempotency_key: str | None = None

    @property
    def subtotal(self) -> Money:
        return sum((line.gross_total for line in self.lines), Money.zero())

    @property
    def total_discount(self) -> Money:
        return sum(
            (line.discount.amount if line.discount else Money.zero() for line in self.lines),
            Money.zero(),
        )

    @property
    def total(self) -> Money:
        return sum((line.total for line in self.lines), Money.zero())

    @property
    def amount_paid(self) -> Money:
        return sum((p.amount for p in self.payments), Money.zero())

    @property
    def total_refunded(self) -> Money:
        return sum((r.amount for r in self.refunds), Money.zero())

    @property
    def refundable_amount(self) -> Money:
        return self.total.subtract(self.total_refunded)

    @property
    def cost_total(self) -> Money:
        return sum((line.cost_total for line in self.lines), Money.zero())

    @property
    def gross_profit(self) -> Money:
        return self.total.subtract(self.cost_total)

    def refundable_quantity_for_line(self, line_id: UUID) -> int:
        line = next((item for item in self.lines if item.id == line_id), None)
        if line is None:
            return 0
        already_refunded = sum(r.quantity for r in self.refunds if r.line_id == line_id)
        return line.quantity - already_refunded
