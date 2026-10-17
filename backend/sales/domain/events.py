from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class SaleCompleted:
    sale_id: UUID
    receipt_number: str
    total: Decimal
    cashier_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class SaleRefunded:
    sale_id: UUID
    refund_id: UUID
    amount: Decimal
    user_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class SaleVoided:
    sale_id: UUID
    receipt_number: str
    user_id: UUID
    reason: str
    timestamp: datetime
