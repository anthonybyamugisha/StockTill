from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SaleCompleted:
    sale_id: UUID
    receipt_number: str
    total: str
    cashier_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class SaleRefunded:
    sale_id: UUID
    refund_id: UUID
    amount: str
    user_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class SaleVoided:
    sale_id: UUID
    receipt_number: str
    user_id: UUID
    reason: str
    timestamp: datetime
