from uuid import uuid4

import pytest

from payments.application.commands import CancelPaymentIntentCommand
from payments.application.use_cases.cancel_intent import CancelPaymentIntentUseCase
from payments.domain.entities import PaymentStatus
from payments.domain.errors import IntentAlreadySettledError, PaymentIntentNotFoundError
from payments.tests.application.fakes import (
    FixedClock,
    InMemoryIntentRepository,
    RecordingAudit,
    make_intent,
)


def _use_case(repository, audit=None) -> CancelPaymentIntentUseCase:
    return CancelPaymentIntentUseCase(repository, FixedClock(), audit)


def test_cancelling_records_the_actor_and_reason():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)
    actor_id = uuid4()
    audit = RecordingAudit()

    result = _use_case(repository, audit).execute(
        CancelPaymentIntentCommand(
            intent_id=intent.id,
            reason="Customer changed their mind",
            actor_id=actor_id,
        )
    )

    assert result.status == PaymentStatus.CANCELLED
    assert result.failure_reason == "Customer changed their mind"
    assert audit.actions() == ["payment.cancelled"]
    assert audit.records[0]["user_id"] == actor_id


def test_a_blank_reason_gets_a_default():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository)

    result = _use_case(repository).execute(CancelPaymentIntentCommand(intent_id=intent.id))

    assert result.failure_reason == "Cancelled by the cashier"


def test_a_paid_payment_cannot_be_cancelled():
    repository = InMemoryIntentRepository()
    intent = make_intent(repository, status=PaymentStatus.PAID)

    with pytest.raises(IntentAlreadySettledError):
        _use_case(repository).execute(CancelPaymentIntentCommand(intent_id=intent.id))


def test_an_unknown_payment_is_not_found():
    repository = InMemoryIntentRepository()

    with pytest.raises(PaymentIntentNotFoundError):
        _use_case(repository).execute(CancelPaymentIntentCommand(intent_id=uuid4()))
