from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from payments.domain.errors import (
    IntentAlreadySettledError,
    InvalidIntentTransitionError,
    InvalidPaymentAmountError,
    MissingMobileMoneyDetailsError,
)
from shared.domain.base import AggregateRoot
from shared.domain.money import Money


class PaymentMethod(StrEnum):
    MOBILE_MONEY = "mobile_money"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class MobileNetwork(StrEnum):
    MTN = "mtn"
    AIRTEL = "airtel"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"


@dataclass(eq=False)
class PaymentIntent(AggregateRoot):
    tx_ref: str = ""
    idempotency_key: str = ""
    cashier_id: UUID | None = None
    shift_id: UUID | None = None
    method: PaymentMethod = PaymentMethod.MOBILE_MONEY
    network: MobileNetwork | None = None
    phone: str = ""
    amount: Money = field(default_factory=Money.zero)
    status: PaymentStatus = PaymentStatus.PENDING
    provider: str = ""
    gateway_reference: str | None = None
    checkout_url: str | None = None
    failure_reason: str = ""
    sale_id: UUID | None = None
    sale_payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    expires_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        tx_ref: str,
        idempotency_key: str,
        cashier_id: UUID,
        shift_id: UUID | None,
        method: PaymentMethod,
        amount: Money,
        phone: str = "",
        network: MobileNetwork | None = None,
        sale_payload: dict[str, Any] | None = None,
        created_at: datetime,
        expires_at: datetime,
    ) -> "PaymentIntent":
        if amount.is_zero() or amount.is_negative():
            raise InvalidPaymentAmountError("A payment must be for more than zero")
        if method == PaymentMethod.MOBILE_MONEY:
            if not phone.strip():
                raise MissingMobileMoneyDetailsError("A mobile money payment needs a phone number")
            if network is None:
                raise MissingMobileMoneyDetailsError("A mobile money payment needs a network")
        return cls(
            tx_ref=tx_ref,
            idempotency_key=idempotency_key,
            cashier_id=cashier_id,
            shift_id=shift_id,
            method=method,
            network=network,
            phone=phone.strip(),
            amount=amount,
            sale_payload=sale_payload or {},
            created_at=created_at,
            updated_at=created_at,
            expires_at=expires_at,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            PaymentStatus.FAILED,
            PaymentStatus.EXPIRED,
            PaymentStatus.CANCELLED,
        }

    @property
    def is_settled(self) -> bool:
        return self.status in {PaymentStatus.PAID, PaymentStatus.NEEDS_REVIEW}

    def is_expired(self, at: datetime) -> bool:
        return self.expires_at is not None and at >= self.expires_at

    def attach_gateway(
        self,
        *,
        provider: str,
        gateway_reference: str | None,
        checkout_url: str | None = None,
        at: datetime,
    ) -> None:
        self._require_pending("attach a gateway")
        self.provider = provider
        self.gateway_reference = gateway_reference
        self.checkout_url = checkout_url
        self.updated_at = at

    def mark_paid(
        self, *, gateway_reference: str | None, sale_id: UUID | None, at: datetime
    ) -> None:
        if self.status == PaymentStatus.PAID:
            return
        self._require_pending("be marked paid")
        self.status = PaymentStatus.PAID
        if gateway_reference:
            self.gateway_reference = gateway_reference
        self.sale_id = sale_id
        self.confirmed_at = at
        self.updated_at = at
        self.failure_reason = ""

    def mark_needs_review(self, *, reason: str, at: datetime) -> None:
        if self.status == PaymentStatus.NEEDS_REVIEW:
            return
        if self.status != PaymentStatus.PAID:
            raise InvalidIntentTransitionError("Only a paid intent can need review")
        self.status = PaymentStatus.NEEDS_REVIEW
        self.failure_reason = reason
        self.updated_at = at

    def mark_reconciled(self, *, sale_id: UUID, at: datetime) -> None:
        if self.status != PaymentStatus.NEEDS_REVIEW:
            raise InvalidIntentTransitionError("Only an intent needing review can be reconciled")
        self.status = PaymentStatus.PAID
        self.sale_id = sale_id
        self.failure_reason = ""
        self.updated_at = at

    def mark_failed(self, *, reason: str, at: datetime) -> None:
        if self.status == PaymentStatus.FAILED:
            return
        self._require_pending("fail")
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = at

    def cancel(self, *, reason: str, at: datetime) -> None:
        if self.status == PaymentStatus.CANCELLED:
            return
        self._require_pending("be cancelled")
        self.status = PaymentStatus.CANCELLED
        self.failure_reason = reason
        self.updated_at = at

    def expire(self, *, at: datetime) -> None:
        if self.status == PaymentStatus.EXPIRED:
            return
        self._require_pending("expire")
        self.status = PaymentStatus.EXPIRED
        self.failure_reason = "The payment request expired"
        self.updated_at = at

    def _require_pending(self, action: str) -> None:
        if self.status == PaymentStatus.PENDING:
            return
        if self.status == PaymentStatus.PAID:
            raise IntentAlreadySettledError(f"This payment is already paid and cannot {action}")
        raise InvalidIntentTransitionError(f"A {self.status.value} payment cannot {action}")
