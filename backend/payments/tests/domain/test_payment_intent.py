from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentMethod, PaymentStatus
from payments.domain.errors import (
    IntentAlreadySettledError,
    InvalidIntentTransitionError,
    InvalidPaymentAmountError,
    MissingMobileMoneyDetailsError,
)
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


def _intent(**overrides):
    values = {
        "tx_ref": "PAY-ABC123",
        "idempotency_key": "key-1",
        "cashier_id": uuid4(),
        "shift_id": None,
        "method": PaymentMethod.MOBILE_MONEY,
        "amount": Money(Decimal("50000")),
        "phone": "256700000000",
        "network": MobileNetwork.MTN,
        "sale_payload": {"lines": []},
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
    }
    values.update(overrides)
    return PaymentIntent.create(**values)


def test_a_new_intent_starts_pending():
    intent = _intent()

    assert intent.status == PaymentStatus.PENDING
    assert intent.amount == Money(Decimal("50000"))
    assert intent.created_at == NOW
    assert intent.expires_at == NOW + timedelta(minutes=5)
    assert intent.is_terminal is False
    assert intent.is_settled is False


def test_a_zero_amount_is_rejected():
    with pytest.raises(InvalidPaymentAmountError):
        _intent(amount=Money(Decimal("0")))


def test_a_negative_amount_is_rejected():
    with pytest.raises(InvalidPaymentAmountError):
        _intent(amount=Money(Decimal("-1")))


def test_mobile_money_needs_a_phone_number():
    with pytest.raises(MissingMobileMoneyDetailsError):
        _intent(phone="   ")


def test_mobile_money_needs_a_network():
    with pytest.raises(MissingMobileMoneyDetailsError):
        _intent(network=None)


def test_attaching_the_gateway_records_the_reference():
    intent = _intent()

    intent.attach_gateway(
        provider="mtn_momo",
        gateway_reference="ref-1",
        checkout_url=None,
        at=NOW,
    )

    assert intent.provider == "mtn_momo"
    assert intent.gateway_reference == "ref-1"
    assert intent.updated_at == NOW


def test_marking_paid_settles_the_intent():
    intent = _intent()
    sale_id = uuid4()

    intent.mark_paid(gateway_reference="ref-1", sale_id=sale_id, at=NOW)

    assert intent.status == PaymentStatus.PAID
    assert intent.sale_id == sale_id
    assert intent.confirmed_at == NOW
    assert intent.is_settled is True
    assert intent.is_terminal is False


def test_marking_paid_twice_is_harmless():
    intent = _intent()
    intent.mark_paid(gateway_reference="ref-1", sale_id=uuid4(), at=NOW)

    intent.mark_paid(gateway_reference="ref-1", sale_id=uuid4(), at=NOW)

    assert intent.status == PaymentStatus.PAID


def test_a_paid_intent_cannot_be_cancelled():
    intent = _intent()
    intent.mark_paid(gateway_reference="ref-1", sale_id=uuid4(), at=NOW)

    with pytest.raises(IntentAlreadySettledError):
        intent.cancel(reason="changed my mind", at=NOW)


def test_a_paid_intent_cannot_attach_a_new_gateway():
    intent = _intent()
    intent.mark_paid(gateway_reference="ref-1", sale_id=uuid4(), at=NOW)

    with pytest.raises(IntentAlreadySettledError):
        intent.attach_gateway(provider="other", gateway_reference="ref-2", at=NOW)


def test_marking_failed_records_the_reason():
    intent = _intent()

    intent.mark_failed(reason="Insufficient funds", at=NOW)

    assert intent.status == PaymentStatus.FAILED
    assert intent.failure_reason == "Insufficient funds"
    assert intent.is_terminal is True


def test_cancelling_records_the_reason():
    intent = _intent()

    intent.cancel(reason="Customer walked away", at=NOW)

    assert intent.status == PaymentStatus.CANCELLED
    assert intent.failure_reason == "Customer walked away"
    assert intent.is_terminal is True


def test_expiring_records_a_default_reason():
    intent = _intent()

    intent.expire(at=NOW)

    assert intent.status == PaymentStatus.EXPIRED
    assert intent.failure_reason == "The payment request expired"
    assert intent.is_terminal is True


def test_an_intent_is_expired_once_the_deadline_passes():
    intent = _intent()

    assert intent.is_expired(NOW + timedelta(minutes=4)) is False
    assert intent.is_expired(NOW + timedelta(minutes=5)) is True


def test_only_a_paid_intent_can_need_review():
    intent = _intent()

    with pytest.raises(InvalidIntentTransitionError):
        intent.mark_needs_review(reason="stock ran out", at=NOW)


def test_a_paid_intent_can_need_review_and_be_reconciled():
    intent = _intent()
    intent.mark_paid(gateway_reference="ref-1", sale_id=None, at=NOW)

    intent.mark_needs_review(reason="stock ran out", at=NOW)
    assert intent.status == PaymentStatus.NEEDS_REVIEW
    assert intent.is_settled is True

    sale_id = uuid4()
    intent.mark_reconciled(sale_id=sale_id, at=NOW)
    assert intent.status == PaymentStatus.PAID
    assert intent.sale_id == sale_id
    assert intent.failure_reason == ""
