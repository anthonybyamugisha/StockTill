from decimal import Decimal
from uuid import uuid4

import pytest

from payments.application.commands import CreatePaymentIntentCommand
from payments.application.ports import GatewayOutcome, GatewayRegistry
from payments.application.use_cases.create_intent import CreatePaymentIntentUseCase
from payments.domain.entities import MobileNetwork, PaymentMethod, PaymentStatus
from payments.domain.errors import UnsupportedPaymentMethodError
from payments.infrastructure.gateways.fake import FakeGateway
from payments.tests.application.fakes import (
    CountingGateway,
    FixedClock,
    InMemoryIntentRepository,
    RecordingAudit,
)
from shared.domain.money import Money


def _use_case(repository, gateway, audit=None) -> CreatePaymentIntentUseCase:
    return CreatePaymentIntentUseCase(
        repository,
        GatewayRegistry({MobileNetwork.MTN: gateway}),
        FixedClock(),
        audit,
        tx_ref_factory=lambda: "PAY-FIXED",
    )


def _command(**overrides) -> CreatePaymentIntentCommand:
    values = {
        "cashier_id": uuid4(),
        "method": PaymentMethod.MOBILE_MONEY,
        "amount": Money(Decimal("50000")),
        "idempotency_key": "key-1",
        "phone": "256772123456",
        "network": MobileNetwork.MTN,
        "sale_payload": {"lines": []},
    }
    values.update(overrides)
    return CreatePaymentIntentCommand(**values)


def test_a_mobile_money_intent_is_sent_to_the_gateway():
    repository = InMemoryIntentRepository()
    audit = RecordingAudit()

    intent = _use_case(repository, FakeGateway(), audit).execute(_command())

    assert intent.status == PaymentStatus.PENDING
    assert intent.provider == "fake"
    assert intent.gateway_reference == "fake-PAY-FIXED"
    assert repository.get_by_tx_ref("PAY-FIXED") is intent
    assert audit.actions() == ["payment.initiated"]


def test_replaying_the_idempotency_key_does_not_charge_again():
    repository = InMemoryIntentRepository()
    gateway = CountingGateway()
    use_case = _use_case(repository, gateway)

    first = use_case.execute(_command())
    second = use_case.execute(_command())

    assert first.id == second.id
    assert gateway.requests == 1
    assert len(repository.intents) == 1


def test_a_rejected_request_is_saved_as_failed():
    repository = InMemoryIntentRepository()

    intent = _use_case(
        repository,
        FakeGateway(request_outcome=GatewayOutcome.FAILED, message="No funds"),
    ).execute(_command())

    assert intent.status == PaymentStatus.FAILED
    assert intent.failure_reason == "No funds"


def test_a_card_payment_is_not_sent_to_the_mobile_gateway():
    repository = InMemoryIntentRepository()

    with pytest.raises(UnsupportedPaymentMethodError):
        _use_case(repository, FakeGateway()).execute(
            _command(method=PaymentMethod.CARD, network=None)
        )

    assert repository.intents == {}


def test_a_bank_transfer_is_not_sent_to_the_mobile_gateway():
    repository = InMemoryIntentRepository()

    with pytest.raises(UnsupportedPaymentMethodError):
        _use_case(repository, FakeGateway()).execute(
            _command(method=PaymentMethod.BANK_TRANSFER, network=None)
        )
