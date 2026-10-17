from dataclasses import dataclass, field
from uuid import UUID

from shared.domain.money import Money


@dataclass(frozen=True)
class CreateSupplierCommand:
    name: str
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    actor_id: UUID | None = None


@dataclass(frozen=True)
class UpdateSupplierCommand:
    supplier_id: UUID
    name: str
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    actor_id: UUID | None = None


@dataclass(frozen=True)
class PurchaseOrderLineInput:
    product_id: UUID
    quantity: int
    unit_cost: Money
    product_name: str = ""


@dataclass(frozen=True)
class CreatePurchaseOrderCommand:
    supplier_id: UUID
    lines: list[PurchaseOrderLineInput] = field(default_factory=list)
    reference: str = ""
    notes: str = ""
    actor_id: UUID | None = None


@dataclass(frozen=True)
class ReceivePurchaseOrderCommand:
    purchase_order_id: UUID
    user_id: UUID | None = None


@dataclass(frozen=True)
class CancelPurchaseOrderCommand:
    purchase_order_id: UUID
    reason: str = ""
    actor_id: UUID | None = None
