from sales.application.audit_events import sale_completed
from sales.application.commands import CompleteSaleCommand
from sales.application.discount_policy import assert_discount_within_limit
from sales.application.payments import build_payments
from sales.application.ports import CatalogPort, IdempotencyPort, InventoryPort, ReceiptNumberPort
from sales.application.sale_lines import build_sale_lines
from sales.domain.entities import Sale, SaleStatus
from sales.domain.errors import InvalidPaymentError
from sales.domain.repository import SaleRepository
from shared.application.audit import AuditPort, NullAuditPort
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
        audit: AuditPort | None = None,
    ):
        self._sale_repo = sale_repository
        self._inventory = inventory_port
        self._catalog = catalog_port
        self._receipt_port = receipt_number_port
        self._idempotency = idempotency_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CompleteSaleCommand) -> Sale:
        if self._idempotency.exists(command.idempotency_key):
            existing = self._sale_repo.get_by_idempotency_key(command.idempotency_key)
            if existing:
                return existing
            raise ValueError("Idempotency key already used")

        if command.max_discount_percent is not None:
            assert_discount_within_limit(command.lines, command.max_discount_percent)

        lines = build_sale_lines(command.lines, self._catalog)

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

        sale.payments.extend(build_payments(command.payments))

        if command.expected_total is not None and sale.total != command.expected_total:
            raise InvalidPaymentError(
                f"The payment does not match the sale total of {sale.total.amount}"
            )

        if sale.amount_paid < sale.total:
            raise InvalidPaymentError("Payments do not cover the sale total")

        for line in sale.lines:
            self._inventory.deduct_stock(line.product_id, line.quantity, sale.receipt_number)

        self._sale_repo.save(sale)
        self._idempotency.store(command.idempotency_key, sale.id)
        self._audit.record(**sale_completed(sale).as_record_kwargs())
        return sale
