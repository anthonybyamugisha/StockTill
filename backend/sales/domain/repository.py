from abc import ABC, abstractmethod
from uuid import UUID

from sales.domain.entities import Refund, Sale, SaleStatus


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
        status: SaleStatus | None = None,
        payment_method: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        receipt_number: str | None = None,
    ) -> list[Sale]:
        pass

    @abstractmethod
    def exists_by_idempotency_key(self, key: str) -> bool:
        pass

    @abstractmethod
    def get_by_idempotency_key(self, key: str) -> Sale | None:
        pass


class RefundRepository(ABC):
    @abstractmethod
    def save(self, refund: Refund) -> None:
        pass

    @abstractmethod
    def list_by_sale(self, sale_id: UUID) -> list[Refund]:
        pass
