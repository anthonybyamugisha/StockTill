from decimal import Decimal
from typing import Any
from uuid import UUID

from sales.application.commands import (
    CompleteSaleCommand,
    LineItem,
    PaymentInput,
    RefundSaleCommand,
    VoidSaleCommand,
)
from sales.domain.entities import DiscountType, PaymentMethod
from shared.domain.money import Money


def to_line_item(data: dict[str, Any]) -> LineItem:
    return LineItem(
        product_id=data["product_id"],
        quantity=int(data["quantity"]),
        unit_price=Money(Decimal(str(data["unit_price"]))),
        unit_cost=Money(Decimal(str(data["unit_cost"]))),
        product_name=data.get("product_name", ""),
        discount_type=DiscountType(data["discount_type"]) if data.get("discount_type") else None,
        discount_value=Decimal(str(data["discount_value"])) if data.get("discount_value") else None,
    )


def to_payment_input(data: dict[str, Any]) -> PaymentInput:
    return PaymentInput(
        method=PaymentMethod(data["method"]),
        amount=Money(data["amount"]),
        tendered=Money(data["tendered"]) if data.get("tendered") else None,
        reference=data.get("reference"),
        provider=data.get("provider"),
    )


def to_complete_sale_command(
    data: dict[str, Any],
    *,
    cashier_id: UUID,
    shift_id: UUID | None,
    max_discount_percent: Decimal | None = None,
) -> CompleteSaleCommand:
    return CompleteSaleCommand(
        cashier_id=cashier_id,
        lines=[to_line_item(line) for line in data["lines"]],
        payments=[to_payment_input(payment) for payment in data["payments"]],
        idempotency_key=data["idempotency_key"],
        notes=data.get("notes", ""),
        shift_id=shift_id,
        max_discount_percent=max_discount_percent,
    )


def to_refund_sale_command(data: dict[str, Any], *, user_id: UUID) -> RefundSaleCommand:
    return RefundSaleCommand(
        sale_id=data["sale_id"],
        line_id=data.get("line_id"),
        quantity=data["quantity"],
        reason=data["reason"],
        restock=data["restock"],
        user_id=user_id,
    )


def to_void_sale_command(data: dict[str, Any], *, user_id: UUID) -> VoidSaleCommand:
    return VoidSaleCommand(
        sale_id=data["sale_id"],
        reason=data["reason"],
        user_id=user_id,
    )
