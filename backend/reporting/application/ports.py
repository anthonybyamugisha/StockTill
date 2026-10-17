from datetime import date
from typing import Protocol

from reporting.application.queries import (
    CashierSales,
    DailySales,
    SalesByPaymentMethod,
    SalesSummary,
    TopProduct,
)


class SalesQueryPort(Protocol):
    def get_sales_summary(self, date_from: date, date_to: date) -> SalesSummary: ...

    def get_top_products(
        self, date_from: date, date_to: date, limit: int = 10
    ) -> list[TopProduct]: ...

    def get_sales_by_payment_method(
        self, date_from: date, date_to: date
    ) -> list[SalesByPaymentMethod]: ...

    def get_daily_sales(self, date_from: date, date_to: date) -> list[DailySales]: ...

    def get_cashier_sales(self, date_from: date, date_to: date) -> list[CashierSales]: ...
