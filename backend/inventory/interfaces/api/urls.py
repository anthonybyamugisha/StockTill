from django.urls import path

from inventory.interfaces.api.views import (
    InventoryValuationView,
    LowStockView,
    OutOfStockView,
    RebuildStockCacheView,
    StockAdjustmentView,
    StockHistoryView,
    StockItemDetailView,
    StockItemListView,
)

urlpatterns = [
    path("adjust/", StockAdjustmentView.as_view(), name="stock-adjust"),
    path("items/", StockItemListView.as_view(), name="stock-item-list"),
    path("items/<uuid:product_id>/", StockItemDetailView.as_view(), name="stock-item-detail"),
    path("history/<uuid:product_id>/", StockHistoryView.as_view(), name="stock-history"),
    path("low-stock/", LowStockView.as_view(), name="low-stock"),
    path("out-of-stock/", OutOfStockView.as_view(), name="out-of-stock"),
    path("valuation/", InventoryValuationView.as_view(), name="inventory-valuation"),
    path("rebuild-cache/", RebuildStockCacheView.as_view(), name="rebuild-stock-cache"),
]
