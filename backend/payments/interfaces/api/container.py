from django.conf import settings

from payments.application.use_cases import (
    CancelPaymentIntentUseCase,
    ConfirmPaymentUseCase,
    CreatePaymentIntentUseCase,
    GetPaymentIntentUseCase,
    HandleGatewayCallbackUseCase,
    ListPaymentIntentsUseCase,
)
from payments.infrastructure.gateways.registry import build_gateway_registry
from payments.infrastructure.repository import DjangoPaymentIntentRepository
from payments.infrastructure.sales_adapter import SalesCompletionAdapter
from shared.domain.clock import SystemClock
from shared.infrastructure.audit import build_audit_recorder


def build_create_intent_use_case() -> CreatePaymentIntentUseCase:
    return CreatePaymentIntentUseCase(
        DjangoPaymentIntentRepository(),
        build_gateway_registry(),
        SystemClock(),
        build_audit_recorder(),
        ttl_seconds=settings.PAYMENTS_INTENT_TTL_SECONDS,
    )


def build_confirm_payment_use_case() -> ConfirmPaymentUseCase:
    return ConfirmPaymentUseCase(
        DjangoPaymentIntentRepository(),
        SalesCompletionAdapter(),
        SystemClock(),
        build_audit_recorder(),
    )


def build_cancel_intent_use_case() -> CancelPaymentIntentUseCase:
    return CancelPaymentIntentUseCase(
        DjangoPaymentIntentRepository(),
        SystemClock(),
        build_audit_recorder(),
    )


def build_get_intent_use_case() -> GetPaymentIntentUseCase:
    return GetPaymentIntentUseCase(DjangoPaymentIntentRepository())


def build_list_intents_use_case() -> ListPaymentIntentsUseCase:
    return ListPaymentIntentsUseCase(DjangoPaymentIntentRepository())


def build_callback_use_case() -> HandleGatewayCallbackUseCase:
    return HandleGatewayCallbackUseCase(
        DjangoPaymentIntentRepository(),
        build_gateway_registry(),
        build_confirm_payment_use_case(),
    )
