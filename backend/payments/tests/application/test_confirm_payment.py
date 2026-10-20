from decimal import Decimal

import pytest

from payments.application.commands import ConfirmPaymentCommand
from payments.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from payments.domain.entities import PaymentStatus
from payments.domain.errors import (
    AmountMismatchError,
    IntentAlreadySettledError,
    PaymentIntentNotFoundError,
)
from payments.tests.application.fakes import (
    FixedClock,
    InMemoryIntentRepository,
    RecordingAudit,
    StubSaleCompletion,
    make_intent,
)


def _use_case(repository, sales, audit=None) -> ConfirmPaymentUseCase:
    return ConfirmPaymentUseCase(repository, sales, FixedClock(), audit)


def _command(intent, **overrides) -> ConfirmPaymentCommand:
    values = {
        "tx_ref": intent.tx_ref,
        "paid": True,
        "gateway_reference": intent.gateway_reference,
        "amount": intent.amount.amount,
        "currency": intent.amount.currency,
        "message": "",
    }
    values.update(overrides)
    return ConfirmPaymentCommand(**values)


def test_a_successful_payment_completes_the_sale():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    audit = RecordingAudit()

    result = _use_case(repository, sales, audit).execute(_command(intent))

    assert result.status == PaymentStatus.PAID
    assert result.sale_id == sales.sale_id
    assert len(sales.calls) == 1
    call = sales.calls[0]
    assert call["method"] == "mobile_money"
    assert call["reference"] == "fake-PAY-TEST"
    assert call["provider"] == "fake-mtn"
    assert call["idempotency_key"] == "key-1"
    assert call["cashier_id"] == intent.cashier_id
    assert audit.actions() == ["payment.confirmed"]


def test_a_failed_payment_is_not_completed():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    audit = RecordingAudit()

    result = _use_case(repository, sales, audit).execute(
        _command(intent, paid=False, message="Insufficient funds")
    )

    assert result.status == PaymentStatus.FAILED
    assert result.failure_reason == "Insufficient funds"
    assert sales.calls == []
    assert audit.actions() == ["payment.failed"]


def test_a_different_amount_is_rejected_before_the_sale():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()

    with pytest.raises(AmountMismatchError):
        _use_case(repository, sales).execute(_command(intent, amount=Decimal("40000")))

    assert intent.status == PaymentStatus.PENDING
    assert sales.calls == []


def test_a_wrong_currency_is_rejected_before_the_sale():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()

    with pytest.raises(AmountMismatchError):
        _use_case(repository, sales).execute(_command(intent, currency="KES"))


def test_a_sale_that_cannot_complete_needs_review():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion(error=ValueError("Not enough stock"))
    audit = RecordingAudit()

    result = _use_case(repository, sales, audit).execute(_command(intent))

    assert result.status == PaymentStatus.NEEDS_REVIEW
    assert result.failure_reason == "Not enough stock"
    assert result.sale_id is None
    assert audit.actions() == ["payment.needs_review"]


def test_confirming_a_paid_intent_returns_it_without_completing_twice():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    sales = StubSaleCompletion()
    use_case = _use_case(repository, sales)

    first = use_case.execute(_command(intent))
    second = use_case.execute(_command(intent))

    assert first.id == second.id
    assert len(sales.calls) == 1


def test_an_unknown_payment_is_not_found():
    repository = InMemoryIntentRepository()

    with pytest.raises(PaymentIntentNotFoundError):
        _use_case(repository, StubSaleCompletion()).execute(
            ConfirmPaymentCommand(tx_ref="PAY-NOPE", paid=True)
        )


def test_a_cancelled_payment_cannot_be_confirmed():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository, status=PaymentStatus.CANCELLED)

    with pytest.raises(IntentAlreadySettledError):
        _use_case(repository, StubSaleCompletion()).execute(_command(intent))
