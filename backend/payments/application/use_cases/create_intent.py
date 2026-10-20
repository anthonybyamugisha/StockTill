from collections.abc import Callable
from datetime import timedelta
from uuid import uuid4

from payments.application.audit_events import intent_initiated
from payments.application.commands import CreatePaymentIntentCommand
from payments.application.ports import GatewayOutcome, GatewayRegistry
from payments.domain.entities import PaymentIntent, PaymentMethod
from payments.domain.errors import UnsupportedPaymentMethodError
from payments.domain.repository import PaymentIntentRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock

DEFAULT_TTL_SECONDS = 300


def new_tx_ref() -> str:
    return f"PAY-{uuid4().hex[:20].upper()}"


class CreatePaymentIntentUseCase:
    def __init__(
        self,
        repository: PaymentIntentRepository,
        gateways: GatewayRegistry,
        clock: Clock,
        audit: AuditPort | None = None,
        tx_ref_factory: Callable[[], str] = new_tx_ref,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self._repository = repository
        self._gateways = gateways
        self._clock = clock
        self._audit = audit or NullAuditPort()
        self._tx_ref_factory = tx_ref_factory
        self._ttl_seconds = ttl_seconds

    def execute(self, command: CreatePaymentIntentCommand) -> PaymentIntent:
        existing = self._repository.get_by_idempotency_key(command.idempotency_key)
        if existing is not None:
            return existing

        if command.method != PaymentMethod.MOBILE_MONEY:
            raise UnsupportedPaymentMethodError(
                "Only mobile money payments are requested from a gateway"
            )

        now = self._clock.now()
        intent = PaymentIntent.create(
            tx_ref=self._tx_ref_factory(),
            idempotency_key=command.idempotency_key,
            cashier_id=command.cashier_id,
            shift_id=command.shift_id,
            method=command.method,
            amount=command.amount,
            phone=command.phone,
            network=command.network,
            sale_payload=command.sale_payload,
            created_at=now,
            expires_at=now + timedelta(seconds=self._ttl_seconds),
        )

        gateway = self._gateways.for_network(intent.network)
        result = gateway.request_payment(intent)
        intent.attach_gateway(
            provider=result.provider,
            gateway_reference=result.reference,
            checkout_url=result.checkout_url,
            at=now,
        )
        if result.status == GatewayOutcome.FAILED:
            intent.mark_failed(
                reason=result.message or "The payment request was rejected",
                at=now,
            )

        self._repository.save(intent)
        self._audit.record(**intent_initiated(intent).as_record_kwargs())
        return intent
