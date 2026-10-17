from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("accounts.interfaces.api.urls")),
    path("api/v1/catalog/", include("catalog.interfaces.api.urls")),
    path("api/v1/inventory/", include("inventory.interfaces.api.urls")),
    path("api/v1/sales/", include("sales.interfaces.api.urls")),
    path("api/v1/reporting/", include("reporting.interfaces.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
