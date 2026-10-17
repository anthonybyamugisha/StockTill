from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

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
from sales.infrastructure.models import PaymentModel, SaleLineModel, SaleModel
from shared.domain.money import Money


class SalesQueryBuilder:
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
        lines = (
            SaleLineModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("product_id", "product_name")
            .annotate(total_qty=Sum("quantity"), total_rev=Sum(F("quantity") * F("unit_price")))
            .order_by("-total_qty")[:limit]
        )
        return [
            TopProduct(
                product_id=row["product_id"],
                product_name=row["product_name"],
                quantity_sold=row["total_qty"],
                revenue=row["total_rev"],
            )
            for row in lines
        ]

    def get_sales_by_payment_method(self, date_from: date, date_to: date) -> list[SalesByPaymentMethod]:
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
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"), total=Sum("total"))
            .order_by("day")
        )
        return [
            DailySales(date=row["day"], transaction_count=row["count"], total=row["total"])
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
                cashier_id=row["cashier_id"],
                cashier_name="",
                transaction_count=row["count"],
                total=row["total"],
            )
            for row in sales
        ]

    def get_sales_report(self, date_from: date, date_to: date) -> list[SalesReportRow]:
        sales = SaleModel.objects.filter(
            created_at__date__range=(date_from, date_to)
        ).order_by("-created_at")
        rows = []
        for sale in sales:
            for payment in sale.payments.all():
                rows.append(
                    SalesReportRow(
                        receipt_number=sale.receipt_number,
                        date=sale.created_at,
                        cashier_name="",
                        total=sale.total,
                        payment_method=payment.method,
                        status=sale.status,
                    )
                )
        return rows

    def get_profit_report(self, date_from: date, date_to: date) -> list[ProfitReport]:
        sales = (
            SaleModel.objects.filter(created_at__date__range=(date_from, date_to))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("total"), cost=Sum("subtotal") - Sum("total") + Sum("total"))
            .order_by("day")
        )
        return [
            ProfitReport(date=row["day"], total_revenue=row["revenue"], total_cost=row["cost"], gross_profit=row["revenue"] - row["cost"])
            for row in sales
        ]

    def get_dashboard_stats(self) -> DashboardStats:
        today = date.today()
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

        from inventory.infrastructure.models import StockItemModel
        from catalog.infrastructure.models import ProductModel

        low_stock = StockItemModel.objects.filter(
            product__minimum_stock_level__gt=0,
            quantity_on_hand__lte=F("product__minimum_stock_level"),
        ).count()
        out_of_stock = StockItemModel.objects.filter(quantity_on_hand=0).count()

        all_sales = SaleModel.objects.all()
        total_rev = sum((Money(s.total) for s in all_sales), Money.zero())
        avg_sale = total_rev.amount / len(all_sales) if all_sales else Decimal(0)

        month_cost = Money.zero()
        for sale in month_sales:
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

        total_products = ProductModel.objects.filter(is_active=True).count()
        items = StockItemModel.objects.select_related("product").all()
        total_value = Money.zero()
        for item in items:
            total_value = total_value.add(Money(item.product.buying_cost) * item.quantity_on_hand)

        low_stock = StockItemModel.objects.filter(
            product__minimum_stock_level__gt=0,
            quantity_on_hand__lte=F("product__minimum_stock_level"),
        ).count()
        out_of_stock = StockItemModel.objects.filter(quantity_on_hand=0).count()

        return InventoryReport(
            total_products=total_products,
            total_value=total_value.amount,
            low_stock_count=low_stock,
            out_of_stock_count=out_of_stock,
        )

    def get_low_stock_items(self) -> list[LowStockItem]:
        from inventory.infrastructure.models import StockItemModel

        items = StockItemModel.objects.filter(
            product__minimum_stock_level__gt=0,
            quantity_on_hand__lte=F("product__minimum_stock_level"),
        ).select_related("product")

        return [
            LowStockItem(
                product_id=item.product_id,
                product_name=item.product.name,
                sku=item.product.sku,
                quantity_on_hand=item.quantity_on_hand,
                minimum_level=item.product.minimum_stock_level,
            )
            for item in items
        ]
