import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from payments.application.ports import GatewayOutcome
from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentMethod
from payments.domain.errors import GatewayError
from payments.infrastructure.gateways.mtn import MTNMoMoGateway
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


def _intent(*, gateway_reference: str | None = None) -> PaymentIntent:
    intent = PaymentIntent.create(
        tx_ref="PAY-MTN-1",
        idempotency_key="key-mtn-1",
        cashier_id=uuid4(),
        shift_id=None,
        method=PaymentMethod.MOBILE_MONEY,
        amount=Money(Decimal("50000")),
        phone="256772123456",
        network=MobileNetwork.MTN,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    if gateway_reference:
        intent.attach_gateway(
            provider="mtn",
            gateway_reference=gateway_reference,
            at=NOW,
        )
    return intent


def _gateway(handler, **overrides) -> MTNMoMoGateway:
    values = {
        "base_url": "https://mtn.test",
        "subscription_key": "sub-key",
        "api_user": "api-user",
        "api_key": "api-key",
        "target_environment": "sandbox",
        "callback_url": "https://stocktill.test/api/v1/payments/callbacks/mtn/",
    }
    values.update(overrides)
    return MTNMoMoGateway(
        **values,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_request_payment_asks_mtn_to_charge_the_customer():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/collection/token/":
            assert request.headers["Authorization"].startswith("Basic ")
            assert request.headers["Ocp-Apim-Subscription-Key"] == "sub-key"
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/collection/v1_0/requesttopay":
            return httpx.Response(202)
        return httpx.Response(404)

    gateway = _gateway(handler)
    result = gateway.request_payment(_intent())

    assert result.status == GatewayOutcome.PENDING
    assert result.provider == "mtn"
    assert result.reference

    charge = requests[1]
    assert charge.headers["Authorization"] == "Bearer token-1"
    assert charge.headers["X-Reference-Id"] == result.reference
    assert charge.headers["X-Target-Environment"] == "sandbox"
    assert charge.headers["X-Callback-Url"].endswith("/payments/callbacks/mtn/")

    body = json.loads(charge.content)
    assert body["amount"] == "50000.00"
    assert body["currency"] == "UGX"
    assert body["externalId"] == "PAY-MTN-1"
    assert body["payer"] == {"partyIdType": "MSISDN", "partyId": "256772123456"}


def test_verify_reports_a_successful_payment():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/collection/token/":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/collection/v1_0/requesttopay/ref-1":
            return httpx.Response(
                200,
                json={
                    "status": "SUCCESSFUL",
                    "amount": "50000",
                    "currency": "UGX",
                    "reason": "",
                },
            )
        return httpx.Response(404)

    result = _gateway(handler).verify(_intent(gateway_reference="ref-1"))

    assert result.status == GatewayOutcome.SUCCESSFUL
    assert result.amount == Decimal("50000")
    assert result.currency == "UGX"


def test_verify_reports_a_failed_payment_with_the_reason():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/collection/token/":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(
            200,
            json={"status": "FAILED", "reason": "Insufficient funds"},
        )

    result = _gateway(handler).verify(_intent(gateway_reference="ref-1"))

    assert result.status == GatewayOutcome.FAILED
    assert result.message == "Insufficient funds"


def test_verify_reads_the_message_from_the_mtn_reason_object():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/collection/token/":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(
            200,
            json={
                "status": "FAILED",
                "reason": {
                    "code": "PAYMENT_NOT_APPROVED",
                    "message": "The payer did not approve the payment",
                },
            },
        )

    result = _gateway(handler).verify(_intent(gateway_reference="ref-1"))

    assert result.status == GatewayOutcome.FAILED
    assert result.message == "The payer did not approve the payment"


def test_verify_treats_a_missing_request_as_failed():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/collection/token/":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(404)

    result = _gateway(handler).verify(_intent(gateway_reference="ref-1"))

    assert result.status == GatewayOutcome.FAILED
    assert "could not find" in result.message


def test_callback_reads_the_external_id_and_status():
    event = _gateway(lambda request: httpx.Response(200)).parse_callback(
        payload={
            "externalId": "PAY-MTN-1",
            "referenceId": "ref-1",
            "status": "SUCCESSFUL",
            "amount": "50000",
            "currency": "UGX",
        },
        query={},
    )

    assert event.tx_ref == "PAY-MTN-1"
    assert event.reference == "ref-1"
    assert event.status == GatewayOutcome.SUCCESSFUL
    assert event.amount == Decimal("50000")


def test_callback_reads_the_message_from_the_mtn_reason_object():
    event = _gateway(lambda request: httpx.Response(200)).parse_callback(
        payload={
            "externalId": "PAY-MTN-1",
            "referenceId": "ref-1",
            "status": "FAILED",
            "reason": {"code": "PAYER_NOT_FOUND", "message": "The payer was not found"},
        },
        query={},
    )

    assert event.status == GatewayOutcome.FAILED
    assert event.message == "The payer was not found"


def test_the_base_url_can_include_the_collection_segment():
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/collection/token/":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(202)

    result = _gateway(handler, base_url="https://mtn.test/collection").request_payment(_intent())

    assert result.status == GatewayOutcome.PENDING
    assert paths == ["/collection/token/", "/collection/v1_0/requesttopay"]


def test_a_rejected_token_raises_a_gateway_error():
    gateway = _gateway(lambda request: httpx.Response(401, json={"message": "Invalid credentials"}))

    with pytest.raises(GatewayError, match="Invalid credentials"):
        gateway.request_payment(_intent())


def test_the_token_is_reused_between_calls():
    token_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls
        if request.url.path == "/collection/token/":
            token_calls += 1
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/collection/v1_0/requesttopay/ref-1":
            return httpx.Response(200, json={"status": "PENDING"})
        return httpx.Response(202)

    gateway = _gateway(handler)
    intent = _intent(gateway_reference="ref-1")
    gateway.verify(intent)
    gateway.verify(intent)

    assert token_calls == 1
