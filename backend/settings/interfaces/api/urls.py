from django.urls import path

from settings.interfaces.api.views import SettingsView

urlpatterns = [
    path("", SettingsView.as_view(), name="settings"),
]
