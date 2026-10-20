from payments.application.audit_events import intent_cancelled
from payments.application.commands import CancelPaymentIntentCommand
from payments.domain.entities import PaymentIntent, PaymentStatus
from payments.domain.errors import IntentAlreadySettledError, PaymentIntentNotFoundError
from payments.domain.repository import PaymentIntentRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class CancelPaymentIntentUseCase:
    def __init__(
        self,
        repository: PaymentIntentRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._repository = repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CancelPaymentIntentCommand) -> PaymentIntent:
        intent = self._repository.get_by_id(command.intent_id)
        if intent is None:
            raise PaymentIntentNotFoundError("Payment not found")
        if intent.status == PaymentStatus.PAID:
            raise IntentAlreadySettledError("A paid payment cannot be cancelled")

        now = self._clock.now()
        intent.cancel(
            reason=command.reason or "Cancelled by the cashier",
            at=now,
        )
        self._repository.save(intent)
        self._audit.record(**intent_cancelled(intent, command.actor_id).as_record_kwargs())
        return intent
