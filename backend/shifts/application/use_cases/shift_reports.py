from uuid import UUID

from shifts.application.ports import CashTotals, SalesSummaryPort
from shifts.domain.entities import Shift
from shifts.domain.errors import NoOpenShiftError
from shifts.domain.repository import CashMovementRepository, ShiftRepository


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
