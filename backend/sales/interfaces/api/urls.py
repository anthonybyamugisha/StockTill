from django.urls import path

from sales.interfaces.api.views import (
    RefundSaleView,
    SaleDetailView,
    SaleListCreateView,
    VoidSaleView,
)

urlpatterns = [
    path("", SaleListCreateView.as_view(), name="sale-list-create"),
    path("<uuid:sale_id>/", SaleDetailView.as_view(), name="sale-detail"),
    path("refund/", RefundSaleView.as_view(), name="sale-refund"),
    path("void/", VoidSaleView.as_view(), name="sale-void"),
]
