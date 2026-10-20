from uuid import UUID

from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock
from shifts.application.commands import CloseShiftCommand, OpenShiftCommand
from shifts.application.ports import CashTotals, SalesSummaryPort
from shifts.domain.entities import Shift
from shifts.domain.errors import NoOpenShiftError, ShiftAlreadyOpenError
from shifts.domain.repository import CashMovementRepository, ShiftRepository


class OpenShiftUseCase:
    def __init__(
        self, shift_repository: ShiftRepository, clock: Clock, audit: AuditPort | None = None
    ):
        self._shift_repo = shift_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

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
        self._audit.record(
            user_id=command.cashier_id,
            action="shift.opened",
            entity_type="shift",
            entity_id=str(shift.id),
            after={"opening_float": str(command.opening_float.amount)},
        )
        return shift


class GetCurrentShiftUseCase:
    def __init__(
        self,
        shift_repository: ShiftRepository,
        movement_repository: CashMovementRepository,
    ):
        self._shift_repo = shift_repository
        self._movement_repo = movement_repository

    def execute(self, cashier_id: UUID) -> Shift | None:
        shift = self._shift_repo.get_open_for_cashier(cashier_id)
        if shift is not None:
            shift.cash_movements = self._movement_repo.list_by_shift(shift.id)
        return shift


class CloseShiftUseCase:
    def __init__(
        self,
        shift_repository: ShiftRepository,
        movement_repository: CashMovementRepository,
        sales_port: SalesSummaryPort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._shift_repo = shift_repository
        self._movement_repo = movement_repository
        self._sales_port = sales_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CloseShiftCommand) -> tuple[Shift, CashTotals]:
        shift = self._shift_repo.get_by_id(command.shift_id)
        if shift is None:
            raise NoOpenShiftError("Shift not found")
        shift.cash_movements = self._movement_repo.list_by_shift(shift.id)
        totals = self._sales_port.cash_totals(shift.id)
        shift.close(command.counted_cash, self._clock.now(), command.notes)
        self._shift_repo.save(shift)
        expected = shift.expected_cash(totals.sales, totals.refunds)
        variance = shift.variance(totals.sales, totals.refunds)
        self._audit.record(
            user_id=command.user_id,
            action="shift.closed",
            entity_type="shift",
            entity_id=str(shift.id),
            after={
                "counted_cash": str(command.counted_cash.amount),
                "expected_cash": str(expected.amount),
                "variance": str(variance.amount) if variance is not None else None,
            },
        )
        return shift, totals
