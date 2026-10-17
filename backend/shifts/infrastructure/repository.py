from uuid import UUID

from shared.domain.money import Money
from shifts.domain.entities import CashMovement, CashMovementType, Shift, ShiftStatus
from shifts.domain.repository import CashMovementRepository, ShiftRepository
from shifts.infrastructure.models import CashMovementModel, ShiftModel


class DjangoShiftRepository(ShiftRepository):
    def get_by_id(self, shift_id: UUID) -> Shift | None:
        try:
            m = ShiftModel.objects.prefetch_related("cash_movements").get(id=shift_id)
            return self._to_domain(m)
        except ShiftModel.DoesNotExist:
            return None

    def get_open_for_cashier(self, cashier_id: UUID) -> Shift | None:
        m = (
            ShiftModel.objects.prefetch_related("cash_movements")
            .filter(cashier_id=cashier_id, status=ShiftStatus.OPEN.value)
            .order_by("-opened_at")
            .first()
        )
        return self._to_domain(m) if m else None

    def save(self, shift: Shift) -> None:
        ShiftModel.objects.update_or_create(
            id=shift.id,
            defaults={
                "cashier_id": shift.cashier_id,
                "status": shift.status.value,
                "opening_float": shift.opening_float.amount,
                "counted_cash": shift.counted_cash.amount if shift.counted_cash else None,
                "notes": shift.notes,
                "closed_at": shift.closed_at,
            },
        )

    def _to_domain(self, m: ShiftModel) -> Shift:
        movements = [
            CashMovement(
                id=cm.id,
                shift_id=cm.shift_id,
                type=CashMovementType(cm.type),
                amount=Money(cm.amount),
                reason=cm.reason,
                user_id=cm.user_id,
                created_at=cm.created_at,
            )
            for cm in m.cash_movements.all()
        ]
        return Shift(
            id=m.id,
            cashier_id=m.cashier_id,
            status=ShiftStatus(m.status),
            opening_float=Money(m.opening_float),
            counted_cash=Money(m.counted_cash) if m.counted_cash is not None else None,
            notes=m.notes,
            opened_at=m.opened_at,
            closed_at=m.closed_at,
            cash_movements=movements,
        )


class DjangoCashMovementRepository(CashMovementRepository):
    def save(self, movement: CashMovement) -> None:
        CashMovementModel.objects.create(
            id=movement.id,
            shift_id=movement.shift_id,
            type=movement.type.value,
            amount=movement.amount.amount,
            reason=movement.reason,
            user_id=movement.user_id,
        )

    def list_by_shift(self, shift_id: UUID) -> list[CashMovement]:
        return [
            CashMovement(
                id=cm.id,
                shift_id=cm.shift_id,
                type=CashMovementType(cm.type),
                amount=Money(cm.amount),
                reason=cm.reason,
                user_id=cm.user_id,
                created_at=cm.created_at,
            )
            for cm in CashMovementModel.objects.filter(shift_id=shift_id)
        ]
