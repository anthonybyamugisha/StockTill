from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from payments.domain.entities import MobileNetwork, PaymentIntent
from payments.domain.errors import GatewayNotConfiguredError, UnsupportedMobileNetworkError
from shared.domain.money import Money


class GatewayOutcome(StrEnum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"


@dataclass(frozen=True)
class GatewayResult:
    provider: str
    reference: str | None = None
    status: GatewayOutcome = GatewayOutcome.PENDING
    message: str = ""
    checkout_url: str | None = None
    amount: Decimal | None = None
    currency: str | None = None


@dataclass(frozen=True)
class CallbackEvent:
    tx_ref: str
    reference: str | None = None
    status: GatewayOutcome = GatewayOutcome.PENDING
    amount: Decimal | None = None
    currency: str | None = None
    message: str = ""


class PaymentGatewayPort(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def request_payment(self, intent: PaymentIntent) -> GatewayResult:
        pass

    @abstractmethod
    def verify(self, intent: PaymentIntent) -> GatewayResult:
        pass

    @abstractmethod
    def parse_callback(self, *, payload: dict[str, Any], query: dict[str, str]) -> CallbackEvent:
        pass


class GatewayRegistry:
    def __init__(self, gateways: dict[MobileNetwork, PaymentGatewayPort]):
        self._gateways = gateways

    def for_network(self, network: MobileNetwork | None) -> PaymentGatewayPort:
        if network is None:
            raise UnsupportedMobileNetworkError("A mobile money payment needs a network")
        gateway = self._gateways.get(network)
        if gateway is None:
            raise GatewayNotConfiguredError(f"No payment gateway is configured for {network.value}")
        return gateway

    def configured_networks(self) -> list[str]:
        return sorted(network.value for network in self._gateways)


class SaleCompletionPort(ABC):
    @abstractmethod
    def complete_sale(
        self,
        *,
        payload: dict[str, Any],
        method: str,
        amount: Money,
        reference: str | None,
        provider: str | None,
        idempotency_key: str,
        cashier_id: UUID,
        shift_id: UUID | None,
    ) -> UUID:
        pass
