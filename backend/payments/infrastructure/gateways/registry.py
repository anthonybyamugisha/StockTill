from django.conf import settings

from payments.application.ports import GatewayRegistry, PaymentGatewayPort
from payments.domain.entities import MobileNetwork
from payments.infrastructure.gateways.airtel import AirtelMoneyGateway
from payments.infrastructure.gateways.fake import FakeGateway
from payments.infrastructure.gateways.mtn import MTNMoMoGateway


def build_provider_gateways() -> dict[MobileNetwork, PaymentGatewayPort]:
    gateways: dict[MobileNetwork, PaymentGatewayPort] = {}

    if (
        settings.MTN_MOMO_SUBSCRIPTION_KEY
        and settings.MTN_MOMO_API_USER
        and settings.MTN_MOMO_API_KEY
    ):
        gateways[MobileNetwork.MTN] = MTNMoMoGateway(
            base_url=settings.MTN_MOMO_BASE_URL,
            subscription_key=settings.MTN_MOMO_SUBSCRIPTION_KEY,
            api_user=settings.MTN_MOMO_API_USER,
            api_key=settings.MTN_MOMO_API_KEY,
            target_environment=settings.MTN_MOMO_TARGET_ENVIRONMENT,
            callback_url=settings.MTN_MOMO_CALLBACK_URL,
        )

    if settings.AIRTEL_MONEY_CLIENT_ID and settings.AIRTEL_MONEY_CLIENT_SECRET:
        gateways[MobileNetwork.AIRTEL] = AirtelMoneyGateway(
            base_url=settings.AIRTEL_MONEY_BASE_URL,
            client_id=settings.AIRTEL_MONEY_CLIENT_ID,
            client_secret=settings.AIRTEL_MONEY_CLIENT_SECRET,
            country=settings.AIRTEL_MONEY_COUNTRY,
            currency=settings.AIRTEL_MONEY_CURRENCY,
            callback_url=settings.AIRTEL_MONEY_CALLBACK_URL,
            simulate=settings.AIRTEL_MONEY_SIMULATE,
            sign_requests=settings.AIRTEL_MONEY_SIGN_REQUESTS,
        )

    return gateways


def build_gateway_registry() -> GatewayRegistry:
    gateways = build_provider_gateways()
    if settings.PAYMENTS_ALLOW_FAKE_GATEWAY:
        for network in MobileNetwork:
            gateways.setdefault(network, FakeGateway(provider=f"fake-{network.value}"))
    return GatewayRegistry(gateways)
