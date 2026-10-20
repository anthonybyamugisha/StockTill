from typing import Any
from uuid import UUID

from payments.application.commands import (
    CancelPaymentIntentCommand,
    CreatePaymentIntentCommand,
)
from payments.application.phone import normalize_phone
from payments.domain.entities import MobileNetwork, PaymentMethod
from shared.domain.money import Money


def _sale_line(line: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": str(line["product_id"]),
        "product_name": line.get("product_name", ""),
        "quantity": line["quantity"],
        "unit_price": str(line["unit_price"]),
        "unit_cost": str(line["unit_cost"]),
        "discount_type": line.get("discount_type"),
        "discount_value": (
            str(line["discount_value"]) if line.get("discount_value") is not None else None
        ),
    }


def to_create_intent_command(
    data: dict[str, Any], *, cashier_id: UUID
) -> CreatePaymentIntentCommand:
    sale = data["sale"]
    return CreatePaymentIntentCommand(
        cashier_id=cashier_id,
        method=PaymentMethod(data["method"]),
        amount=Money(data["amount"]),
        idempotency_key=data["idempotency_key"],
        phone=normalize_phone(data["phone"]),
        network=MobileNetwork(data["network"]),
        sale_payload={
            "lines": [_sale_line(line) for line in sale["lines"]],
            "notes": sale.get("notes", ""),
        },
    )


def to_cancel_intent_command(
    data: dict[str, Any], *, intent_id: UUID, actor_id: UUID
) -> CancelPaymentIntentCommand:
    return CancelPaymentIntentCommand(
        intent_id=intent_id,
        reason=data.get("reason", ""),
        actor_id=actor_id,
    )
