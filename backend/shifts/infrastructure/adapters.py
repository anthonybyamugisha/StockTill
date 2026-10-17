from decimal import Decimal
from uuid import UUID

from django.db.models import Sum

from sales.infrastructure.models import PaymentModel, RefundModel, SaleModel
from shared.domain.money import Money
from shifts.application.ports import CashTotals, SalesSummaryPort


class SalesSummaryAdapter(SalesSummaryPort):
    def cash_totals(self, shift_id: UUID) -> CashTotals:
        sales = SaleModel.objects.filter(shift_id=shift_id)
        cash_sales = PaymentModel.objects.filter(sale__in=sales, method="cash").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        cash_refunds = RefundModel.objects.filter(sale__in=sales).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        return CashTotals(sales=Money(Decimal(cash_sales)), refunds=Money(Decimal(cash_refunds)))
