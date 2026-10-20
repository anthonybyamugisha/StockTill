from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.utils import timezone

from reporting.application.queries import ProfitReport
from sales.infrastructure.models import SaleModel


class DjangoProfitReportQuery:
    def execute(self, date_from: date, date_to: date) -> list[ProfitReport]:
        sales = SaleModel.objects.filter(
            created_at__date__range=(date_from, date_to)
        ).prefetch_related("lines")
        revenue: dict[date, Decimal] = defaultdict(Decimal)
        cost: dict[date, Decimal] = defaultdict(Decimal)
        for sale in sales:
            day = timezone.localtime(sale.created_at).date()
            revenue[day] += sale.total
            for line in sale.lines.all():
                cost[day] += Decimal(line.unit_cost) * line.quantity
        days = sorted(set(revenue) | set(cost))
        return [
            ProfitReport(
                date=day,
                total_revenue=revenue[day],
                total_cost=cost[day],
                gross_profit=revenue[day] - cost[day],
            )
            for day in days
        ]
