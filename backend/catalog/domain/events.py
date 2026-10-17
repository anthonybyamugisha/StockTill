from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class ProductCreated:
    product_id: UUID
    name: str
    sku: str
    timestamp: datetime


@dataclass(frozen=True)
class PriceChanged:
    product_id: UUID
    field: str
    old_value: Decimal
    new_value: Decimal
    user_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class ProductDeactivated:
    product_id: UUID
    name: str
    timestamp: datetime
