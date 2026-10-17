from django.urls import path

from shifts.interfaces.api.views import (
    CashMovementView,
    CloseShiftView,
    CurrentShiftView,
    OpenShiftView,
    ShiftReportView,
)

urlpatterns = [
    path("current/", CurrentShiftView.as_view(), name="shift-current"),
    path("open/", OpenShiftView.as_view(), name="shift-open"),
    path("close/", CloseShiftView.as_view(), name="shift-close"),
    path("cash-movement/", CashMovementView.as_view(), name="shift-cash-movement"),
    path("<uuid:shift_id>/", ShiftReportView.as_view(), name="shift-report"),
]
