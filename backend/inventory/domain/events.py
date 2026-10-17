from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class StockDeducted:
    product_id: UUID
    quantity: int
    reference: str
    timestamp: datetime


@dataclass(frozen=True)
class StockRestored:
    product_id: UUID
    quantity: int
    reference: str
    timestamp: datetime


@dataclass(frozen=True)
class LowStockAlert:
    product_id: UUID
    product_name: str
    current_quantity: int
    minimum_level: int
    timestamp: datetime
