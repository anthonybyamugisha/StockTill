import json
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
from payments.infrastructure.gateways.airtel_signing import sign_payload


class AirtelMoneyGateway(PaymentGatewayPort):
    """Airtel Money Collections API, using the merchant payment flow."""

    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        country: str = "UG",
        currency: str = "UGX",
        callback_url: str = "",
        simulate: bool = False,
        sign_requests: bool = True,
        client: httpx.Client | None = None,
    ):
        base_url = base_url.rstrip("/")
        if base_url.endswith("/simulate"):
            base_url = base_url[: -len("/simulate")]
        self._base_url = base_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._country = country
        self._currency = currency
        self._callback_url = callback_url
        self._simulate = simulate
        self._sign_requests = sign_requests
        self._client = client or httpx.Client(timeout=15)
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._public_key: str | None = None

    def provider_name(self) -> str:
        return "airtel"

    def request_payment(self, intent: PaymentIntent) -> GatewayResult:
        reference = str(uuid4())
        headers = {
            **self._auth_headers(),
            "X-Country": self._country,
            "X-Currency": self._currency,
            "Content-Type": "application/json",
        }
        if self._callback_url:
            headers["X-Callback-Url"] = self._callback_url

        payload = {
            "reference": intent.tx_ref,
            "subscriber": {
                "country": self._country,
                "currency": self._currency,
                "msisdn": intent.phone,
            },
            "transaction": {
                "amount": f"{intent.amount.amount:.2f}",
                "country": self._country,
                "currency": self._currency,
                "id": reference,
            },
        }

        if self._sign_requests:
            try:
                signed = sign_payload(self._encryption_key(), payload)
            except (TypeError, ValueError) as error:
                raise GatewayError("Could not sign the Airtel Money request") from error
            headers.update(signed.headers)
            body = signed.body
        else:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        response = self._post(self._path("/merchant/v2/payments/"), headers=headers, content=body)
        if response.status_code not in {200, 201, 202}:
            raise GatewayError(self._error_message(response, "Airtel Money rejected the request"))

        data = response.json()
        status = data.get("status") or {}
        code = str(status.get("code") or "")
        if code and code != "200":
            raise GatewayError(str(status.get("message") or "Airtel Money rejected the request"))

        transaction = (data.get("data") or {}).get("transaction") or {}
        return GatewayResult(
            provider="airtel",
            reference=str(transaction.get("id") or reference),
            status=GatewayOutcome.PENDING,
        )

    def verify(self, intent: PaymentIntent) -> GatewayResult:
        if not intent.gateway_reference:
            raise GatewayError("The Airtel Money request has no reference to check")

        response = self._get(
            self._path(f"/standard/v1/payments/{intent.gateway_reference}"),
            headers={
                **self._auth_headers(),
                "X-Country": self._country,
                "X-Currency": self._currency,
            },
        )
        if response.status_code == 404:
            return GatewayResult(
                provider="airtel",
                reference=intent.gateway_reference,
                status=GatewayOutcome.FAILED,
                message="Airtel Money could not find the payment request",
            )
        if response.status_code != 200:
            raise GatewayError(
                self._error_message(response, "Airtel Money could not check the payment")
            )

        data = response.json()
        transaction = (data.get("data") or {}).get("transaction") or {}
        return GatewayResult(
            provider="airtel",
            reference=str(transaction.get("id") or intent.gateway_reference),
            status=self._outcome(
                str(transaction.get("status") or transaction.get("status_code") or "")
            ),
            message=str(
                transaction.get("message") or (data.get("status") or {}).get("message") or ""
            ),
            amount=self._decimal(transaction.get("amount")),
            currency=transaction.get("currency"),
        )

    def parse_callback(self, *, payload: dict[str, Any], query: dict[str, str]) -> CallbackEvent:
        transaction = payload.get("transaction") or {}
        tx_ref = str(
            payload.get("reference")
            or payload.get("tx_ref")
            or transaction.get("reference")
            or query.get("tx_ref")
            or ""
        )
        if not tx_ref:
            raise InvalidCallbackError("The Airtel Money callback did not identify a payment")

        return CallbackEvent(
            tx_ref=tx_ref,
            reference=transaction.get("id") or transaction.get("airtel_money_id"),
            status=self._outcome(
                str(
                    transaction.get("status")
                    or transaction.get("status_code")
                    or payload.get("status")
                    or ""
                )
            ),
            amount=self._decimal(transaction.get("amount") or payload.get("amount")),
            currency=transaction.get("currency") or payload.get("currency"),
            message=str(transaction.get("message") or payload.get("message") or ""),
        )

    def _path(self, path: str) -> str:
        return f"/simulate{path}" if self._simulate else path

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token()}"}

    def _encryption_key(self) -> str:
        if self._public_key:
            return self._public_key

        response = self._get(
            "/v1/rsa/encryption-keys",
            headers={
                **self._auth_headers(),
                "X-Country": self._country,
                "X-Currency": self._currency,
            },
        )
        if response.status_code != 200:
            raise GatewayError(
                self._error_message(response, "Airtel Money did not provide a signing key")
            )

        data = response.json()
        key = (data.get("data") or {}).get("key")
        if not key:
            raise GatewayError("Airtel Money did not provide a signing key")

        self._public_key = str(key)
        return self._public_key

    def _access_token(self) -> str:
        now = datetime.now(UTC)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token

        response = self._post(
            "/auth/oauth2/token",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )
        if response.status_code not in {200, 201}:
            raise GatewayError(
                self._error_message(response, "Airtel Money rejected the API credentials")
            )

        data = response.json()
        token = data.get("access_token")
        if not token:
            raise GatewayError("Airtel Money did not return an access token")

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
        content: bytes | None = None,
    ) -> httpx.Response:
        try:
            return self._client.post(
                f"{self._base_url}{path}",
                headers=headers,
                json=json,
                content=content,
            )
        except httpx.HTTPError as error:
            raise GatewayError("Could not reach Airtel Money") from error

    def _get(self, path: str, *, headers: dict[str, str]) -> httpx.Response:
        try:
            return self._client.get(f"{self._base_url}{path}", headers=headers)
        except httpx.HTTPError as error:
            raise GatewayError("Could not reach Airtel Money") from error

    @staticmethod
    def _outcome(raw_status: str) -> GatewayOutcome:
        status = raw_status.upper()
        if status in {"TS", "SUCCESS", "SUCCESSFUL", "PAID"}:
            return GatewayOutcome.SUCCESSFUL
        if status in {"TF", "FAILED", "FAILURE", "REJECTED", "CANCELLED"}:
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
    def _error_message(response: httpx.Response, fallback: str) -> str:
        try:
            data = response.json()
        except ValueError:
            data = None
        if isinstance(data, dict):
            status = data.get("status")
            if isinstance(status, dict):
                message = status.get("message") or status.get("code")
                if message:
                    return str(message)
            message = data.get("message") or data.get("error") or data.get("detail")
            if message:
                return str(message)
        text = response.text.strip()
        return text[:200] if text else fallback
