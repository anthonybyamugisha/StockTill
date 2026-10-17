from decimal import Decimal

from sales.application.commands import (
    CompleteSaleCommand,
    RefundSaleCommand,
    VoidSaleCommand,
)
from sales.application.ports import CatalogPort, IdempotencyPort, InventoryPort, ReceiptNumberPort
from sales.domain.entities import Payment, PaymentMethod, Refund, Sale, SaleLine, SaleStatus
from sales.domain.errors import (
    InvalidPaymentError,
    RefundExceedsRefundableError,
    SaleAlreadyVoidedError,
)
from sales.domain.repository import RefundRepository, SaleRepository
from sales.domain.services import calculate_change, calculate_discount
from shared.domain.clock import Clock


class CompleteSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        inventory_port: InventoryPort,
        catalog_port: CatalogPort,
        receipt_number_port: ReceiptNumberPort,
        idempotency_port: IdempotencyPort,
        clock: Clock,
    ):
        self._sale_repo = sale_repository
        self._inventory = inventory_port
        self._catalog = catalog_port
        self._receipt_port = receipt_number_port
        self._idempotency = idempotency_port
        self._clock = clock

    def execute(self, command: CompleteSaleCommand) -> Sale:
        if self._idempotency.exists(command.idempotency_key):
            existing = self._sale_repo.get_by_idempotency_key(command.idempotency_key)
            if existing:
                return existing
            raise ValueError("Idempotency key already used")

        lines: list[SaleLine] = []
        for item in command.lines:
            discount = None
            if item.discount_type and item.discount_value:
                discount = calculate_discount(
                    item.unit_price, item.quantity, item.discount_type, item.discount_value
                )
            line = SaleLine(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                unit_cost=item.unit_cost,
                discount=discount,
            )
            lines.append(line)

        sale = Sale(
            receipt_number=self._receipt_port.generate(),
            cashier_id=command.cashier_id,
            shift_id=command.shift_id,
            lines=lines,
            status=SaleStatus.COMPLETED,
            created_at=self._clock.now(),
            notes=command.notes,
            idempotency_key=command.idempotency_key,
        )

        for payment_input in command.payments:
            change = calculate_change(
                Payment(
                    method=payment_input.method,
                    amount=payment_input.amount,
                    tendered=payment_input.tendered,
                )
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
        self._idempotency.store(command.idempotency_key, sale.id)
        return sale


class RefundSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        refund_repository: RefundRepository,
        inventory_port: InventoryPort,
        clock: Clock,
    ):
        self._sale_repo = sale_repository
        self._refund_repo = refund_repository
        self._inventory = inventory_port
        self._clock = clock

    def execute(self, command: RefundSaleCommand) -> Refund:
        sale = self._sale_repo.get_by_id(command.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        if sale.status == SaleStatus.VOIDED:
            raise SaleAlreadyVoidedError("Cannot refund a voided sale")
        if sale.status == SaleStatus.REFUNDED:
            raise RefundExceedsRefundableError("Sale is already fully refunded")

        refundable_qty = (
            sale.refundable_quantity_for_line(command.line_id) if command.line_id else 1
        )
        if command.quantity > refundable_qty:
            raise RefundExceedsRefundableError(
                f"Refund quantity {command.quantity} exceeds refundable {refundable_qty}"
            )

        line = (
            next((item for item in sale.lines if item.id == command.line_id), None)
            if command.line_id
            else sale.lines[0]
        )
        if line is None:
            raise ValueError("Sale line not found")
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
            created_at=self._clock.now(),
        )

        sale.refunds.append(refund)
        if sale.refundable_amount.is_zero():
            sale.status = SaleStatus.REFUNDED
        else:
            sale.status = SaleStatus.PARTIALLY_REFUNDED

        if command.restock and line:
            self._inventory.restore_stock(line.product_id, command.quantity, sale.receipt_number)

        self._refund_repo.save(refund)
        self._sale_repo.save(sale)
        return refund


class VoidSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        inventory_port: InventoryPort,
        clock: Clock,
    ):
        self._sale_repo = sale_repository
        self._inventory = inventory_port
        self._clock = clock

    def execute(self, command: VoidSaleCommand) -> Sale:
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
