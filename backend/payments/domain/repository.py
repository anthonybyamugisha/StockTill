from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from payments.domain.entities import PaymentIntent, PaymentStatus


class PaymentIntentRepository(ABC):
    @abstractmethod
    def get_by_id(self, intent_id: UUID) -> PaymentIntent | None:
        pass

    @abstractmethod
    def get_by_tx_ref(self, tx_ref: str) -> PaymentIntent | None:
        pass

    @abstractmethod
    def get_by_gateway_reference(self, gateway_reference: str) -> PaymentIntent | None:
        pass

    @abstractmethod
    def get_by_idempotency_key(self, key: str) -> PaymentIntent | None:
        pass

    @abstractmethod
    def save(self, intent: PaymentIntent) -> None:
        pass

    @abstractmethod
    def list_pending_expired(self, at: datetime) -> list[PaymentIntent]:
        pass

    @abstractmethod
    def list_intents(
        self,
        *,
        status: PaymentStatus | None = None,
        cashier_id: UUID | None = None,
    ) -> list[PaymentIntent]:
        pass
