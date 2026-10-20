from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock
from shifts.application.commands import RecordCashMovementCommand
from shifts.domain.entities import CashMovement
from shifts.domain.errors import NoOpenShiftError
from shifts.domain.repository import CashMovementRepository, ShiftRepository


class RecordCashMovementUseCase:
    def __init__(
        self,
        shift_repository: ShiftRepository,
        movement_repository: CashMovementRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._shift_repo = shift_repository
        self._movement_repo = movement_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

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
        self._audit.record(
            user_id=command.user_id,
            action="shift.cash_movement",
            entity_type="shift",
            entity_id=str(shift.id),
            after={
                "type": command.type.value,
                "amount": str(command.amount.amount),
                "reason": command.reason,
            },
        )
        return movement
