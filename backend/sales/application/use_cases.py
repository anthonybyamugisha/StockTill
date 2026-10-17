from decimal import Decimal

from sales.application.commands import (
    CompleteSaleCommand,
    LineItem,
    PaymentInput,
    RefundSaleCommand,
    VoidSaleCommand,
)
from sales.application.ports import CatalogPort, InventoryPort, ReceiptNumberPort
from sales.domain.entities import Payment, PaymentMethod, Sale, SaleLine, SaleStatus
from sales.domain.errors import (
    InvalidPaymentError,
    RefundExceedsRefundableError,
    SaleAlreadyVoidedError,
)
from sales.domain.repository import RefundRepository, SaleRepository
from sales.domain.services import calculate_change
from shared.domain.money import Money


class CompleteSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        inventory_port: InventoryPort,
        catalog_port: CatalogPort,
        receipt_number_port: ReceiptNumberPort,
    ):
        self._sale_repo = sale_repository
        self._inventory = inventory_port
        self._catalog = catalog_port
        self._receipt_port = receipt_number_port

    def execute(self, command: CompleteSaleCommand) -> Sale:
        lines: list[SaleLine] = []
        for item in command.lines:
            line = SaleLine(
                product_id=item.product_id,
                product_name="",
                quantity=item.quantity,
                unit_price=item.unit_price,
                unit_cost=item.unit_cost,
            )
            lines.append(line)

        sale = Sale(
            receipt_number=self._receipt_port.generate(),
            cashier_id=command.cashier_id,
            lines=lines,
            status=SaleStatus.COMPLETED,
        )

        for payment_input in command.payments:
            change = calculate_change(
                Payment(method=payment_input.method, amount=payment_input.amount, tendered=payment_input.tendered)
            )
            sale.payments.append(
                Payment(
                    method=payment_input.method,
                    amount=payment_input.amount,
                    tendered=payment_input.tendered,
                    change=change if payment_input.method == PaymentMethod.CASH else None,
                    reference=payment_input.reference,
                    provider=payment_input.provider,
                )
            )

        if sale.amount_paid < sale.total:
            raise InvalidPaymentError("Payments do not cover the sale total")

        for line in sale.lines:
            self._inventory.deduct_stock(line.product_id, line.quantity, sale.receipt_number)

        self._sale_repo.save(sale)
        return sale


class RefundSaleUseCase:
    def __init__(self, sale_repository: SaleRepository, refund_repository: RefundRepository, inventory_port: InventoryPort):
        self._sale_repo = sale_repository
        self._refund_repo = refund_repository
        self._inventory = inventory_port

    def execute(self, command: RefundSaleCommand):
        sale = self._sale_repo.get_by_id(command.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        if sale.status == SaleStatus.VOIDED:
            raise SaleAlreadyVoidedError("Cannot refund a voided sale")

        line = next((l for l in sale.lines if l.id == command.line_id), None)
        if line is None:
            raise ValueError("Line not found")

        already_refunded = sum(
            r.quantity for r in sale.refunds if r.line_id == command.line_id
        )
        if already_refunded + command.quantity > line.quantity:
            raise RefundExceedsRefundableError("Refund quantity exceeds sold quantity")

        refund_amount = line.unit_price.multiply(Decimal(command.quantity))
        if refund_amount > sale.refundable_amount:
            raise RefundExceedsRefundableError("Refund exceeds refundable amount")

        refund = Refund(
            sale_id=sale.id,
            line_id=command.line_id,
            quantity=command.quantity,
            amount=refund_amount,
            reason=command.reason,
            restock=command.restock,
            user_id=command.user_id,
        )

        sale.refunds.append(refund)
        if sale.refundable_amount.is_zero():
            sale.status = SaleStatus.REFUNDED
        else:
            sale.status = SaleStatus.PARTIALLY_REFUNDED

        if command.restock:
            self._inventory.restore_stock(line.product_id, command.quantity, sale.receipt_number)

        self._refund_repo.save(refund)
        self._sale_repo.save(sale)
        return refund


class VoidSaleUseCase:
    def __init__(self, sale_repository: SaleRepository, inventory_port: InventoryPort):
        self._sale_repo = sale_repository
        self._inventory = inventory_port

    def execute(self, command: VoidSaleCommand):
        sale = self._sale_repo.get_by_id(command.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        if sale.status == SaleStatus.VOIDED:
            raise SaleAlreadyVoidedError("Sale is already voided")

        for line in sale.lines:
            self._inventory.restore_stock(line.product_id, line.quantity, sale.receipt_number)

        sale.status = SaleStatus.VOIDED
        self._sale_repo.save(sale)
        return sale
