class DomainError(Exception):
    pass


class InsufficientStockError(DomainError):
    pass


class InvalidQuantityError(DomainError):
    pass


class InvalidPaymentError(DomainError):
    pass


class DiscountLimitExceededError(DomainError):
    pass


class SaleAlreadyVoidedError(DomainError):
    pass


class RefundExceedsRefundableError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass
