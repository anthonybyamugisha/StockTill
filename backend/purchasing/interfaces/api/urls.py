from django.urls import path

from purchasing.interfaces.api.views import (
    PurchaseOrderCancelView,
    PurchaseOrderDetailView,
    PurchaseOrderListCreateView,
    PurchaseOrderOrderView,
    PurchaseOrderReceiveView,
    SupplierDetailView,
    SupplierInvoiceDetailView,
    SupplierInvoiceListCreateView,
    SupplierInvoicePaymentView,
    SupplierInvoiceVoidView,
    SupplierListCreateView,
)

urlpatterns = [
    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("suppliers/<uuid:supplier_id>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path("invoices/", SupplierInvoiceListCreateView.as_view(), name="supplier-invoice-list-create"),
    path(
        "invoices/<uuid:invoice_id>/",
        SupplierInvoiceDetailView.as_view(),
        name="supplier-invoice-detail",
    ),
    path(
        "invoices/<uuid:invoice_id>/payments/",
        SupplierInvoicePaymentView.as_view(),
        name="supplier-invoice-payment",
    ),
    path(
        "invoices/<uuid:invoice_id>/void/",
        SupplierInvoiceVoidView.as_view(),
        name="supplier-invoice-void",
    ),
    path("orders/", PurchaseOrderListCreateView.as_view(), name="purchase-order-list-create"),
    path(
        "orders/<uuid:purchase_order_id>/",
        PurchaseOrderDetailView.as_view(),
        name="purchase-order-detail",
    ),
    path(
        "orders/<uuid:purchase_order_id>/order/",
        PurchaseOrderOrderView.as_view(),
        name="purchase-order-order",
    ),
    path(
        "orders/<uuid:purchase_order_id>/receive/",
        PurchaseOrderReceiveView.as_view(),
        name="purchase-order-receive",
    ),
    path(
        "orders/<uuid:purchase_order_id>/cancel/",
        PurchaseOrderCancelView.as_view(),
        name="purchase-order-cancel",
    ),
]
