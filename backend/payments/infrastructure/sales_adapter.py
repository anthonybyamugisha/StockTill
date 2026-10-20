from decimal import Decimal
from typing import Any
from uuid import UUID

from accounts.infrastructure.models import UserModel
from payments.application.ports import SaleCompletionPort
from sales.application.commands import CompleteSaleCommand, LineItem, PaymentInput
from sales.domain.entities import DiscountType, PaymentMethod
from sales.infrastructure.adapters import ShiftAdapter
from sales.interfaces.api.container import build_complete_sale_use_case
from sales.interfaces.api.discount_limits import cashier_discount_limit
from shared.domain.money import Money


class SalesCompletionAdapter(SaleCompletionPort):
    """Completes a sale through the sales context once money has arrived."""

    def complete_sale(
        self,
        *,
        payload: dict[str, Any],
        method: str,
        amount: Money,
        reference: str | None,
        provider: str | None,
        idempotency_key: str,
        cashier_id: UUID,
        shift_id: UUID | None,
    ) -> UUID:
        if shift_id is None:
            shift_id = ShiftAdapter().open_shift_id(cashier_id)
        cashier = UserModel.objects.filter(id=cashier_id).only("role").first()
        max_discount_percent = cashier_discount_limit(cashier) if cashier is not None else None
        command = CompleteSaleCommand(
            cashier_id=cashier_id,
            lines=[self._line(item) for item in payload.get("lines", [])],
            payments=[
                PaymentInput(
                    method=PaymentMethod(method),
                    amount=amount,
                    reference=reference,
                    provider=provider,
                )
            ],
            idempotency_key=idempotency_key,
            notes=str(payload.get("notes") or ""),
            shift_id=shift_id,
            expected_total=amount,
            max_discount_percent=max_discount_percent,
        )
        sale = build_complete_sale_use_case().execute(command)
        return sale.id

    def _line(self, item: dict[str, Any]) -> LineItem:
        return LineItem(
            product_id=UUID(str(item["product_id"])),
            quantity=int(item["quantity"]),
            unit_price=Money(Decimal(str(item["unit_price"]))),
            unit_cost=Money(Decimal(str(item["unit_cost"]))),
            product_name=str(item.get("product_name") or ""),
            discount_type=DiscountType(item["discount_type"])
            if item.get("discount_type")
            else None,
            discount_value=Decimal(str(item["discount_value"]))
            if item.get("discount_value")
            else None,
        )
