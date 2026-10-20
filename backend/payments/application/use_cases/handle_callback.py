from typing import Any

from payments.application.commands import ConfirmPaymentCommand
from payments.application.ports import GatewayOutcome, GatewayRegistry
from payments.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from payments.domain.entities import MobileNetwork, PaymentIntent, PaymentStatus
from payments.domain.errors import InvalidCallbackError, PaymentIntentNotFoundError
from payments.domain.repository import PaymentIntentRepository


class HandleGatewayCallbackUseCase:
    def __init__(
        self,
        repository: PaymentIntentRepository,
        gateways: GatewayRegistry,
        confirm: ConfirmPaymentUseCase,
    ):
        self._repository = repository
        self._gateways = gateways
        self._confirm = confirm

    def execute(
        self,
        *,
        network: MobileNetwork,
        payload: dict[str, Any],
        query: dict[str, str],
    ) -> PaymentIntent:
        gateway = self._gateways.for_network(network)
        event = gateway.parse_callback(payload=payload, query=query)
        if not event.tx_ref:
            raise InvalidCallbackError("The callback did not identify a payment")

        intent = self._repository.get_by_tx_ref(event.tx_ref)
        if intent is None:
            raise PaymentIntentNotFoundError(f"No payment found for {event.tx_ref}")
        if intent.status == PaymentStatus.PAID:
            return intent

        result = gateway.verify(intent)
        if result.status == GatewayOutcome.PENDING:
            return intent

        return self._confirm.execute(
            ConfirmPaymentCommand(
                tx_ref=intent.tx_ref,
                paid=result.status == GatewayOutcome.SUCCESSFUL,
                gateway_reference=result.reference or intent.gateway_reference,
                amount=result.amount,
                currency=result.currency,
                message=result.message,
            )
        )
