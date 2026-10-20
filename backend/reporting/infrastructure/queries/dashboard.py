from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import DashboardStats
from reporting.infrastructure.stock_levels import StockLevels
from sales.infrastructure.models import SaleModel
from shared.domain.money import Money


class DjangoDashboardQuery:
    def execute(self) -> DashboardStats:
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        today_sales = SaleModel.objects.filter(created_at__date=today)
        week_sales = SaleModel.objects.filter(created_at__date__range=(week_ago, today))
        month_sales = SaleModel.objects.filter(created_at__date__range=(month_ago, today))

        today_revenue = sum((Money(sale.total) for sale in today_sales), Money.zero())
        week_revenue = sum((Money(sale.total) for sale in week_sales), Money.zero())
        month_revenue = sum((Money(sale.total) for sale in month_sales), Money.zero())

        total_transactions = SaleModel.objects.count()
        total_products = ProductModel.objects.filter(is_active=True).count()

        levels = StockLevels.load()

        all_sales = SaleModel.objects.all()
        total_revenue = sum((Money(sale.total) for sale in all_sales), Money.zero())
        average_sale = total_revenue.amount / len(all_sales) if all_sales else Decimal(0)

        month_cost = Money.zero()
        for sale in month_sales.prefetch_related("lines"):
            for line in sale.lines.all():
                month_cost = month_cost.add(Money(line.unit_cost).multiply(Decimal(line.quantity)))
        month_profit = month_revenue.subtract(month_cost)

        return DashboardStats(
            today_sales=today_sales.count(),
            today_revenue=today_revenue.amount,
            week_sales=week_sales.count(),
            week_revenue=week_revenue.amount,
            month_sales=month_sales.count(),
            month_revenue=month_revenue.amount,
            total_transactions=total_transactions,
            total_products=total_products,
            low_stock_count=levels.low,
            out_of_stock_count=levels.out,
            average_sale_value=average_sale,
            gross_profit=month_profit.amount,
        )
