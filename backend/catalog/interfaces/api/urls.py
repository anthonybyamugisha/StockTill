from django.urls import path

from catalog.interfaces.api.views import (
    CategoryDetailView,
    CategoryListCreateView,
    ProductByBarcodeView,
    ProductDetailView,
    ProductListCreateView,
)

urlpatterns = [
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path(
        "products/by-barcode/",
        ProductByBarcodeView.as_view(),
        name="product-by-barcode",
    ),
    path("products/<uuid:product_id>/", ProductDetailView.as_view(), name="product-detail"),
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path(
        "categories/<uuid:category_id>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
]
