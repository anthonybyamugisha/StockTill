from shared.domain.errors import DomainError


class PurchasingError(DomainError):
    pass


class SupplierNotFoundError(PurchasingError):
    pass


class PurchaseOrderNotFoundError(PurchasingError):
    pass


class InvalidPurchaseOrderStateError(PurchasingError):
    pass


class EmptyPurchaseOrderError(PurchasingError):
    pass


class InvalidSupplierError(PurchasingError):
    pass


class SupplierInvoiceNotFoundError(PurchasingError):
    pass


class InvalidInvoiceStateError(PurchasingError):
    pass


class DuplicateInvoiceNumberError(PurchasingError):
    pass
