from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sales.domain.entities import Refund, Sale


@dataclass(frozen=True)
class SaleAuditEntry:
    user_id: UUID | None
    action: str
    sale_id: UUID
    before: dict[str, Any] | None
    after: dict[str, Any]

    def as_record_kwargs(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": "sale",
            "entity_id": str(self.sale_id),
            "before": self.before,
            "after": self.after,
        }


def sale_completed(sale: Sale) -> SaleAuditEntry:
    return SaleAuditEntry(
        user_id=sale.cashier_id,
        action="sale.completed",
        sale_id=sale.id,
        before=None,
        after={
            "receipt_number": sale.receipt_number,
            "total": str(sale.total.amount),
            "line_count": len(sale.lines),
            "payment_methods": sorted({payment.method.value for payment in sale.payments}),
        },
    )


def sale_refunded(
    sale: Sale, refund: Refund, previous_status: str, previous_refundable: str
) -> SaleAuditEntry:
    return SaleAuditEntry(
        user_id=refund.user_id,
        action="sale.refunded",
        sale_id=sale.id,
        before={"status": previous_status, "refundable_amount": previous_refundable},
        after={
            "status": sale.status.value,
            "amount": str(refund.amount.amount),
            "quantity": refund.quantity,
            "restock": refund.restock,
            "reason": refund.reason,
        },
    )


def sale_voided(
    sale: Sale, user_id: UUID | None, previous_status: str, reason: str
) -> SaleAuditEntry:
    return SaleAuditEntry(
        user_id=user_id,
        action="sale.voided",
        sale_id=sale.id,
        before={"status": previous_status, "total": str(sale.total.amount)},
        after={"status": sale.status.value, "reason": reason},
    )
