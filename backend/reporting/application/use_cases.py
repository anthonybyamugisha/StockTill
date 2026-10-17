from datetime import date

from reporting.application.queries import (
    CashierSales,
    DailySales,
    SalesByPaymentMethod,
    SalesSummary,
    TopProduct,
)
from shared.domain.money import Money


class GetSalesSummaryUseCase:
    def __init__(self, sales_query):
        self._query = sales_query

    def execute(self, date_from: date, date_to: date) -> SalesSummary:
        return self._query.get_sales_summary(date_from, date_to)


class GetTopProductsUseCase:
    def __init__(self, sales_query):
        self._query = sales_query

    def execute(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]:
        return self._query.get_top_products(date_from, date_to, limit)


class GetSalesByPaymentMethodUseCase:
    def __init__(self, sales_query):
        self._query = sales_query

    def execute(self, date_from: date, date_to: date) -> list[SalesByPaymentMethod]:
        return self._query.get_sales_by_payment_method(date_from, date_to)


class GetDailySalesUseCase:
    def __init__(self, sales_query):
        self._query = sales_query

    def execute(self, date_from: date, date_to: date) -> list[DailySales]:
        return self._query.get_daily_sales(date_from, date_to)


class GetCashierSalesUseCase:
    def __init__(self, sales_query):
        self._query = sales_query

    def execute(self, date_from: date, date_to: date) -> list[CashierSales]:
        return self._query.get_cashier_sales(date_from, date_to)
