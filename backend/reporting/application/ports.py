from datetime import date
from typing import Protocol

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


class SalesSummaryQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> SalesSummary: ...


class TopProductsQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]: ...


class PaymentMethodSalesQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> list[SalesByPaymentMethod]: ...


class DailySalesQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> list[DailySales]: ...


class CashierSalesQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> list[CashierSales]: ...


class ProfitReportQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> list[ProfitReport]: ...


class SalesReportQueryPort(Protocol):
    def execute(self, date_from: date, date_to: date) -> list[SalesReportRow]: ...


class DashboardQueryPort(Protocol):
    def execute(self) -> DashboardStats: ...


class InventoryReportQueryPort(Protocol):
    def execute(self) -> InventoryReport: ...


class LowStockQueryPort(Protocol):
    def execute(self) -> list[LowStockItem]: ...
