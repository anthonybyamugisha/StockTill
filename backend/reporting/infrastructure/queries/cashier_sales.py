from datetime import date

from django.db.models import Count, Sum

from reporting.application.queries import CashierSales
from reporting.infrastructure.directories import CashierDirectory
from sales.infrastructure.models import SaleModel


class DjangoCashierSalesQuery:
    def execute(self, date_from: date, date_to: date) -> list[CashierSales]:
        cashiers = CashierDirectory.load()
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .values("cashier_id")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("-total")
        )
        return [
            CashierSales(
                cashier_id=row["cashier_id"],
                cashier_name=cashiers.label_for(row["cashier_id"]),
                transaction_count=row["count"],
                total=row["total"],
            )
            for row in sales
        ]
