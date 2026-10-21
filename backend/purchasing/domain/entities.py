from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from purchasing.domain.errors import (
    EmptyPurchaseOrderError,
    InvalidInvoiceStateError,
    InvalidPurchaseOrderStateError,
    InvalidSupplierError,
)
from shared.domain.base import AggregateRoot, Entity
from shared.domain.money import Money


class PurchaseOrderStatus(StrEnum):
    DRAFT = "draft"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class SupplierInvoiceStatus(StrEnum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    VOID = "void"


@dataclass(eq=False)
class Supplier(Entity):
    name: str = ""
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    is_active: bool = True
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidSupplierError("Supplier name is required")

    def update_contact(
        self,
        *,
        name: str,
        contact_name: str,
        email: str,
        phone: str,
        address: str,
    ) -> None:
        if not name.strip():
            raise InvalidSupplierError("Supplier name is required")
        self.name = name
        self.contact_name = contact_name
        self.email = email
        self.phone = phone
        self.address = address

    def deactivate(self) -> None:
        self.is_active = False


@dataclass(eq=False)
class PurchaseOrderLine(Entity):
    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity: int = 0
    unit_cost: Money = field(default_factory=Money.zero)

    @property
    def line_total(self) -> Money:
        return self.unit_cost.multiply(Decimal(self.quantity))


@dataclass(eq=False)
class PurchaseOrder(AggregateRoot):
    supplier_id: UUID | None = None
    supplier_name: str = ""
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    reference: str = ""
    notes: str = ""
    lines: list[PurchaseOrderLine] = field(default_factory=list)
    created_at: datetime | None = None
    ordered_at: datetime | None = None
    received_at: datetime | None = None

    @property
    def total(self) -> Money:
        return sum((line.line_total for line in self.lines), Money.zero())

    @property
    def is_received(self) -> bool:
        return self.status == PurchaseOrderStatus.RECEIVED

    def mark_ordered(self, at: datetime) -> None:
        if self.status != PurchaseOrderStatus.DRAFT:
            raise InvalidPurchaseOrderStateError("Only draft orders can be sent to a supplier")
        if not self.lines:
            raise EmptyPurchaseOrderError("Cannot order a purchase order with no lines")
        self.status = PurchaseOrderStatus.ORDERED
        self.ordered_at = at

    def receive(self, at: datetime) -> None:
        if self.status == PurchaseOrderStatus.RECEIVED:
            raise InvalidPurchaseOrderStateError("Purchase order is already received")
        if self.status == PurchaseOrderStatus.CANCELLED:
            raise InvalidPurchaseOrderStateError("Cannot receive a cancelled purchase order")
        if not self.lines:
            raise EmptyPurchaseOrderError("Cannot receive a purchase order with no lines")
        self.status = PurchaseOrderStatus.RECEIVED
        self.received_at = at

    def cancel(self, reason: str = "") -> None:
        if self.status == PurchaseOrderStatus.RECEIVED:
            raise InvalidPurchaseOrderStateError("Cannot cancel a received purchase order")
        if self.status == PurchaseOrderStatus.CANCELLED:
            raise InvalidPurchaseOrderStateError("Purchase order is already cancelled")
        if reason:
            self.notes = f"{self.notes}\nCancelled: {reason}".strip()
        self.status = PurchaseOrderStatus.CANCELLED


@dataclass(eq=False)
class SupplierInvoiceLine(Entity):
    product_id: UUID | None = None
    product_name: str = ""
    description: str = ""
    quantity: int = 1
    unit_cost: Money = field(default_factory=Money.zero)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidInvoiceStateError("Invoice line quantity must be greater than zero")
        if self.unit_cost.is_negative():
            raise InvalidInvoiceStateError("Invoice line cost cannot be negative")

    @property
    def line_total(self) -> Money:
        return self.unit_cost.multiply(Decimal(self.quantity))


@dataclass(eq=False)
class SupplierInvoice(AggregateRoot):
    supplier_id: UUID | None = None
    supplier_name: str = ""
    invoice_number: str = ""
    invoice_date: date | None = None
    due_date: date | None = None
    purchase_order_id: UUID | None = None
    status: SupplierInvoiceStatus = SupplierInvoiceStatus.UNPAID
    notes: str = ""
    lines: list[SupplierInvoiceLine] = field(default_factory=list)
    amount_paid: Money = field(default_factory=Money.zero)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.invoice_number.strip():
            raise InvalidInvoiceStateError("Invoice number is required")
        if not self.lines:
            raise InvalidInvoiceStateError("Invoice must have at least one line")

    @property
    def total(self) -> Money:
        return sum((line.line_total for line in self.lines), Money.zero())

    @property
    def balance(self) -> Money:
        return self.total.subtract(self.amount_paid)

    def record_payment(self, amount: Money) -> None:
        if self.status == SupplierInvoiceStatus.VOID:
            raise InvalidInvoiceStateError("Cannot pay a void invoice")
        if self.status == SupplierInvoiceStatus.PAID:
            raise InvalidInvoiceStateError("Invoice is already paid")
        if amount.amount <= 0:
            raise InvalidInvoiceStateError("Payment amount must be greater than zero")
        if amount > self.balance:
            raise InvalidInvoiceStateError("Payment cannot exceed the outstanding balance")
        self.amount_paid = self.amount_paid.add(amount)
        self.status = (
            SupplierInvoiceStatus.PAID
            if self.amount_paid >= self.total
            else SupplierInvoiceStatus.PARTIAL
        )

    def void(self, reason: str = "") -> None:
        if self.status == SupplierInvoiceStatus.VOID:
            raise InvalidInvoiceStateError("Invoice is already void")
        if self.status == SupplierInvoiceStatus.PAID or not self.amount_paid.is_zero():
            raise InvalidInvoiceStateError("Only unpaid invoices can be voided")
        if reason:
            self.notes = f"{self.notes}\nVoided: {reason}".strip()
        self.status = SupplierInvoiceStatus.VOID
