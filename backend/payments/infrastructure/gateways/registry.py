from django.conf import settings

from payments.application.ports import GatewayRegistry, PaymentGatewayPort
from payments.domain.entities import MobileNetwork
from payments.infrastructure.gateways.fake import FakeGateway


def build_provider_gateways() -> dict[MobileNetwork, PaymentGatewayPort]:
    gateways: dict[MobileNetwork, PaymentGatewayPort] = {}
    return gateways


def build_gateway_registry() -> GatewayRegistry:
    gateways = build_provider_gateways()
    if settings.PAYMENTS_ALLOW_FAKE_GATEWAY:
        for network in MobileNetwork:
            gateways.setdefault(network, FakeGateway(provider=f"fake-{network.value}"))
    return GatewayRegistry(gateways)
