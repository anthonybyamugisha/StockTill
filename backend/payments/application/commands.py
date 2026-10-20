from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID

from payments.domain.entities import MobileNetwork, PaymentMethod
from shared.domain.money import Money


@dataclass(frozen=True)
class CreatePaymentIntentCommand:
    cashier_id: UUID
    method: PaymentMethod
    amount: Money
    idempotency_key: str
    phone: str = ""
    network: MobileNetwork | None = None
    shift_id: UUID | None = None
    sale_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfirmPaymentCommand:
    tx_ref: str
    paid: bool
    gateway_reference: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    message: str = ""


@dataclass(frozen=True)
class CancelPaymentIntentCommand:
    intent_id: UUID
    reason: str = ""
    actor_id: UUID | None = None
