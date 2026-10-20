import pytest

from payments.application.ports import GatewayOutcome, GatewayRegistry
from payments.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from payments.application.use_cases.handle_callback import HandleGatewayCallbackUseCase
from payments.domain.entities import MobileNetwork, PaymentStatus
from payments.domain.errors import InvalidCallbackError, PaymentIntentNotFoundError
from payments.infrastructure.gateways.fake import FakeGateway
from payments.tests.application.fakes import (
    FixedClock,
    InMemoryIntentRepository,
    RecordingAudit,
    StubSaleCompletion,
    make_intent,
)


def _use_case(repository, gateway, sales, audit=None) -> HandleGatewayCallbackUseCase:
    return HandleGatewayCallbackUseCase(
        repository,
        GatewayRegistry({MobileNetwork.MTN: gateway}),
        ConfirmPaymentUseCase(repository, sales, FixedClock(), audit),
    )


def _execute(use_case, tx_ref, status="successful"):
    return use_case.execute(
        network=MobileNetwork.MTN,
        payload={"tx_ref": tx_ref, "status": status},
        query={},
    )


def test_a_successful_verification_completes_the_sale():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()

    result = _execute(_use_case(repository, FakeGateway(), sales), intent.tx_ref)

    assert result.status == PaymentStatus.PAID
    assert len(sales.calls) == 1


def test_the_verify_endpoint_decides_the_outcome_not_the_body():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    gateway = FakeGateway(
        verify_outcome=GatewayOutcome.FAILED,
        message="Cancelled on the phone",
    )

    result = _execute(
        _use_case(repository, gateway, sales),
        intent.tx_ref,
        status="successful",
    )

    assert result.status == PaymentStatus.FAILED
    assert result.failure_reason == "Cancelled on the phone"
    assert sales.calls == []


def test_a_pending_verification_leaves_the_intent_pending():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    audit = RecordingAudit()

    result = _execute(
        _use_case(repository, FakeGateway(verify_outcome=GatewayOutcome.PENDING), sales, audit),
        intent.tx_ref,
    )

    assert result.status == PaymentStatus.PENDING
    assert sales.calls == []
    assert audit.records == []


def test_a_replayed_callback_completes_the_sale_once():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    use_case = _use_case(repository, FakeGateway(), sales)

    _execute(use_case, intent.tx_ref)
    _execute(use_case, intent.tx_ref)

    assert len(sales.calls) == 1


def test_an_unknown_callback_is_not_found():
    repository = InMemoryIntentRepository()

    with pytest.raises(PaymentIntentNotFoundError):
        _execute(_use_case(repository, FakeGateway(), StubSaleCompletion()), "PAY-NOPE")


def test_a_callback_without_a_reference_is_invalid():
    repository = InMemoryIntentRepository()
    use_case = _use_case(repository, FakeGateway(), StubSaleCompletion())

    with pytest.raises(InvalidCallbackError):
        use_case.execute(network=MobileNetwork.MTN, payload={}, query={})
