from dataclasses import dataclass
from uuid import UUID

from inventory.domain.entities import MovementType
from shared.domain.money import Money


@dataclass(frozen=True)
class AdjustStockCommand:
    product_id: UUID
    quantity: int
    movement_type: MovementType
    reason: str
    reference: str | None = None
    unit_cost: Money | None = None
    user_id: UUID | None = None
    notes: str = ""


@dataclass(frozen=True)
class ReserveStockCommand:
    product_id: UUID
    quantity: int
    reference: str


@dataclass(frozen=True)
class ReleaseStockCommand:
    product_id: UUID
    quantity: int
    reference: str
