from uuid import UUID

from purchasing.application.commands import (
    CreateSupplierInvoiceCommand,
    RecordSupplierInvoicePaymentCommand,
    VoidSupplierInvoiceCommand,
)
from purchasing.domain.entities import (
    SupplierInvoice,
    SupplierInvoiceLine,
    SupplierInvoiceStatus,
)
from purchasing.domain.errors import (
    DuplicateInvoiceNumberError,
    InvalidInvoiceStateError,
    SupplierInvoiceNotFoundError,
    SupplierNotFoundError,
)
from purchasing.domain.repository import SupplierInvoiceRepository, SupplierRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class CreateSupplierInvoiceUseCase:
    def __init__(
        self,
        invoice_repository: SupplierInvoiceRepository,
        supplier_repository: SupplierRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._invoice_repo = invoice_repository
        self._supplier_repo = supplier_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreateSupplierInvoiceCommand) -> SupplierInvoice:
        supplier = self._supplier_repo.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")

        invoice_number = command.invoice_number.strip()
        if not invoice_number:
            raise InvalidInvoiceStateError("Invoice number is required")
        if self._invoice_repo.invoice_number_exists(supplier.id, invoice_number):
            raise DuplicateInvoiceNumberError(
                f"Invoice {invoice_number} already exists for this supplier"
            )
        if not command.lines:
            raise InvalidInvoiceStateError("Invoice must have at least one line")
        if command.invoice_date and command.due_date and command.due_date < command.invoice_date:
            raise InvalidInvoiceStateError("Due date cannot be before the invoice date")

        lines = [
            SupplierInvoiceLine(
                product_id=line.product_id,
                product_name=line.product_name,
                description=line.description,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
            )
            for line in command.lines
        ]
        invoice = SupplierInvoice(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            invoice_number=invoice_number,
            invoice_date=command.invoice_date,
            due_date=command.due_date,
            purchase_order_id=command.purchase_order_id,
            notes=command.notes,
            lines=lines,
            created_at=self._clock.now(),
        )
        self._invoice_repo.save(invoice)
        self._audit.record(
            user_id=command.actor_id,
            action="supplier_invoice.created",
            entity_type="supplier_invoice",
            entity_id=str(invoice.id),
            after={
                "supplier_name": invoice.supplier_name,
                "invoice_number": invoice.invoice_number,
                "total": str(invoice.total.amount),
            },
        )
        return invoice


class RecordSupplierInvoicePaymentUseCase:
    def __init__(
        self, invoice_repository: SupplierInvoiceRepository, audit: AuditPort | None = None
    ):
        self._invoice_repo = invoice_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: RecordSupplierInvoicePaymentCommand) -> SupplierInvoice:
        invoice = self._invoice_repo.get_by_id(command.invoice_id)
        if invoice is None:
            raise SupplierInvoiceNotFoundError("Supplier invoice not found")
        before_paid = str(invoice.amount_paid.amount)
        before_status = invoice.status.value
        invoice.record_payment(command.amount)
        self._invoice_repo.save(invoice)
        self._audit.record(
            user_id=command.actor_id,
            action="supplier_invoice.payment_recorded",
            entity_type="supplier_invoice",
            entity_id=str(invoice.id),
            before={"amount_paid": before_paid, "status": before_status},
            after={
                "amount_paid": str(invoice.amount_paid.amount),
                "status": invoice.status.value,
                "payment": str(command.amount.amount),
            },
        )
        return invoice


class VoidSupplierInvoiceUseCase:
    def __init__(
        self, invoice_repository: SupplierInvoiceRepository, audit: AuditPort | None = None
    ):
        self._invoice_repo = invoice_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: VoidSupplierInvoiceCommand) -> SupplierInvoice:
        invoice = self._invoice_repo.get_by_id(command.invoice_id)
        if invoice is None:
            raise SupplierInvoiceNotFoundError("Supplier invoice not found")
        before_status = invoice.status.value
        invoice.void(command.reason)
        self._invoice_repo.save(invoice)
        self._audit.record(
            user_id=command.actor_id,
            action="supplier_invoice.voided",
            entity_type="supplier_invoice",
            entity_id=str(invoice.id),
            before={"status": before_status},
            after={"status": invoice.status.value, "reason": command.reason},
        )
        return invoice


class ListSupplierInvoicesUseCase:
    def __init__(self, invoice_repository: SupplierInvoiceRepository):
        self._invoice_repo = invoice_repository

    def execute(
        self,
        *,
        supplier_id: UUID | None = None,
        status: SupplierInvoiceStatus | None = None,
    ) -> list[SupplierInvoice]:
        return self._invoice_repo.list_invoices(supplier_id=supplier_id, status=status)


class GetSupplierInvoiceUseCase:
    def __init__(self, invoice_repository: SupplierInvoiceRepository):
        self._invoice_repo = invoice_repository

    def execute(self, invoice_id: UUID) -> SupplierInvoice:
        invoice = self._invoice_repo.get_by_id(invoice_id)
        if invoice is None:
            raise SupplierInvoiceNotFoundError("Supplier invoice not found")
        return invoice
