from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from payments.application.ports import SaleCompletionPort
from payments.domain.entities import (
    MobileNetwork,
    PaymentIntent,
    PaymentMethod,
    PaymentStatus,
)
from payments.domain.repository import PaymentIntentRepository
from payments.infrastructure.gateways.fake import FakeGateway
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


class InMemoryIntentRepository(PaymentIntentRepository):
    def __init__(self):
        self.intents: dict[UUID, PaymentIntent] = {}

    def get_by_id(self, intent_id: UUID) -> PaymentIntent | None:
        return self.intents.get(intent_id)

    def get_by_tx_ref(self, tx_ref: str) -> PaymentIntent | None:
        return next(
            (intent for intent in self.intents.values() if intent.tx_ref == tx_ref),
            None,
        )

    def get_by_gateway_reference(self, gateway_reference: str) -> PaymentIntent | None:
        return next(
            (
                intent
                for intent in self.intents.values()
                if intent.gateway_reference == gateway_reference
            ),
            None,
        )

    def get_by_idempotency_key(self, key: str) -> PaymentIntent | None:
        return next(
            (intent for intent in self.intents.values() if intent.idempotency_key == key),
            None,
        )

    def save(self, intent: PaymentIntent) -> None:
        self.intents[intent.id] = intent

    def list_pending_expired(self, at: datetime) -> list[PaymentIntent]:
        return [
            intent
            for intent in self.intents.values()
            if intent.status == PaymentStatus.PENDING
            and intent.expires_at is not None
            and intent.expires_at < at
        ]

    def list_intents(
        self,
        *,
        status: PaymentStatus | None = None,
        cashier_id: UUID | None = None,
    ) -> list[PaymentIntent]:
        return [
            intent
            for intent in self.intents.values()
            if (status is None or intent.status == status)
            and (cashier_id is None or intent.cashier_id == cashier_id)
        ]


class StubSaleCompletion(SaleCompletionPort):
    def __init__(self, sale_id: UUID | None = None, error: Exception | None = None):
        self.sale_id = sale_id or uuid4()
        self.error = error
        self.calls: list[dict] = []

    def complete_sale(self, **kwargs) -> UUID:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.sale_id


class FixedClock:
    def now(self) -> datetime:
        return NOW


class RecordingAudit:
    def __init__(self):
        self.records: list[dict] = []

    def record(self, **kwargs) -> None:
        self.records.append(kwargs)

    def actions(self) -> list[str]:
        return [record["action"] for record in self.records]


class CountingGateway(FakeGateway):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.requests = 0

    def request_payment(self, intent):
        self.requests += 1
        return super().request_payment(intent)


def make_intent(
    repository: InMemoryIntentRepository,
    *,
    tx_ref: str = "PAY-TEST",
    idempotency_key: str = "key-1",
    status: PaymentStatus = PaymentStatus.PENDING,
    attach_gateway: bool = True,
    **overrides,
) -> PaymentIntent:
    values = {
        "tx_ref": tx_ref,
        "idempotency_key": idempotency_key,
        "cashier_id": uuid4(),
        "shift_id": None,
        "method": PaymentMethod.MOBILE_MONEY,
        "amount": Money(Decimal("50000")),
        "phone": "256772123456",
        "network": MobileNetwork.MTN,
        "sale_payload": {
            "lines": [
                {
                    "product_id": str(uuid4()),
                    "quantity": 2,
                    "unit_price": "25000.00",
                    "unit_cost": "20000.00",
                }
            ]
        },
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
    }
    values.update(overrides)
    intent = PaymentIntent.create(**values)
    if attach_gateway:
        intent.attach_gateway(
            provider="fake-mtn",
            gateway_reference=f"fake-{tx_ref}",
            at=NOW,
        )
    intent.status = status
    repository.save(intent)
    return intent
