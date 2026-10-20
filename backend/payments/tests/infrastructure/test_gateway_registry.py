from django.test import override_settings

from payments.domain.entities import MobileNetwork
from payments.infrastructure.gateways.airtel import AirtelMoneyGateway
from payments.infrastructure.gateways.mtn import MTNMoMoGateway
from payments.infrastructure.gateways.registry import (
    build_gateway_registry,
    build_provider_gateways,
)


@override_settings(
    MTN_MOMO_SUBSCRIPTION_KEY="sub-key",
    MTN_MOMO_API_USER="api-user",
    MTN_MOMO_API_KEY="api-key",
    AIRTEL_MONEY_CLIENT_ID="client-id",
    AIRTEL_MONEY_CLIENT_SECRET="client-secret",
)
def test_the_registry_builds_both_providers_from_settings():
    gateways = build_provider_gateways()

    assert isinstance(gateways[MobileNetwork.MTN], MTNMoMoGateway)
    assert isinstance(gateways[MobileNetwork.AIRTEL], AirtelMoneyGateway)


@override_settings(
    MTN_MOMO_SUBSCRIPTION_KEY="",
    MTN_MOMO_API_USER="",
    MTN_MOMO_API_KEY="",
    AIRTEL_MONEY_CLIENT_ID="",
    AIRTEL_MONEY_CLIENT_SECRET="",
)
def test_the_registry_omits_providers_without_credentials():
    assert build_provider_gateways() == {}


@override_settings(
    PAYMENTS_ALLOW_FAKE_GATEWAY=True,
    MTN_MOMO_SUBSCRIPTION_KEY="",
    MTN_MOMO_API_USER="",
    MTN_MOMO_API_KEY="",
    AIRTEL_MONEY_CLIENT_ID="",
    AIRTEL_MONEY_CLIENT_SECRET="",
)
def test_the_fake_gateway_covers_every_network_when_allowed():
    registry = build_gateway_registry()

    assert registry.configured_networks() == ["airtel", "mtn"]
