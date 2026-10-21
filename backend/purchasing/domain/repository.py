from abc import ABC, abstractmethod
from uuid import UUID

from purchasing.domain.entities import (
    PurchaseOrder,
    PurchaseOrderStatus,
    Supplier,
    SupplierInvoice,
    SupplierInvoiceStatus,
)


class SupplierRepository(ABC):
    @abstractmethod
    def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        pass

    @abstractmethod
    def save(self, supplier: Supplier) -> None:
        pass

    @abstractmethod
    def list_suppliers(self, *, search: str | None = None) -> list[Supplier]:
        pass


class PurchaseOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, purchase_order_id: UUID) -> PurchaseOrder | None:
        pass

    @abstractmethod
    def save(self, purchase_order: PurchaseOrder) -> None:
        pass

    @abstractmethod
    def list_orders(
        self,
        *,
        supplier_id: UUID | None = None,
        status: PurchaseOrderStatus | None = None,
    ) -> list[PurchaseOrder]:
        pass


class SupplierInvoiceRepository(ABC):
    @abstractmethod
    def get_by_id(self, invoice_id: UUID) -> SupplierInvoice | None:
        pass

    @abstractmethod
    def save(self, invoice: SupplierInvoice) -> None:
        pass

    @abstractmethod
    def list_invoices(
        self,
        *,
        supplier_id: UUID | None = None,
        status: SupplierInvoiceStatus | None = None,
    ) -> list[SupplierInvoice]:
        pass

    @abstractmethod
    def invoice_number_exists(
        self, supplier_id: UUID, invoice_number: str, exclude_id: UUID | None = None
    ) -> bool:
        pass
