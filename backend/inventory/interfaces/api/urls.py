from django.urls import path

from inventory.interfaces.api.views import (
    LowStockView,
    OutOfStockView,
    StockAdjustmentView,
    StockItemDetailView,
)

urlpatterns = [
    path("adjust/", StockAdjustmentView.as_view(), name="stock-adjust"),
    path("items/<uuid:product_id>/", StockItemDetailView.as_view(), name="stock-item-detail"),
    path("low-stock/", LowStockView.as_view(), name="low-stock"),
    path("out-of-stock/", OutOfStockView.as_view(), name="out-of-stock"),
]
