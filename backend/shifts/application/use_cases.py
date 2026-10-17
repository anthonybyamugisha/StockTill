from uuid import UUID

from shared.domain.clock import Clock
from shifts.application.commands import (
    CloseShiftCommand,
    OpenShiftCommand,
    RecordCashMovementCommand,
)
from shifts.application.ports import CashTotals, SalesSummaryPort
from shifts.domain.entities import CashMovement, Shift
from shifts.domain.errors import NoOpenShiftError, ShiftAlreadyOpenError
from shifts.domain.repository import CashMovementRepository, ShiftRepository


class OpenShiftUseCase:
    def __init__(self, shift_repository: ShiftRepository, clock: Clock):
        self._shift_repo = shift_repository
        self._clock = clock

    def execute(self, command: OpenShiftCommand) -> Shift:
        if self._shift_repo.get_open_for_cashier(command.cashier_id) is not None:
            raise ShiftAlreadyOpenError("This cashier already has an open shift")
        shift = Shift(
            cashier_id=command.cashier_id,
            opening_float=command.opening_float,
            notes=command.notes,
            opened_at=self._clock.now(),
        )
        self._shift_repo.save(shift)
        return shift


class GetCurrentShiftUseCase:
    def __init__(self, shift_repository: ShiftRepository):
        self._shift_repo = shift_repository

    def execute(self, cashier_id: UUID) -> Shift | None:
        return self._shift_repo.get_open_for_cashier(cashier_id)


class CloseShiftUseCase:
    def __init__(
        self,
        shift_repository: ShiftRepository,
        sales_port: SalesSummaryPort,
        clock: Clock,
    ):
        self._shift_repo = shift_repository
        self._sales_port = sales_port
        self._clock = clock

    def execute(self, command: CloseShiftCommand) -> tuple[Shift, CashTotals]:
        shift = self._shift_repo.get_by_id(command.shift_id)
        if shift is None:
            raise NoOpenShiftError("Shift not found")
        totals = self._sales_port.cash_totals(shift.id)
        shift.close(command.counted_cash, self._clock.now(), command.notes)
        self._shift_repo.save(shift)
        return shift, totals


class RecordCashMovementUseCase:
    def __init__(
        self,
        shift_repository: ShiftRepository,
        movement_repository: CashMovementRepository,
        clock: Clock,
    ):
        self._shift_repo = shift_repository
        self._movement_repo = movement_repository
        self._clock = clock

    def execute(self, command: RecordCashMovementCommand) -> CashMovement:
        shift = self._shift_repo.get_by_id(command.shift_id)
        if shift is None or not shift.is_open:
            raise NoOpenShiftError("No open shift with that id")
        movement = CashMovement(
            shift_id=shift.id,
            type=command.type,
            amount=command.amount,
            reason=command.reason,
            user_id=command.user_id,
            created_at=self._clock.now(),
        )
        self._movement_repo.save(movement)
        return movement


class GetShiftReportUseCase:
    """Produces the data for an X-report (open shift) or Z-report (closed shift)."""

    def __init__(
        self,
        shift_repository: ShiftRepository,
        movement_repository: CashMovementRepository,
        sales_port: SalesSummaryPort,
    ):
        self._shift_repo = shift_repository
        self._movement_repo = movement_repository
        self._sales_port = sales_port

    def execute(self, shift_id: UUID) -> tuple[Shift, CashTotals]:
        shift = self._shift_repo.get_by_id(shift_id)
        if shift is None:
            raise NoOpenShiftError("Shift not found")
        shift.cash_movements = self._movement_repo.list_by_shift(shift_id)
        totals = self._sales_port.cash_totals(shift_id)
        return shift, totals
