from django.urls import path

from reporting.interfaces.api.views import (
    CashierSalesView,
    DailySalesView,
    DashboardView,
    InventoryReportView,
    LowStockReportView,
    ProfitReportView,
    SalesByPaymentMethodView,
    SalesReportCSVView,
    SalesReportView,
    SalesSummaryView,
    TopProductsView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("sales-summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("top-products/", TopProductsView.as_view(), name="top-products"),
    path("by-payment-method/", SalesByPaymentMethodView.as_view(), name="by-payment-method"),
    path("daily-sales/", DailySalesView.as_view(), name="daily-sales"),
    path("cashier-sales/", CashierSalesView.as_view(), name="cashier-sales"),
    path("profit/", ProfitReportView.as_view(), name="profit-report"),
    path("inventory/", InventoryReportView.as_view(), name="inventory-report"),
    path("sales-report/", SalesReportView.as_view(), name="sales-report"),
    path("sales-report/csv/", SalesReportCSVView.as_view(), name="sales-report-csv"),
    path("low-stock/", LowStockReportView.as_view(), name="low-stock-report"),
]
