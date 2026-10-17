from settings.domain.repository import SettingsRepository
from settings.infrastructure.models import BusinessSettingsModel
from shared.domain.settings import BusinessSettings


class DjangoSettingsRepository(SettingsRepository):
    def get(self) -> BusinessSettings:
        m, _ = BusinessSettingsModel.objects.get_or_create(key="main")
        return BusinessSettings(
            business_name=m.business_name,
            address=m.address,
            phone=m.phone,
            email=m.email,
            currency=m.currency,
            receipt_header=m.receipt_header,
            receipt_footer=m.receipt_footer,
            cashier_discount_limit=float(m.cashier_discount_limit),
            tax_rate=float(m.tax_rate),
            logo_url=m.logo_url,
        )

    def save(self, settings: BusinessSettings) -> None:
        BusinessSettingsModel.objects.update_or_create(
            key="main",
            defaults={
                "business_name": settings.business_name,
                "address": settings.address,
                "phone": settings.phone,
                "email": settings.email,
                "currency": settings.currency,
                "receipt_header": settings.receipt_header,
                "receipt_footer": settings.receipt_footer,
                "cashier_discount_limit": settings.cashier_discount_limit,
                "tax_rate": settings.tax_rate,
                "logo_url": settings.logo_url,
            },
        )
