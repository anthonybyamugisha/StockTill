from dataclasses import dataclass

from shared.domain.base import Entity


@dataclass
class BusinessSettings(Entity):
    business_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    currency: str = "UGX"
    receipt_header: str = ""
    receipt_footer: str = ""
    cashier_discount_limit: float = 0.0
    tax_rate: float = 0.0
    logo_url: str | None = None
