from datetime import date

from django.db.models import Count, Sum

from reporting.application.queries import SalesByPaymentMethod
from sales.infrastructure.models import PaymentModel


class DjangoPaymentMethodSalesQuery:
    def execute(self, date_from: date, date_to: date) -> list[SalesByPaymentMethod]:
        payments = (
            PaymentModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("method")
            .annotate(count=Count("id"), total=Sum("amount"))
        )
        return [
            SalesByPaymentMethod(method=row["method"], count=row["count"], total=row["total"])
            for row in payments
        ]
