from sales.application.audit_events import sale_voided
from sales.application.commands import VoidSaleCommand
from sales.application.ports import InventoryPort
from sales.domain.entities import Sale, SaleStatus
from sales.domain.errors import SaleAlreadyVoidedError
from sales.domain.repository import SaleRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class VoidSaleUseCase:
    def __init__(
        self,
        sale_repository: SaleRepository,
        inventory_port: InventoryPort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._sale_repo = sale_repository
        self._inventory = inventory_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: VoidSaleCommand) -> Sale:
        sale = self._sale_repo.get_by_id(command.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        if sale.status == SaleStatus.VOIDED:
            raise SaleAlreadyVoidedError("Sale is already voided")

        original_status = sale.status.value

        for line in sale.lines:
            self._inventory.restore_stock(line.product_id, line.quantity, sale.receipt_number)

        sale.status = SaleStatus.VOIDED
        self._sale_repo.save(sale)
        entry = sale_voided(sale, command.user_id, original_status, command.reason)
        self._audit.record(**entry.as_record_kwargs())
        return sale
