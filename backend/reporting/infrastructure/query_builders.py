from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import (
    DashboardStats,
    InventoryReport,
    LowStockItem,
    ProfitReport,
)
from reporting.infrastructure.directories import CashierDirectory, CatalogDirectory
from reporting.infrastructure.stock_levels import StockLevels
from sales.infrastructure.models import SaleModel
from shared.domain.money import Money

_MAX_FILLED_DAYS = 366


def _date_range(date_from: date, date_to: date) -> list[date]:
    return [date_from + timedelta(days=offset) for offset in range((date_to - date_from).days + 1)]


class SalesQueryBuilder:
    def _cashier_names(self) -> dict:
        return CashierDirectory.load().labels

    def _products_by_id(self) -> dict:
        return CatalogDirectory.load().products

    def _stock_counts(self) -> tuple[int, int]:
        levels = StockLevels.load()
        return levels.low, levels.out

    def get_profit_report(self, date_from: date, date_to: date) -> list[ProfitReport]:
        sales = SaleModel.objects.filter(
            created_at__date__range=(date_from, date_to)
        ).prefetch_related("lines")
        revenue: dict = defaultdict(Decimal)
        cost: dict = defaultdict(Decimal)
        for sale in sales:
            day = sale.created_at.date()
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

    def get_dashboard_stats(self) -> DashboardStats:
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        today_sales = SaleModel.objects.filter(created_at__date=today)
        week_sales = SaleModel.objects.filter(created_at__date__range=(week_ago, today))
        month_sales = SaleModel.objects.filter(created_at__date__range=(month_ago, today))

        today_revenue = sum((Money(s.total) for s in today_sales), Money.zero())
        week_revenue = sum((Money(s.total) for s in week_sales), Money.zero())
        month_revenue = sum((Money(s.total) for s in month_sales), Money.zero())

        total_transactions = SaleModel.objects.count()
        total_products = ProductModel.objects.filter(is_active=True).count()

        low_stock, out_of_stock = self._stock_counts()

        all_sales = SaleModel.objects.all()
        total_rev = sum((Money(s.total) for s in all_sales), Money.zero())
        avg_sale = total_rev.amount / len(all_sales) if all_sales else Decimal(0)

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
            low_stock_count=low_stock,
            out_of_stock_count=out_of_stock,
            average_sale_value=avg_sale,
            gross_profit=month_profit.amount,
        )

    def get_inventory_report(self) -> InventoryReport:
        from inventory.infrastructure.models import StockItemModel

        products = self._products_by_id()
        total_value = Money.zero()
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product is None:
                continue
            total_value = total_value.add(
                Money(product.buying_cost).multiply(Decimal(item.quantity_on_hand))
            )

        low_stock, out_of_stock = self._stock_counts()

        return InventoryReport(
            total_products=ProductModel.objects.filter(is_active=True).count(),
            total_value=total_value.amount,
            low_stock_count=low_stock,
            out_of_stock_count=out_of_stock,
        )

    def get_low_stock_items(self) -> list[LowStockItem]:
        from inventory.infrastructure.models import StockItemModel

        products = {p.id: p for p in ProductModel.objects.filter(minimum_stock_level__gt=0)}
        items = []
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product and item.quantity_on_hand <= product.minimum_stock_level:
                items.append(
                    LowStockItem(
                        product_id=item.product_id,
                        product_name=product.name,
                        sku=product.sku,
                        quantity_on_hand=item.quantity_on_hand,
                        minimum_level=product.minimum_stock_level,
                    )
                )
        return items
