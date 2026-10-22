import base64
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx

from payments.application.ports import (
    CallbackEvent,
    GatewayOutcome,
    GatewayResult,
    PaymentGatewayPort,
)
from payments.domain.entities import PaymentIntent
from payments.domain.errors import GatewayError, InvalidCallbackError


class MTNMoMoGateway(PaymentGatewayPort):
    """MTN MoMo Collections API, using the request-to-pay flow."""

    def __init__(
        self,
        *,
        base_url: str,
        subscription_key: str,
        api_user: str,
        api_key: str,
        target_environment: str = "sandbox",
        callback_url: str = "",
        client: httpx.Client | None = None,
    ):
        base_url = base_url.rstrip("/")
        if base_url.endswith("/collection"):
            base_url = base_url[: -len("/collection")]
        self._base_url = base_url
        self._subscription_key = subscription_key
        self._api_user = api_user
        self._api_key = api_key
        self._target_environment = target_environment
        self._callback_url = callback_url
        self._client = client or httpx.Client(timeout=15)
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    def provider_name(self) -> str:
        return "mtn"

    def request_payment(self, intent: PaymentIntent) -> GatewayResult:
        reference = str(uuid4())
        headers = {
            **self._auth_headers(),
            "X-Reference-Id": reference,
            "X-Target-Environment": self._target_environment,
            "Content-Type": "application/json",
        }
        if self._callback_url:
            headers["X-Callback-Url"] = self._callback_url

        payload = {
            "amount": f"{intent.amount.amount:.2f}",
            "currency": intent.amount.currency,
            "externalId": intent.tx_ref,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": intent.phone,
            },
            "payerMessage": "StockTill sale",
            "payeeNote": "StockTill",
        }

        response = self._post("/collection/v1_0/requesttopay", headers=headers, json=payload)
        if response.status_code in {200, 201, 202}:
            return GatewayResult(
                provider="mtn",
                reference=reference,
                status=GatewayOutcome.PENDING,
            )
        if response.status_code == 409:
            return GatewayResult(
                provider="mtn",
                reference=reference,
                status=GatewayOutcome.PENDING,
                message="MTN MoMo already has this request",
            )
        raise GatewayError(self._error_message(response, "MTN MoMo rejected the payment request"))

    def verify(self, intent: PaymentIntent) -> GatewayResult:
        if not intent.gateway_reference:
            raise GatewayError("The MTN MoMo request has no reference to check")

        response = self._get(
            f"/collection/v1_0/requesttopay/{intent.gateway_reference}",
            headers={
                **self._auth_headers(),
                "X-Target-Environment": self._target_environment,
            },
        )
        if response.status_code == 404:
            return GatewayResult(
                provider="mtn",
                reference=intent.gateway_reference,
                status=GatewayOutcome.FAILED,
                message="MTN MoMo could not find the payment request",
            )
        if response.status_code != 200:
            raise GatewayError(
                self._error_message(response, "MTN MoMo could not check the payment")
            )

        data = response.json()
        return GatewayResult(
            provider="mtn",
            reference=intent.gateway_reference,
            status=self._outcome(str(data.get("status", ""))),
            message=self._reason_message(data.get("reason")),
            amount=self._decimal(data.get("amount")),
            currency=data.get("currency"),
        )

    def parse_callback(self, *, payload: dict[str, Any], query: dict[str, str]) -> CallbackEvent:
        tx_ref = str(
            payload.get("externalId") or payload.get("tx_ref") or query.get("tx_ref") or ""
        )
        if not tx_ref:
            raise InvalidCallbackError("The MTN MoMo callback did not identify a payment")

        return CallbackEvent(
            tx_ref=tx_ref,
            reference=payload.get("referenceId") or payload.get("reference"),
            status=self._outcome(str(payload.get("status", ""))),
            amount=self._decimal(payload.get("amount")),
            currency=payload.get("currency"),
            message=self._reason_message(payload.get("reason") or payload.get("message")),
        )

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Ocp-Apim-Subscription-Key": self._subscription_key,
        }

    def _access_token(self) -> str:
        now = datetime.now(UTC)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token

        credentials = base64.b64encode(f"{self._api_user}:{self._api_key}".encode()).decode()
        response = self._post(
            "/collection/token/",
            headers={
                "Authorization": f"Basic {credentials}",
                "Ocp-Apim-Subscription-Key": self._subscription_key,
            },
        )
        if response.status_code != 200:
            raise GatewayError(
                self._error_message(response, "MTN MoMo rejected the API credentials")
            )

        data = response.json()
        token = data.get("access_token")
        if not token:
            raise GatewayError("MTN MoMo did not return an access token")

        expires_in = int(data.get("expires_in") or 3600)
        self._token = str(token)
        self._token_expires_at = now + timedelta(seconds=max(60, expires_in - 60))
        return self._token

    def _post(
        self,
        path: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            return self._client.post(f"{self._base_url}{path}", headers=headers, json=json)
        except httpx.HTTPError as error:
            raise GatewayError("Could not reach MTN MoMo") from error

    def _get(self, path: str, *, headers: dict[str, str]) -> httpx.Response:
        try:
            return self._client.get(f"{self._base_url}{path}", headers=headers)
        except httpx.HTTPError as error:
            raise GatewayError("Could not reach MTN MoMo") from error

    @staticmethod
    def _outcome(raw_status: str) -> GatewayOutcome:
        status = raw_status.upper()
        if status in {"SUCCESSFUL", "SUCCESS", "PAID"}:
            return GatewayOutcome.SUCCESSFUL
        if status in {"FAILED", "REJECTED", "CANCELLED", "TIMEOUT"}:
            return GatewayOutcome.FAILED
        return GatewayOutcome.PENDING

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (ArithmeticError, ValueError):
            return None

    @staticmethod
    def _reason_message(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("message") or value.get("code") or "")
        return str(value or "")

    @staticmethod
    def _error_message(response: httpx.Response, fallback: str) -> str:
        try:
            data = response.json()
        except ValueError:
            data = None
        if isinstance(data, dict):
            message = data.get("message") or data.get("error") or data.get("detail")
            if message:
                return str(message)
        text = response.text.strip()
        return text[:200] if text else fallback
