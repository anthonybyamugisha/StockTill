from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from reporting.application.queries import DailySales
from sales.infrastructure.models import SaleModel

_MAX_FILLED_DAYS = 366


class DjangoDailySalesQuery:
    def execute(self, date_from: date, date_to: date) -> list[DailySales]:
        rows = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"), total=Sum("total"))
        )
        sold: dict[date, DailySales] = {
            row["day"]: DailySales(
                date=row["day"], transaction_count=row["count"], total=row["total"] or 0
            )
            for row in rows
        }
        days = _date_range(date_from, date_to)
        if len(days) > _MAX_FILLED_DAYS:
            return [sold[day] for day in sorted(sold)]
        return [sold.get(day, DailySales(date=day, transaction_count=0, total=0)) for day in days]


def _date_range(date_from: date, date_to: date) -> list[date]:
    return [date_from + timedelta(days=offset) for offset in range((date_to - date_from).days + 1)]
