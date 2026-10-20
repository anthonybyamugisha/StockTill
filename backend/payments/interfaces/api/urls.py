from django.urls import path

from payments.interfaces.api.views import (
    MobileMoneyCallbackView,
    PaymentIntentCancelView,
    PaymentIntentDetailView,
    PaymentIntentListCreateView,
)

urlpatterns = [
    path("intents/", PaymentIntentListCreateView.as_view(), name="payment-intent-list-create"),
    path(
        "intents/<uuid:intent_id>/",
        PaymentIntentDetailView.as_view(),
        name="payment-intent-detail",
    ),
    path(
        "intents/<uuid:intent_id>/cancel/",
        PaymentIntentCancelView.as_view(),
        name="payment-intent-cancel",
    ),
    path(
        "callbacks/<str:network>/",
        MobileMoneyCallbackView.as_view(),
        name="payment-callback",
    ),
]
