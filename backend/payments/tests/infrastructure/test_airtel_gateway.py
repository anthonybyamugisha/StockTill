import base64
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from payments.application.ports import GatewayOutcome
from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentMethod
from payments.domain.errors import GatewayError
from payments.infrastructure.gateways.airtel import AirtelMoneyGateway
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = base64.b64encode(
    PRIVATE_KEY.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
).decode()


def _encryption_key_response() -> httpx.Response:
    return httpx.Response(200, json={"data": {"key": PUBLIC_KEY}})


def _signed_body(request: httpx.Request) -> dict:
    key_material = (
        PRIVATE_KEY.decrypt(
            base64.b64decode(request.headers["x-key"]),
            asymmetric_padding.PKCS1v15(),
        )
        .decode()
        .split(":")
    )
    key, iv = (base64.b64decode(part) for part in key_material)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = (
        decryptor.update(base64.b64decode(request.headers["x-signature"])) + decryptor.finalize()
    )
    unpadder = padding.PKCS7(128).unpadder()
    body = unpadder.update(padded) + unpadder.finalize()
    assert body == request.content
    return json.loads(body)


def _intent(*, gateway_reference: str | None = None) -> PaymentIntent:
    intent = PaymentIntent.create(
        tx_ref="PAY-AIRTEL-1",
        idempotency_key="key-airtel-1",
        cashier_id=uuid4(),
        shift_id=None,
        method=PaymentMethod.MOBILE_MONEY,
        amount=Money(Decimal("50000")),
        phone="256752123456",
        network=MobileNetwork.AIRTEL,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    if gateway_reference:
        intent.attach_gateway(
            provider="airtel",
            gateway_reference=gateway_reference,
            at=NOW,
        )
    return intent


def _gateway(handler, **overrides) -> AirtelMoneyGateway:
    values = {
        "base_url": "https://airtel.test",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "country": "UG",
        "currency": "UGX",
        "callback_url": "https://stocktill.test/api/v1/payments/callbacks/airtel/",
    }
    values.update(overrides)
    return AirtelMoneyGateway(
        **values,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_request_payment_asks_airtel_to_charge_the_customer():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/auth/oauth2/token":
            assert json.loads(request.content)["grant_type"] == "client_credentials"
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/v1/rsa/encryption-keys":
            return _encryption_key_response()
        if request.url.path == "/merchant/v2/payments/":
            return httpx.Response(
                200,
                json={
                    "data": {"transaction": {"id": "airtel-ref-1", "status": "TIP"}},
                    "status": {"code": "200", "message": "Success"},
                },
            )
        return httpx.Response(404)

    gateway = _gateway(handler)
    result = gateway.request_payment(_intent())

    assert result.status == GatewayOutcome.PENDING
    assert result.provider == "airtel"
    assert result.reference == "airtel-ref-1"

    assert requests[1].url.path == "/v1/rsa/encryption-keys"
    charge = requests[2]
    assert charge.headers["Authorization"] == "Bearer token-1"
    assert charge.headers["X-Country"] == "UG"
    assert charge.headers["X-Currency"] == "UGX"
    assert charge.headers["X-Callback-Url"].endswith("/payments/callbacks/airtel/")
    assert charge.headers["x-signature"]
    assert charge.headers["x-key"]

    body = _signed_body(charge)
    assert body["reference"] == "PAY-AIRTEL-1"
    assert body["subscriber"] == {
        "country": "UG",
        "currency": "UGX",
        "msisdn": "256752123456",
    }
    assert body["transaction"]["amount"] == "50000.00"
    assert body["transaction"]["currency"] == "UGX"
    assert body["transaction"]["id"]


def test_sandbox_payments_use_the_simulate_endpoints_without_signing():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/simulate/merchant/v2/payments/":
            return httpx.Response(
                200,
                json={
                    "data": {"transaction": {"id": "airtel-ref-1", "status": "TIP"}},
                    "status": {"code": "200", "message": "Success"},
                },
            )
        return httpx.Response(404)

    gateway = _gateway(handler, simulate=True, sign_requests=False)
    result = gateway.request_payment(_intent())

    assert result.reference == "airtel-ref-1"
    assert [request.url.path for request in requests] == [
        "/auth/oauth2/token",
        "/simulate/merchant/v2/payments/",
    ]
    charge = requests[1]
    assert "x-signature" not in charge.headers
    body = json.loads(charge.content)
    assert body["reference"] == "PAY-AIRTEL-1"
    assert body["transaction"]["amount"] == "50000.00"


def test_sandbox_verification_uses_the_simulate_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        assert request.url.path == "/simulate/standard/v1/payments/airtel-ref-1"
        return httpx.Response(
            200,
            json={
                "data": {
                    "transaction": {
                        "id": "airtel-ref-1",
                        "status": "TS",
                        "amount": "50000",
                        "currency": "UGX",
                    }
                },
                "status": {"code": "200", "message": "Success"},
            },
        )

    result = _gateway(handler, simulate=True).verify(_intent(gateway_reference="airtel-ref-1"))

    assert result.status == GatewayOutcome.SUCCESSFUL


def test_the_base_url_can_include_the_simulate_segment():
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(
            200,
            json={
                "data": {"transaction": {"id": "airtel-ref-1", "status": "TIP"}},
                "status": {"code": "200", "message": "Success"},
            },
        )

    gateway = _gateway(
        handler,
        base_url="https://openapi.airtel.ug/simulate",
        simulate=True,
        sign_requests=False,
    )
    gateway.request_payment(_intent())

    assert paths == ["/auth/oauth2/token", "/simulate/merchant/v2/payments/"]


def test_verify_reports_a_successful_payment():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(
            200,
            json={
                "data": {
                    "transaction": {
                        "id": "airtel-ref-1",
                        "status": "TS",
                        "amount": 50000,
                        "currency": "UGX",
                    }
                },
                "status": {"code": "200", "message": "Success"},
            },
        )

    result = _gateway(handler).verify(_intent(gateway_reference="airtel-ref-1"))

    assert result.status == GatewayOutcome.SUCCESSFUL
    assert result.amount == Decimal("50000")
    assert result.currency == "UGX"


def test_verify_reports_a_failed_payment():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(
            200,
            json={
                "data": {
                    "transaction": {
                        "id": "airtel-ref-1",
                        "status": "TF",
                        "message": "Insufficient funds",
                    }
                },
                "status": {"code": "200", "message": "Success"},
            },
        )

    result = _gateway(handler).verify(_intent(gateway_reference="airtel-ref-1"))

    assert result.status == GatewayOutcome.FAILED
    assert result.message == "Insufficient funds"


def test_verify_treats_a_missing_request_as_failed():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(404)

    result = _gateway(handler).verify(_intent(gateway_reference="airtel-ref-1"))

    assert result.status == GatewayOutcome.FAILED
    assert "could not find" in result.message


def test_callback_reads_the_reference_and_status():
    event = _gateway(lambda request: httpx.Response(200)).parse_callback(
        payload={
            "reference": "PAY-AIRTEL-1",
            "transaction": {
                "id": "airtel-ref-1",
                "status": "TS",
                "amount": 50000,
                "currency": "UGX",
            },
        },
        query={},
    )

    assert event.tx_ref == "PAY-AIRTEL-1"
    assert event.reference == "airtel-ref-1"
    assert event.status == GatewayOutcome.SUCCESSFUL
    assert event.amount == Decimal("50000")


def test_a_rejected_token_raises_a_gateway_error():
    gateway = _gateway(lambda request: httpx.Response(401, json={"message": "Invalid client"}))

    with pytest.raises(GatewayError, match="Invalid client"):
        gateway.request_payment(_intent())


def test_a_rejected_charge_raises_a_gateway_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/oauth2/token":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path == "/v1/rsa/encryption-keys":
            return _encryption_key_response()
        return httpx.Response(
            200,
            json={"status": {"code": "400", "message": "Invalid subscriber"}},
        )

    with pytest.raises(GatewayError, match="Invalid subscriber"):
        _gateway(handler).request_payment(_intent())
