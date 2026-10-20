from decimal import Decimal

from payments.application.audit_events import (
    intent_confirmed,
    intent_failed,
    intent_needs_review,
)
from payments.application.commands import ConfirmPaymentCommand
from payments.application.ports import SaleCompletionPort
from payments.domain.entities import PaymentIntent, PaymentStatus
from payments.domain.errors import (
    AmountMismatchError,
    IntentAlreadySettledError,
    PaymentIntentNotFoundError,
)
from payments.domain.repository import PaymentIntentRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class ConfirmPaymentUseCase:
    def __init__(
        self,
        repository: PaymentIntentRepository,
        sale_completion: SaleCompletionPort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._repository = repository
        self._sale_completion = sale_completion
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: ConfirmPaymentCommand) -> PaymentIntent:
        intent = self._repository.get_by_tx_ref(command.tx_ref)
        if intent is None:
            raise PaymentIntentNotFoundError(f"No payment found for {command.tx_ref}")
        if intent.status == PaymentStatus.PAID:
            return intent
        if intent.is_terminal:
            raise IntentAlreadySettledError(
                f"This payment is already {intent.status.value} and cannot be confirmed"
            )

        now = self._clock.now()
        if not command.paid:
            intent.mark_failed(
                reason=command.message or "The payment failed",
                at=now,
            )
            self._repository.save(intent)
            self._audit.record(**intent_failed(intent).as_record_kwargs())
            return intent

        self._check_amount(intent, command.amount, command.currency)

        intent.mark_paid(
            gateway_reference=command.gateway_reference or intent.gateway_reference,
            sale_id=None,
            at=now,
        )
        assert intent.cashier_id is not None
        try:
            sale_id = self._sale_completion.complete_sale(
                payload=intent.sale_payload,
                method=intent.method.value,
                amount=intent.amount,
                reference=intent.gateway_reference or intent.tx_ref,
                provider=intent.provider or None,
                idempotency_key=intent.idempotency_key,
                cashier_id=intent.cashier_id,
                shift_id=intent.shift_id,
            )
        except Exception as error:
            intent.mark_needs_review(reason=str(error), at=now)
            self._repository.save(intent)
            self._audit.record(**intent_needs_review(intent).as_record_kwargs())
            return intent

        intent.sale_id = sale_id
        self._repository.save(intent)
        self._audit.record(**intent_confirmed(intent).as_record_kwargs())
        return intent

    def _check_amount(
        self, intent: PaymentIntent, amount: Decimal | None, currency: str | None
    ) -> None:
        if amount is None:
            return
        paid_currency = currency or intent.amount.currency
        if amount != intent.amount.amount or paid_currency != intent.amount.currency:
            raise AmountMismatchError("The amount paid does not match the payment request")
