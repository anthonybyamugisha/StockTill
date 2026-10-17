from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from shared.domain.base import AggregateRoot, Entity
from shared.domain.money import Money
from shifts.domain.errors import ShiftAlreadyClosedError


class ShiftStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class CashMovementType(StrEnum):
    PAYOUT = "payout"
    CASH_IN = "cash_in"


@dataclass(eq=False)
class CashMovement(Entity):
    shift_id: UUID | None = None
    type: CashMovementType = CashMovementType.PAYOUT
    amount: Money = field(default_factory=Money.zero)
    reason: str = ""
    user_id: UUID | None = None
    created_at: datetime | None = None

    def signed_amount(self) -> Money:
        if self.type == CashMovementType.CASH_IN:
            return self.amount
        return Money.zero().subtract(self.amount)


@dataclass(eq=False)
class Shift(AggregateRoot):
    cashier_id: UUID | None = None
    status: ShiftStatus = ShiftStatus.OPEN
    opening_float: Money = field(default_factory=Money.zero)
    counted_cash: Money | None = None
    notes: str = ""
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    cash_movements: list[CashMovement] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.status == ShiftStatus.OPEN

    def net_cash_movements(self) -> Money:
        total = Money.zero()
        for movement in self.cash_movements:
            total = total.add(movement.signed_amount())
        return total

    def expected_cash(self, cash_sales: Money, cash_refunds: Money) -> Money:
        """Cash the drawer should hold: float + cash sales - cash refunds +/- movements."""
        return (
            self.opening_float.add(cash_sales).subtract(cash_refunds).add(self.net_cash_movements())
        )

    def variance(self, cash_sales: Money, cash_refunds: Money) -> Money | None:
        if self.counted_cash is None:
            return None
        return self.counted_cash.subtract(self.expected_cash(cash_sales, cash_refunds))

    def close(self, counted_cash: Money, at: datetime, notes: str = "") -> None:
        if self.status == ShiftStatus.CLOSED:
            raise ShiftAlreadyClosedError("Shift is already closed")
        self.counted_cash = counted_cash
        self.notes = notes
        self.closed_at = at
        self.status = ShiftStatus.CLOSED
