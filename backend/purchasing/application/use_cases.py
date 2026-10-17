from uuid import UUID

from purchasing.application.commands import (
    CancelPurchaseOrderCommand,
    CreatePurchaseOrderCommand,
    CreateSupplierCommand,
    ReceivePurchaseOrderCommand,
    UpdateSupplierCommand,
)
from purchasing.application.ports import StockIntakePort
from purchasing.domain.entities import PurchaseOrder, PurchaseOrderLine, Supplier
from purchasing.domain.errors import (
    PurchaseOrderNotFoundError,
    SupplierNotFoundError,
)
from purchasing.domain.repository import PurchaseOrderRepository, SupplierRepository
from shared.domain.clock import Clock


class CreateSupplierUseCase:
    def __init__(self, supplier_repository: SupplierRepository, clock: Clock):
        self._supplier_repo = supplier_repository
        self._clock = clock

    def execute(self, command: CreateSupplierCommand) -> Supplier:
        supplier = Supplier(
            name=command.name,
            contact_name=command.contact_name,
            email=command.email,
            phone=command.phone,
            address=command.address,
            created_at=self._clock.now(),
        )
        self._supplier_repo.save(supplier)
        return supplier


class UpdateSupplierUseCase:
    def __init__(self, supplier_repository: SupplierRepository):
        self._supplier_repo = supplier_repository

    def execute(self, command: UpdateSupplierCommand) -> Supplier:
        supplier = self._supplier_repo.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        supplier.update_contact(
            name=command.name,
            contact_name=command.contact_name,
            email=command.email,
            phone=command.phone,
            address=command.address,
        )
        self._supplier_repo.save(supplier)
        return supplier


class ListSuppliersUseCase:
    def __init__(self, supplier_repository: SupplierRepository):
        self._supplier_repo = supplier_repository

    def execute(self, *, search: str | None = None) -> list[Supplier]:
        return self._supplier_repo.list_suppliers(search=search)


class GetSupplierUseCase:
    def __init__(self, supplier_repository: SupplierRepository):
        self._supplier_repo = supplier_repository

    def execute(self, supplier_id: UUID) -> Supplier:
        supplier = self._supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        return supplier


class CreatePurchaseOrderUseCase:
    def __init__(
        self,
        order_repository: PurchaseOrderRepository,
        supplier_repository: SupplierRepository,
        clock: Clock,
    ):
        self._order_repo = order_repository
        self._supplier_repo = supplier_repository
        self._clock = clock

    def execute(self, command: CreatePurchaseOrderCommand) -> PurchaseOrder:
        supplier = self._supplier_repo.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError("Supplier not found")
        lines = [
            PurchaseOrderLine(
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
            )
            for line in command.lines
        ]
        order = PurchaseOrder(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            lines=lines,
            reference=command.reference,
            notes=command.notes,
            created_at=self._clock.now(),
        )
        self._order_repo.save(order)
        return order


class MarkPurchaseOrderOrderedUseCase:
    def __init__(self, order_repository: PurchaseOrderRepository, clock: Clock):
        self._order_repo = order_repository
        self._clock = clock

    def execute(self, purchase_order_id: UUID) -> PurchaseOrder:
        order = self._order_repo.get_by_id(purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        order.mark_ordered(self._clock.now())
        self._order_repo.save(order)
        return order


class ReceivePurchaseOrderUseCase:
    def __init__(
        self,
        order_repository: PurchaseOrderRepository,
        stock_intake_port: StockIntakePort,
        clock: Clock,
    ):
        self._order_repo = order_repository
        self._stock_intake = stock_intake_port
        self._clock = clock

    def execute(self, command: ReceivePurchaseOrderCommand) -> PurchaseOrder:
        order = self._order_repo.get_by_id(command.purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
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
        return order


class CancelPurchaseOrderUseCase:
    def __init__(self, order_repository: PurchaseOrderRepository):
        self._order_repo = order_repository

    def execute(self, command: CancelPurchaseOrderCommand) -> PurchaseOrder:
        order = self._order_repo.get_by_id(command.purchase_order_id)
        if order is None:
            raise PurchaseOrderNotFoundError("Purchase order not found")
        order.cancel(command.reason)
        self._order_repo.save(order)
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
