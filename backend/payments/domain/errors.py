from shared.domain.errors import DomainError


class PaymentError(DomainError):
    pass


class InvalidPaymentAmountError(PaymentError):
    pass


class MissingMobileMoneyDetailsError(PaymentError):
    pass


class UnsupportedMobileNetworkError(PaymentError):
    pass


class UnsupportedPaymentMethodError(PaymentError):
    pass


class PaymentIntentNotFoundError(PaymentError):
    pass


class IntentAlreadySettledError(PaymentError):
    pass


class InvalidIntentTransitionError(PaymentError):
    pass


class AmountMismatchError(PaymentError):
    pass


class GatewayError(PaymentError):
    pass


class GatewayNotConfiguredError(GatewayError):
    pass


class InvalidCallbackError(PaymentError):
    pass
