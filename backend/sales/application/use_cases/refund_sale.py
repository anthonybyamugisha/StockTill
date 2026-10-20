from decimal import Decimal

from sales.application.audit_events import sale_refunded
from sales.application.commands import RefundSaleCommand
from sales.application.ports import InventoryPort
from sales.domain.entities import Refund, SaleStatus
from sales.domain.errors import RefundExceedsRefundableError, SaleAlreadyVoidedError
from sales.domain.repository import RefundRepository, SaleRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class RefundSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        refund_repository: RefundRepository,
        inventory_port: InventoryPort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._sale_repo = sale_repository
        self._refund_repo = refund_repository
        self._inventory = inventory_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: RefundSaleCommand) -> Refund:
        sale = self._sale_repo.get_by_id(command.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        if sale.status == SaleStatus.VOIDED:
            raise SaleAlreadyVoidedError("Cannot refund a voided sale")
        if sale.status == SaleStatus.REFUNDED:
            raise RefundExceedsRefundableError("Sale is already fully refunded")

        original_status = sale.status.value
        original_refundable = sale.refundable_amount.amount

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
        entry = sale_refunded(sale, refund, original_status, str(original_refundable))
        self._audit.record(**entry.as_record_kwargs())
        return refund
