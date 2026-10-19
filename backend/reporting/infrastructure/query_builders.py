from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import (
    CashierSales,
    DailySales,
    DashboardStats,
    InventoryReport,
    LowStockItem,
    ProfitReport,
    SalesByPaymentMethod,
    SalesReportRow,
    SalesSummary,
    TopProduct,
)
from reporting.infrastructure.directories import CashierDirectory
from sales.infrastructure.models import PaymentModel, SaleLineModel, SaleModel
from shared.domain.money import Money

_MAX_FILLED_DAYS = 366


def _date_range(date_from: date, date_to: date) -> list[date]:
    return [date_from + timedelta(days=offset) for offset in range((date_to - date_from).days + 1)]


class SalesQueryBuilder:
    def _cashier_names(self) -> dict:
        return CashierDirectory.load().labels

    def _products_by_id(self) -> dict:
        return {p.id: p for p in ProductModel.objects.all()}

    def _stock_counts(self) -> tuple[int, int]:
        from inventory.infrastructure.models import StockItemModel

        products = self._products_by_id()
        low = 0
        out = 0
        for item in StockItemModel.objects.all():
            if item.quantity_on_hand == 0:
                out += 1
            product = products.get(item.product_id)
            if (
                product
                and product.minimum_stock_level > 0
                and item.quantity_on_hand <= product.minimum_stock_level
            ):
                low += 1
        return low, out

    def get_sales_summary(self, date_from: date, date_to: date) -> SalesSummary:
        sales = SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
        total_sales = sales.count()
        total_revenue = sum((Money(s.total) for s in sales), Money.zero())
        total_cost = Money.zero()
        for sale in sales:
            for line in sale.lines.all():
                total_cost = total_cost.add(Money(line.unit_cost).multiply(Decimal(line.quantity)))
        gross_profit = total_revenue.subtract(total_cost)
        avg = total_revenue.amount / total_sales if total_sales > 0 else Decimal(0)
        return SalesSummary(
            total_sales=total_sales,
            total_revenue=total_revenue.amount,
            total_cost=total_cost.amount,
            gross_profit=gross_profit.amount,
            average_sale_value=avg,
            date_from=date_from,
            date_to=date_to,
        )

    def get_top_products(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]:
        rows = list(
            SaleLineModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("product_id")
            .annotate(total_qty=Sum("quantity"), total_rev=Sum(F("quantity") * F("unit_price")))
            .order_by("-total_qty")[:limit]
        )
        product_ids = [row["product_id"] for row in rows]
        names = dict(ProductModel.objects.filter(id__in=product_ids).values_list("id", "name"))
        returned_names: dict = {}
        for product_id, line_name in SaleLineModel.objects.filter(
            product_id__in=product_ids
        ).values_list("product_id", "product_name"):
            if line_name:
                returned_names.setdefault(product_id, line_name)
        return [
            TopProduct(
                product_id=row["product_id"],
                product_name=names.get(row["product_id"])
                or returned_names.get(row["product_id"])
                or "Unknown product",
                quantity_sold=row["total_qty"],
                revenue=row["total_rev"],
            )
            for row in rows
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
            SalesByPaymentMethod(method=row["method"], count=row["count"], total=row["total"])
            for row in payments
        ]

    def get_daily_sales(self, date_from: date, date_to: date) -> list[DailySales]:
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

    def get_cashier_sales(self, date_from: date, date_to: date) -> list[CashierSales]:
        names = self._cashier_names()
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .values("cashier_id")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("-total")
        )
        return [
            CashierSales(
                cashier_id=row["cashier_id"],
                cashier_name=names.get(row["cashier_id"], ""),
                transaction_count=row["count"],
                total=row["total"],
            )
            for row in sales
        ]

    def get_sales_report(self, date_from: date, date_to: date) -> list[SalesReportRow]:
        names = self._cashier_names()
        sales = SaleModel.objects.filter(created_at__date__range=(date_from, date_to)).order_by(
            "-created_at"
        )
        rows = []
        for sale in sales:
            for payment in sale.payments.all():
                rows.append(
                    SalesReportRow(
                        receipt_number=sale.receipt_number,
                        date=sale.created_at,
                        cashier_name=names.get(sale.cashier_id, ""),
                        total=sale.total,
                        payment_method=payment.method,
                        status=sale.status,
                    )
                )
        return rows

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
