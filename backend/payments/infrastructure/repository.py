from datetime import datetime
from uuid import UUID

from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentMethod, PaymentStatus
from payments.domain.repository import PaymentIntentRepository
from payments.infrastructure.models import PaymentIntentModel
from shared.domain.money import Money


class DjangoPaymentIntentRepository(PaymentIntentRepository):
    def get_by_id(self, intent_id: UUID) -> PaymentIntent | None:
        try:
            return self._to_domain(PaymentIntentModel.objects.get(id=intent_id))
        except PaymentIntentModel.DoesNotExist:
            return None

    def get_by_tx_ref(self, tx_ref: str) -> PaymentIntent | None:
        model = PaymentIntentModel.objects.filter(tx_ref=tx_ref).first()
        return self._to_domain(model) if model else None

    def get_by_gateway_reference(self, gateway_reference: str) -> PaymentIntent | None:
        model = PaymentIntentModel.objects.filter(gateway_reference=gateway_reference).first()
        return self._to_domain(model) if model else None

    def get_by_idempotency_key(self, key: str) -> PaymentIntent | None:
        model = PaymentIntentModel.objects.filter(idempotency_key=key).first()
        return self._to_domain(model) if model else None

    def save(self, intent: PaymentIntent) -> None:
        PaymentIntentModel.objects.update_or_create(
            id=intent.id,
            defaults={
                "tx_ref": intent.tx_ref,
                "idempotency_key": intent.idempotency_key,
                "cashier_id": intent.cashier_id,
                "shift_id": intent.shift_id,
                "method": intent.method.value,
                "network": intent.network.value if intent.network else "",
                "phone": intent.phone,
                "amount": intent.amount.amount,
                "currency": intent.amount.currency,
                "status": intent.status.value,
                "provider": intent.provider,
                "gateway_reference": intent.gateway_reference,
                "checkout_url": intent.checkout_url or "",
                "failure_reason": intent.failure_reason,
                "sale_id": intent.sale_id,
                "sale_payload": intent.sale_payload,
                "confirmed_at": intent.confirmed_at,
                "expires_at": intent.expires_at,
            },
        )

    def list_pending_expired(self, at: datetime) -> list[PaymentIntent]:
        models = PaymentIntentModel.objects.filter(
            status=PaymentStatus.PENDING.value,
            expires_at__lt=at,
        )
        return [self._to_domain(model) for model in models]

    def list_intents(
        self,
        *,
        status: PaymentStatus | None = None,
        cashier_id: UUID | None = None,
    ) -> list[PaymentIntent]:
        models = PaymentIntentModel.objects.all()
        if status is not None:
            models = models.filter(status=status.value)
        if cashier_id is not None:
            models = models.filter(cashier_id=cashier_id)
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: PaymentIntentModel) -> PaymentIntent:
        return PaymentIntent(
            id=model.id,
            tx_ref=model.tx_ref,
            idempotency_key=model.idempotency_key,
            cashier_id=model.cashier_id,
            shift_id=model.shift_id,
            method=PaymentMethod(model.method),
            network=MobileNetwork(model.network) if model.network else None,
            phone=model.phone,
            amount=Money(model.amount, model.currency),
            status=PaymentStatus(model.status),
            provider=model.provider,
            gateway_reference=model.gateway_reference,
            checkout_url=model.checkout_url or None,
            failure_reason=model.failure_reason,
            sale_id=model.sale_id,
            sale_payload=model.sale_payload or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            confirmed_at=model.confirmed_at,
            expires_at=model.expires_at,
        )
