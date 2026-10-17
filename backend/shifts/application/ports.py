from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from shared.domain.money import Money


@dataclass(frozen=True)
class CashTotals:
    sales: Money
    refunds: Money


class SalesSummaryPort(ABC):
    @abstractmethod
    def cash_totals(self, shift_id: UUID) -> CashTotals:
        pass
