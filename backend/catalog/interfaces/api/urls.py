from django.urls import path

from catalog.interfaces.api.views import ProductListCreateView, ProductSearchView

urlpatterns = [
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/search/", ProductSearchView.as_view(), name="product-search"),
]
