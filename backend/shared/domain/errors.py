class DomainError(Exception):
    pass


class InsufficientStockError(DomainError):
    pass


class InvalidQuantityError(DomainError):
    pass


class InvalidDiscountError(DomainError):
    pass


class InvalidPaymentError(DomainError):
    pass


class SaleAlreadyCompletedError(DomainError):
    pass


class SaleAlreadyVoidedError(DomainError):
    pass


class RefundExceedsRefundableError(DomainError):
    pass


class ProductNotFoundError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass
