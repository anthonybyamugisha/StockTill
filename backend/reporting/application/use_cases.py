from datetime import date

from reporting.application.ports import (
    CashierSalesQueryPort,
    DailySalesQueryPort,
    DashboardQueryPort,
    InventoryReportQueryPort,
    LowStockQueryPort,
    PaymentMethodSalesQueryPort,
    ProfitReportQueryPort,
    SalesReportQueryPort,
    SalesSummaryQueryPort,
    TopProductsQueryPort,
)
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


class GetSalesSummaryUseCase:
    def __init__(self, sales_summary: SalesSummaryQueryPort):
        self._sales_summary = sales_summary

    def execute(self, date_from: date, date_to: date) -> SalesSummary:
        return self._sales_summary.execute(date_from, date_to)


class GetTopProductsUseCase:
    def __init__(self, top_products: TopProductsQueryPort):
        self._top_products = top_products

    def execute(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]:
        return self._top_products.execute(date_from, date_to, limit)


class GetSalesByPaymentMethodUseCase:
    def __init__(self, payment_methods: PaymentMethodSalesQueryPort):
        self._payment_methods = payment_methods

    def execute(self, date_from: date, date_to: date) -> list[SalesByPaymentMethod]:
        return self._payment_methods.execute(date_from, date_to)


class GetDailySalesUseCase:
    def __init__(self, daily_sales: DailySalesQueryPort):
        self._daily_sales = daily_sales

    def execute(self, date_from: date, date_to: date) -> list[DailySales]:
        return self._daily_sales.execute(date_from, date_to)


class GetCashierSalesUseCase:
    def __init__(self, cashier_sales: CashierSalesQueryPort):
        self._cashier_sales = cashier_sales

    def execute(self, date_from: date, date_to: date) -> list[CashierSales]:
        return self._cashier_sales.execute(date_from, date_to)


class GetProfitReportUseCase:
    def __init__(self, profit_report: ProfitReportQueryPort):
        self._profit_report = profit_report

    def execute(self, date_from: date, date_to: date) -> list[ProfitReport]:
        return self._profit_report.execute(date_from, date_to)


class GetSalesReportUseCase:
    def __init__(self, sales_report: SalesReportQueryPort):
        self._sales_report = sales_report

    def execute(self, date_from: date, date_to: date) -> list[SalesReportRow]:
        return self._sales_report.execute(date_from, date_to)


class GetDashboardStatsUseCase:
    def __init__(self, dashboard: DashboardQueryPort):
        self._dashboard = dashboard

    def execute(self) -> DashboardStats:
        return self._dashboard.execute()


class GetInventoryReportUseCase:
    def __init__(self, inventory_report: InventoryReportQueryPort):
        self._inventory_report = inventory_report

    def execute(self) -> InventoryReport:
        return self._inventory_report.execute()


class GetLowStockItemsUseCase:
    def __init__(self, low_stock: LowStockQueryPort):
        self._low_stock = low_stock

    def execute(self) -> list[LowStockItem]:
        return self._low_stock.execute()
