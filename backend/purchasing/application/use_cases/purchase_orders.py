from uuid import UUID

from purchasing.application.commands import (
    CancelPurchaseOrderCommand,
    CreatePurchaseOrderCommand,
    ReceivePurchaseOrderCommand,
)
from purchasing.application.order_lines import build_order_lines
from purchasing.application.ports import StockIntakePort
from purchasing.domain.entities import PurchaseOrder
from purchasing.domain.errors import PurchaseOrderNotFoundError, SupplierNotFoundError
from purchasing.domain.repository import PurchaseOrderRepository, SupplierRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


class CreatePurchaseOrderUseCase:
    def __init__(
        self,
        order_repository: PurchaseOrderRepository,
        supplier_repository: SupplierRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._order_repo = order_repository
        self._supplier_repo = supplier_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreatePurchaseOrderCommand) -> PurchaseOrder:
        supplier = self._supplier_repo.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        lines = build_order_lines(command.lines)

        order = PurchaseOrder(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            lines=lines,
            reference=command.reference,
            notes=command.notes,
            created_at=self._clock.now(),
        )
        self._order_repo.save(order)
        self._audit.record(
            user_id=command.actor_id,
            action="purchase_order.created",
            entity_type="purchase_order",
            entity_id=str(order.id),
            after={
                "supplier_name": order.supplier_name,
                "reference": order.reference,
                "line_count": len(order.lines),
                "total": str(order.total.amount),
            },
        )
        return order


class MarkPurchaseOrderOrderedUseCase:
    def __init__(
        self,
        order_repository: PurchaseOrderRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._order_repo = order_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, purchase_order_id: UUID) -> PurchaseOrder:
        order = self._order_repo.get_by_id(purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        previous_status = order.status.value
        order.mark_ordered(self._clock.now())
        self._order_repo.save(order)
        self._audit.record(
            user_id=None,
            action="purchase_order.ordered",
            entity_type="purchase_order",
            entity_id=str(order.id),
            before={"status": previous_status},
            after={"status": order.status.value, "reference": order.reference},
        )
        return order


class ReceivePurchaseOrderUseCase:
    def __init__(
        self,
        order_repository: PurchaseOrderRepository,
        stock_intake_port: StockIntakePort,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._order_repo = order_repository
        self._stock_intake = stock_intake_port
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: ReceivePurchaseOrderCommand) -> PurchaseOrder:
        order = self._order_repo.get_by_id(command.purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        previous_status = order.status.value
        order.receive(self._clock.now())
        for line in order.lines:
            self._stock_intake.receive_stock(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
                reference=order.reference or str(order.id),
                user_id=command.user_id,
            )
        self._order_repo.save(order)
        self._audit.record(
            user_id=command.user_id,
            action="purchase_order.received",
            entity_type="purchase_order",
            entity_id=str(order.id),
            before={"status": previous_status},
            after={"status": order.status.value, "line_count": len(order.lines)},
        )
        return order


class CancelPurchaseOrderUseCase:
    def __init__(self, order_repository: PurchaseOrderRepository, audit: AuditPort | None = None):
        self._order_repo = order_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: CancelPurchaseOrderCommand) -> PurchaseOrder:
        order = self._order_repo.get_by_id(command.purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        previous_status = order.status.value
        order.cancel(command.reason)
        self._order_repo.save(order)
        self._audit.record(
            user_id=command.actor_id,
            action="purchase_order.cancelled",
            entity_type="purchase_order",
            entity_id=str(order.id),
            before={"status": previous_status},
            after={"status": order.status.value, "reason": command.reason},
        )
        return order


class ListPurchaseOrdersUseCase:
    def __init__(self, order_repository: PurchaseOrderRepository):
        self._order_repo = order_repository

    def execute(self) -> list[PurchaseOrder]:
        return self._order_repo.list_orders()


class GetPurchaseOrderUseCase:
    def __init__(self, order_repository: PurchaseOrderRepository):
        self._order_repo = order_repository

    def execute(self, purchase_order_id: UUID) -> PurchaseOrder:
        order = self._order_repo.get_by_id(purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        return order
