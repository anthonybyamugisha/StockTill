from datetime import date
from decimal import Decimal

from reporting.application.queries import SalesSummary
from sales.infrastructure.models import SaleModel
from shared.domain.money import Money


class DjangoSalesSummaryQuery:
    def execute(self, date_from: date, date_to: date) -> SalesSummary:
        sales = SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
        total_sales = sales.count()
        total_revenue = sum((Money(sale.total) for sale in sales), Money.zero())
        total_cost = Money.zero()
        for sale in sales:
            for line in sale.lines.all():
                total_cost = total_cost.add(Money(line.unit_cost).multiply(Decimal(line.quantity)))
        gross_profit = total_revenue.subtract(total_cost)
        average = total_revenue.amount / total_sales if total_sales > 0 else Decimal(0)
        return SalesSummary(
            total_sales=total_sales,
            total_revenue=total_revenue.amount,
            total_cost=total_cost.amount,
            gross_profit=gross_profit.amount,
            average_sale_value=average,
            date_from=date_from,
            date_to=date_to,
        )
