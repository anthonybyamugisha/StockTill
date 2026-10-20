from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health"),
    path("api/v1/accounts/", include("accounts.interfaces.api.urls")),
    path("api/v1/catalog/", include("catalog.interfaces.api.urls")),
    path("api/v1/inventory/", include("inventory.interfaces.api.urls")),
    path("api/v1/sales/", include("sales.interfaces.api.urls")),
    path("api/v1/payments/", include("payments.interfaces.api.urls")),
    path("api/v1/shifts/", include("shifts.interfaces.api.urls")),
    path("api/v1/purchasing/", include("purchasing.interfaces.api.urls")),
    path("api/v1/reporting/", include("reporting.interfaces.api.urls")),
    path("api/v1/settings/", include("settings.interfaces.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
