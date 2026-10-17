from abc import ABC, abstractmethod
from uuid import UUID

from shifts.domain.entities import CashMovement, Shift


class ShiftRepository(ABC):
    @abstractmethod
    def get_by_id(self, shift_id: UUID) -> Shift | None:
        pass

    @abstractmethod
    def get_open_for_cashier(self, cashier_id: UUID) -> Shift | None:
        pass

    @abstractmethod
    def save(self, shift: Shift) -> None:
        pass


class CashMovementRepository(ABC):
    @abstractmethod
    def save(self, movement: CashMovement) -> None:
        pass

    @abstractmethod
    def list_by_shift(self, shift_id: UUID) -> list[CashMovement]:
        pass
