from sales.application.commands import CompleteSaleCommand
from sales.application.ports import CatalogPort, IdempotencyPort, InventoryPort, ReceiptNumberPort
from sales.domain.entities import Payment, PaymentMethod, Sale, SaleLine, SaleStatus
from sales.domain.errors import InvalidPaymentError
from sales.domain.repository import SaleRepository
from sales.domain.services import calculate_change, calculate_discount
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

        lines: list[SaleLine] = []
        for item in command.lines:
            discount = None
            if item.discount_type and item.discount_value:
                discount = calculate_discount(
                    item.unit_price, item.quantity, item.discount_type, item.discount_value
                )

            product_name = item.product_name
            if not product_name:
                product = self._catalog.get_product(item.product_id)
                if product is not None:
                    product_name = str(product.get("name") or "")

            line = SaleLine(
                product_id=item.product_id,
                product_name=product_name,
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
        self._audit.record(
            user_id=command.cashier_id,
            action="sale.completed",
            entity_type="sale",
            entity_id=str(sale.id),
            after={
                "receipt_number": sale.receipt_number,
                "total": str(sale.total.amount),
                "line_count": len(sale.lines),
                "payment_methods": sorted({payment.method.value for payment in sale.payments}),
            },
        )
        return sale
