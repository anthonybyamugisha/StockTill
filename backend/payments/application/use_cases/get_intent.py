from uuid import UUID

from payments.domain.entities import PaymentIntent, PaymentStatus
from payments.domain.errors import PaymentIntentNotFoundError
from payments.domain.repository import PaymentIntentRepository


class GetPaymentIntentUseCase:
    def __init__(self, repository: PaymentIntentRepository):
        self._repository = repository

    def execute(self, intent_id: UUID) -> PaymentIntent:
        intent = self._repository.get_by_id(intent_id)
        if intent is None:
            raise PaymentIntentNotFoundError("Payment not found")
        return intent


class ListPaymentIntentsUseCase:
    def __init__(self, repository: PaymentIntentRepository):
        self._repository = repository

    def execute(
        self,
        *,
        status: PaymentStatus | None = None,
        cashier_id: UUID | None = None,
    ) -> list[PaymentIntent]:
        return self._repository.list_intents(status=status, cashier_id=cashier_id)
