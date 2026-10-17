from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from shared.domain.base import AggregateRoot, Entity
from shared.domain.money import Money


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PaymentMethod(str, Enum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class SaleStatus(str, Enum):
    COMPLETED = "completed"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"


@dataclass(frozen=True)
class Discount:
    type: DiscountType
    value: float
    amount: Money = field(default_factory=Money.zero)


@dataclass
class SaleLine(Entity):
    product_id: UUID = field(default_factory=UUID)
    product_name: str = ""
    quantity: int = 0
    unit_price: Money = field(default_factory=Money.zero)
    unit_cost: Money = field(default_factory=Money.zero)
    discount: Discount | None = None

    @property
    def total(self) -> Money:
        if self.discount:
            return self.unit_price.multiply(Decimal(self.quantity)).subtract(self.discount.amount)
        return self.unit_price.multiply(Decimal(self.quantity))


@dataclass
class Payment(Entity):
    method: PaymentMethod = PaymentMethod.CASH
    amount: Money = field(default_factory=Money.zero)
    tendered: Money | None = None
    change: Money | None = None
    reference: str | None = None
    provider: str | None = None


@dataclass
class Refund(Entity):
    sale_id: UUID = field(default_factory=UUID)
    line_id: UUID | None = None
    quantity: int = 0
    amount: Money = field(default_factory=Money.zero)
    reason: str = ""
    restock: bool = False
    user_id: UUID | None = None
    created_at: datetime | None = None


@dataclass
class Sale(AggregateRoot):
    receipt_number: str = ""
    cashier_id: UUID | None = None
    lines: list[SaleLine] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    refunds: list[Refund] = field(default_factory=list)
    status: SaleStatus = SaleStatus.COMPLETED
    created_at: datetime | None = None

    @property
    def subtotal(self) -> Money:
        return sum((line.total for line in self.lines), Money.zero())

    @property
    def total_discount(self) -> Money:
        return sum(
            (line.discount.amount if line.discount else Money.zero() for line in self.lines),
            Money.zero(),
        )

    @property
    def total(self) -> Money:
        return self.subtotal.subtract(self.total_discount)

    @property
    def amount_paid(self) -> Money:
        return sum((p.amount for p in self.payments), Money.zero())

    @property
    def total_refunded(self) -> Money:
        return sum((r.amount for r in self.refunds), Money.zero())

    @property
    def refundable_amount(self) -> Money:
        return self.total.subtract(self.total_refunded)


from decimal import Decimal  # noqa: E402
