from dataclasses import dataclass
from typing import Any
from uuid import UUID

from payments.domain.entities import PaymentIntent


@dataclass(frozen=True)
class PaymentAuditEntry:
    user_id: UUID | None
    action: str
    intent_id: UUID
    before: dict[str, Any] | None
    after: dict[str, Any]

    def as_record_kwargs(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": "payment_intent",
            "entity_id": str(self.intent_id),
            "before": self.before,
            "after": self.after,
        }


def intent_initiated(intent: PaymentIntent) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=intent.cashier_id,
        action="payment.initiated",
        intent_id=intent.id,
        before=None,
        after={
            "tx_ref": intent.tx_ref,
            "method": intent.method.value,
            "network": intent.network.value if intent.network else None,
            "amount": str(intent.amount.amount),
            "currency": intent.amount.currency,
            "provider": intent.provider,
        },
    )


def intent_confirmed(intent: PaymentIntent) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=intent.cashier_id,
        action="payment.confirmed",
        intent_id=intent.id,
        before={"status": "pending"},
        after={
            "status": intent.status.value,
            "tx_ref": intent.tx_ref,
            "sale_id": str(intent.sale_id) if intent.sale_id else None,
            "gateway_reference": intent.gateway_reference,
        },
    )


def intent_failed(intent: PaymentIntent) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=intent.cashier_id,
        action="payment.failed",
        intent_id=intent.id,
        before={"status": "pending"},
        after={"status": intent.status.value, "reason": intent.failure_reason},
    )


def intent_cancelled(intent: PaymentIntent, actor_id: UUID | None) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=actor_id,
        action="payment.cancelled",
        intent_id=intent.id,
        before={"status": "pending"},
        after={"status": intent.status.value, "reason": intent.failure_reason},
    )


def intent_needs_review(intent: PaymentIntent) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=intent.cashier_id,
        action="payment.needs_review",
        intent_id=intent.id,
        before={"status": "paid", "sale_id": None},
        after={"status": intent.status.value, "reason": intent.failure_reason},
    )


def intent_expired(intent: PaymentIntent) -> PaymentAuditEntry:
    return PaymentAuditEntry(
        user_id=intent.cashier_id,
        action="payment.expired",
        intent_id=intent.id,
        before={"status": "pending"},
        after={"status": intent.status.value, "tx_ref": intent.tx_ref},
    )
