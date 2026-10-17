from datetime import date

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate

from reporting.application.queries import (
    CashierSales,
    DailySales,
    SalesByPaymentMethod,
    SalesSummary,
    TopProduct,
)
from sales.infrastructure.models import PaymentModel, SaleLineModel, SaleModel
from shared.domain.money import Money


class SalesQueryBuilder:
    def get_sales_summary(self, date_from: date, date_to: date) -> SalesSummary:
        sales = SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
        total_sales = sales.count()
        total_revenue = sum((Money(s.total) for s in sales), Money.zero())
        total_cost = sum(
            (Money(sum(line.unit_cost * line.quantity for line in s.lines.all())) for s in sales),
            Money.zero(),
        )
        gross_profit = total_revenue.subtract(total_cost)
        avg = total_revenue.amount / total_sales if total_sales > 0 else 0
        return SalesSummary(
            total_sales=total_sales,
            total_revenue=total_revenue,
            total_cost=total_cost,
            gross_profit=gross_profit,
            average_sale_value=Money(avg),
            date_from=date_from,
            date_to=date_to,
        )

    def get_top_products(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]:
        lines = (
            SaleLineModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("product_id", "product_name")
            .annotate(total_qty=Sum("quantity"), total_rev=Sum(F("quantity") * F("unit_price")))
            .order_by("-total_qty")[:limit]
        )
        return [
            TopProduct(
                product_id=str(row["product_id"]),
                product_name=row["product_name"],
                quantity_sold=row["total_qty"],
                revenue=Money(row["total_rev"]),
            )
            for row in lines
        ]

    def get_sales_by_payment_method(
        self, date_from: date, date_to: date
    ) -> list[SalesByPaymentMethod]:
        payments = (
            PaymentModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("method")
            .annotate(count=Count("id"), total=Sum("amount"))
        )
        return [
            SalesByPaymentMethod(
                method=row["method"],
                count=row["count"],
                total=Money(row["total"]),
            )
            for row in payments
        ]

    def get_daily_sales(self, date_from: date, date_to: date) -> list[DailySales]:
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("day")
        )
        return [
            DailySales(
                date=row["day"],
                transaction_count=row["count"],
                total=Money(row["total"]),
            )
            for row in sales
        ]

    def get_cashier_sales(self, date_from: date, date_to: date) -> list[CashierSales]:
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .values("cashier_id")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("-total")
        )
        return [
            CashierSales(
                cashier_id=str(row["cashier_id"]),
                cashier_name="",
                transaction_count=row["count"],
                total=Money(row["total"]),
            )
            for row in sales
        ]
