from django.urls import path

from reporting.interfaces.api.views import (
    CashierSalesView,
    DailySalesView,
    SalesByPaymentMethodView,
    SalesSummaryView,
    TopProductsView,
)

urlpatterns = [
    path("sales-summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("top-products/", TopProductsView.as_view(), name="top-products"),
    path("by-payment-method/", SalesByPaymentMethodView.as_view(), name="by-payment-method"),
    path("daily-sales/", DailySalesView.as_view(), name="daily-sales"),
    path("cashier-sales/", CashierSalesView.as_view(), name="cashier-sales"),
]
