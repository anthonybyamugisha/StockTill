from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import UUID

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentStatus
from payments.domain.errors import (
    GatewayError,
    GatewayNotConfiguredError,
    PaymentIntentNotFoundError,
)
from payments.interfaces.api.container import (
    build_callback_use_case,
    build_cancel_intent_use_case,
    build_create_intent_use_case,
    build_get_intent_use_case,
    build_list_intents_use_case,
)
from payments.interfaces.api.request_mapping import (
    to_cancel_intent_command,
    to_create_intent_command,
)
from payments.interfaces.api.serializers import (
    CancelPaymentIntentSerializer,
    CreatePaymentIntentSerializer,
    PaymentIntentSerializer,
)
from sales.application.discount_policy import assert_discount_within_limit
from sales.interfaces.api.discount_limits import cashier_discount_limit
from sales.interfaces.api.request_mapping import to_line_item
from shared.domain.errors import DomainError


def _payment_errors(view_method: Callable[..., Response]) -> Callable[..., Response]:
    @wraps(view_method)
    def wrapper(view: APIView, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return view_method(view, request, *args, **kwargs)
        except PaymentIntentNotFoundError as error:
            return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
        except GatewayNotConfiguredError as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GatewayError as error:
            return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
        except (ValueError, DomainError) as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    return wrapper


def _is_manager(request: Request) -> bool:
    return getattr(request.user, "role", "") in ("admin", "manager")


def _may_view(request: Request, intent: PaymentIntent) -> bool:
    return _is_manager(request) or intent.cashier_id == request.user.id


class PaymentIntentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            raw_status = request.query_params.get("status")
            status_filter = PaymentStatus(raw_status) if raw_status else None
        except ValueError:
            return Response(
                {"detail": f"Unknown payment status {raw_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cashier_id = (
            UUID(request.query_params["cashier_id"])
            if request.query_params.get("cashier_id") and _is_manager(request)
            else None
        )
        if not _is_manager(request):
            cashier_id = request.user.id
        intents = build_list_intents_use_case().execute(status=status_filter, cashier_id=cashier_id)
        return Response(PaymentIntentSerializer(intents, many=True).data)

    @_payment_errors
    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = to_create_intent_command(serializer.validated_data, cashier_id=request.user.id)
        max_discount_percent = cashier_discount_limit(request.user)
        if max_discount_percent is not None:
            lines = [to_line_item(line) for line in command.sale_payload.get("lines", [])]
            assert_discount_within_limit(lines, max_discount_percent)
        intent = build_create_intent_use_case().execute(command)
        return Response(PaymentIntentSerializer(intent).data, status=status.HTTP_201_CREATED)


class PaymentIntentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @_payment_errors
    def get(self, request, intent_id):
        intent = build_get_intent_use_case().execute(intent_id)
        if not _may_view(request, intent):
            raise PaymentIntentNotFoundError("Payment not found")
        return Response(PaymentIntentSerializer(intent).data)


class PaymentIntentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @_payment_errors
    def post(self, request, intent_id):
        intent = build_get_intent_use_case().execute(intent_id)
        if not _may_view(request, intent):
            raise PaymentIntentNotFoundError("Payment not found")
        serializer = CancelPaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cancelled = build_cancel_intent_use_case().execute(
            to_cancel_intent_command(
                serializer.validated_data,
                intent_id=intent_id,
                actor_id=request.user.id,
            )
        )
        return Response(PaymentIntentSerializer(cancelled).data)


class MobileMoneyCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[Any] = []

    def post(self, request, network):
        return self._handle_callback(request, network)

    def put(self, request, network):
        return self._handle_callback(request, network)

    def _handle_callback(self, request, network):
        secret = getattr(settings, "PAYMENTS_CALLBACK_SECRET", "")
        if secret and request.query_params.get("token") != secret:
            return Response({"detail": "Invalid callback token"}, status=status.HTTP_403_FORBIDDEN)
        try:
            mobile_network = MobileNetwork(network)
        except ValueError:
            return Response(
                {"detail": f"Unknown mobile network {network}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        payload = request.data if isinstance(request.data, dict) else {}
        query = {key: value for key, value in request.query_params.items()}
        try:
            intent = build_callback_use_case().execute(
                network=mobile_network, payload=payload, query=query
            )
        except PaymentIntentNotFoundError as error:
            return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
        except GatewayNotConfiguredError as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GatewayError as error:
            return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
        except (ValueError, DomainError) as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": intent.status.value, "tx_ref": intent.tx_ref})
