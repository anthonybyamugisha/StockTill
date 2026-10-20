from decimal import Decimal
from typing import Any

from payments.application.ports import (
    CallbackEvent,
    GatewayOutcome,
    GatewayResult,
    PaymentGatewayPort,
)
from payments.domain.entities import PaymentIntent
from payments.domain.errors import InvalidCallbackError


class FakeGateway(PaymentGatewayPort):
    """A gateway that never leaves the process, for development and tests."""

    def __init__(
        self,
        provider: str = "fake",
        request_outcome: GatewayOutcome = GatewayOutcome.PENDING,
        verify_outcome: GatewayOutcome = GatewayOutcome.SUCCESSFUL,
        message: str = "",
    ):
        self._provider = provider
        self._request_outcome = request_outcome
        self._verify_outcome = verify_outcome
        self._message = message

    def provider_name(self) -> str:
        return self._provider

    def request_payment(self, intent: PaymentIntent) -> GatewayResult:
        return GatewayResult(
            provider=self._provider,
            reference=f"fake-{intent.tx_ref}",
            status=self._request_outcome,
            message=self._message,
        )

    def verify(self, intent: PaymentIntent) -> GatewayResult:
        return GatewayResult(
            provider=self._provider,
            reference=intent.gateway_reference,
            status=self._verify_outcome,
            message=self._message,
            amount=intent.amount.amount,
            currency=intent.amount.currency,
        )

    def parse_callback(self, *, payload: dict[str, Any], query: dict[str, str]) -> CallbackEvent:
        tx_ref = str(payload.get("tx_ref") or query.get("tx_ref") or "")
        if not tx_ref:
            raise InvalidCallbackError("The callback did not identify a payment")
        raw_status = str(payload.get("status") or "pending").lower()
        try:
            status = GatewayOutcome(raw_status)
        except ValueError as error:
            raise InvalidCallbackError(f"Unknown callback status {raw_status}") from error
        amount = payload.get("amount")
        return CallbackEvent(
            tx_ref=tx_ref,
            reference=payload.get("reference"),
            status=status,
            amount=Decimal(str(amount)) if amount is not None else None,
            currency=payload.get("currency"),
            message=str(payload.get("message") or ""),
        )
