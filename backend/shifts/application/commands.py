from dataclasses import dataclass
from uuid import UUID

from shared.domain.money import Money
from shifts.domain.entities import CashMovementType


@dataclass(frozen=True)
class OpenShiftCommand:
    cashier_id: UUID
    opening_float: Money
    notes: str = ""


@dataclass(frozen=True)
class CloseShiftCommand:
    shift_id: UUID
    counted_cash: Money
    notes: str = ""
    user_id: UUID | None = None


@dataclass(frozen=True)
class RecordCashMovementCommand:
    shift_id: UUID
    type: CashMovementType
    amount: Money
    reason: str = ""
    user_id: UUID | None = None
