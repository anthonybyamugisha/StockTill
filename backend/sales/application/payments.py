from sales.application.commands import PaymentInput
from sales.domain.entities import Payment, PaymentMethod
from sales.domain.services import calculate_change


def build_payment(payment_input: PaymentInput) -> Payment:
    change = calculate_change(
        Payment(
            method=payment_input.method,
            amount=payment_input.amount,
            tendered=payment_input.tendered,
        )
    )
    return Payment(
        method=payment_input.method,
        amount=payment_input.amount,
        tendered=payment_input.tendered,
        change=change if payment_input.method == PaymentMethod.CASH else None,
        reference=payment_input.reference,
        provider=payment_input.provider,
    )


def build_payments(payment_inputs: list[PaymentInput]) -> list[Payment]:
    return [build_payment(payment_input) for payment_input in payment_inputs]
