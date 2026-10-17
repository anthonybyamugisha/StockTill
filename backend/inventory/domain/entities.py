from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from shared.domain.base import Entity
from shared.domain.money import Money


class MovementType(str, Enum):
    OPENING = "opening"
    PURCHASE = "purchase"
    SALE = "sale"
    REFUND_RETURN = "refund_return"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    WRITE_OFF = "write_off"


@dataclass
class StockMovement(Entity):
    product_id: UUID = field(default_factory=UUID)
    quantity: int = 0
    movement_type: MovementType = MovementType.ADJUSTMENT_IN
    reason: str = ""
    reference: str | None = None
    unit_cost: Money = field(default_factory=Money.zero)
    user_id: UUID | None = None
    timestamp: datetime | None = None


@dataclass
class StockItem(Entity):
    product_id: UUID = field(default_factory=UUID)
    quantity_on_hand: int = 0
    reserved_quantity: int = 0
    last_movement_id: UUID | None = None

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.reserved_quantity
