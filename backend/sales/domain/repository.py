from abc import ABC, abstractmethod
from uuid import UUID

from sales.domain.entities import Refund, Sale, SaleLine


class SaleRepository(ABC):
    @abstractmethod
    def get_by_id(self, sale_id: UUID) -> Sale | None:
        pass

    @abstractmethod
    def get_by_receipt_number(self, receipt_number: str) -> Sale | None:
        pass

    @abstractmethod
    def save(self, sale: Sale) -> None:
        pass

    @abstractmethod
    def list_sales(
        self,
        *,
        cashier_id: UUID | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Sale]:
        pass


class RefundRepository(ABC):
    @abstractmethod
    def save(self, refund: Refund) -> None:
        pass

    @abstractmethod
    def list_by_sale(self, sale_id: UUID) -> list[Refund]:
        pass
