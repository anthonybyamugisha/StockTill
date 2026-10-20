from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import IntegrityError

from payments.domain.entities import (
    MobileNetwork,
    PaymentIntent,
    PaymentMethod,
    PaymentStatus,
)
from payments.infrastructure.models import PaymentIntentModel
from payments.infrastructure.repository import DjangoPaymentIntentRepository
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


@pytest.fixture
def repository():
    return DjangoPaymentIntentRepository()


def _intent(**overrides):
    values = {
        "tx_ref": "PAY-ROUNDTRIP",
        "idempotency_key": "key-roundtrip",
        "cashier_id": uuid4(),
        "shift_id": uuid4(),
        "method": PaymentMethod.MOBILE_MONEY,
        "amount": Money(Decimal("50000")),
        "phone": "256772123456",
        "network": MobileNetwork.MTN,
        "sale_payload": {"lines": [{"quantity": 2}], "notes": "hello"},
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
    }
    values.update(overrides)
    return PaymentIntent.create(**values)


@pytest.mark.django_db
def test_a_saved_intent_round_trips(repository):
    intent = _intent()
    intent.attach_gateway(
        provider="mtn_momo",
        gateway_reference="ref-1",
        at=NOW,
    )
    repository.save(intent)

    loaded = repository.get_by_id(intent.id)

    assert loaded is not None
    assert loaded.tx_ref == intent.tx_ref
    assert loaded.idempotency_key == intent.idempotency_key
    assert loaded.cashier_id == intent.cashier_id
    assert loaded.shift_id == intent.shift_id
    assert loaded.method == PaymentMethod.MOBILE_MONEY
    assert loaded.network == MobileNetwork.MTN
    assert loaded.phone == "256772123456"
    assert loaded.amount == Money(Decimal("50000"))
    assert loaded.status == PaymentStatus.PENDING
    assert loaded.provider == "mtn_momo"
    assert loaded.gateway_reference == "ref-1"
    assert loaded.sale_payload == {"lines": [{"quantity": 2}], "notes": "hello"}
    assert loaded.expires_at == intent.expires_at


@pytest.mark.django_db
def test_an_intent_can_be_found_by_tx_ref(repository):
    intent = _intent(tx_ref="PAY-LOOKUP")
    repository.save(intent)

    assert repository.get_by_tx_ref("PAY-LOOKUP").id == intent.id
    assert repository.get_by_tx_ref("PAY-NOPE") is None


@pytest.mark.django_db
def test_an_intent_can_be_found_by_idempotency_key(repository):
    intent = _intent(idempotency_key="key-lookup")
    repository.save(intent)

    assert repository.get_by_idempotency_key("key-lookup").id == intent.id
    assert repository.get_by_idempotency_key("key-nope") is None


@pytest.mark.django_db
def test_an_intent_can_be_found_by_gateway_reference(repository):
    intent = _intent()
    intent.attach_gateway(provider="mtn_momo", gateway_reference="ref-lookup", at=NOW)
    repository.save(intent)

    assert repository.get_by_gateway_reference("ref-lookup").id == intent.id
    assert repository.get_by_gateway_reference("ref-nope") is None


@pytest.mark.django_db
def test_saving_again_updates_the_settled_state(repository):
    intent = _intent()
    repository.save(intent)
    sale_id = uuid4()

    intent.mark_paid(gateway_reference="ref-1", sale_id=sale_id, at=NOW)
    repository.save(intent)

    loaded = repository.get_by_id(intent.id)
    assert loaded.status == PaymentStatus.PAID
    assert loaded.sale_id == sale_id
    assert loaded.confirmed_at == NOW


@pytest.mark.django_db
def test_pending_expired_intents_are_listed(repository):
    expired = _intent(
        tx_ref="PAY-EXPIRED",
        idempotency_key="key-expired",
        expires_at=NOW + timedelta(minutes=1),
    )
    fresh = _intent(
        tx_ref="PAY-FRESH",
        idempotency_key="key-fresh",
        expires_at=NOW + timedelta(minutes=30),
    )
    paid = _intent(
        tx_ref="PAY-PAID",
        idempotency_key="key-paid",
        expires_at=NOW + timedelta(minutes=1),
    )
    paid.mark_paid(gateway_reference="ref-2", sale_id=uuid4(), at=NOW)
    for intent in (expired, fresh, paid):
        repository.save(intent)

    result = repository.list_pending_expired(NOW + timedelta(minutes=5))

    assert [intent.tx_ref for intent in result] == ["PAY-EXPIRED"]


@pytest.mark.django_db
def test_intents_can_be_filtered(repository):
    cashier_id = uuid4()
    repository.save(_intent(tx_ref="PAY-ONE", idempotency_key="key-1", cashier_id=cashier_id))
    repository.save(_intent(tx_ref="PAY-TWO", idempotency_key="key-2"))
    failed = _intent(tx_ref="PAY-THREE", idempotency_key="key-3", cashier_id=cashier_id)
    failed.mark_failed(reason="No funds", at=NOW)
    repository.save(failed)

    assert len(repository.list_intents()) == 3
    assert sorted(intent.tx_ref for intent in repository.list_intents(cashier_id=cashier_id)) == [
        "PAY-ONE",
        "PAY-THREE",
    ]
    assert [intent.tx_ref for intent in repository.list_intents(status=PaymentStatus.FAILED)] == [
        "PAY-THREE"
    ]


@pytest.mark.django_db
def test_the_same_idempotency_key_cannot_be_stored_twice(repository):
    repository.save(_intent(tx_ref="PAY-ONE", idempotency_key="key-same"))

    with pytest.raises(IntegrityError):
        repository.save(_intent(tx_ref="PAY-TWO", idempotency_key="key-same"))

    assert PaymentIntentModel.objects.count() == 1
