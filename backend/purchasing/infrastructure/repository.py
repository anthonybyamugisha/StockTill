from uuid import UUID

from purchasing.domain.entities import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
)
from purchasing.domain.repository import PurchaseOrderRepository, SupplierRepository
from purchasing.infrastructure.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    SupplierModel,
)
from shared.domain.money import Money


class DjangoSupplierRepository(SupplierRepository):
    def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        try:
            m = SupplierModel.objects.get(id=supplier_id)
            return self._to_domain(m)
        except SupplierModel.DoesNotExist:
            return None

    def save(self, supplier: Supplier) -> None:
        SupplierModel.objects.update_or_create(
            id=supplier.id,
            defaults={
                "name": supplier.name,
                "contact_name": supplier.contact_name,
                "email": supplier.email,
                "phone": supplier.phone,
                "address": supplier.address,
                "is_active": supplier.is_active,
            },
        )

    def list_suppliers(self, *, search: str | None = None) -> list[Supplier]:
        qs = SupplierModel.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        return [self._to_domain(m) for m in qs]

    def _to_domain(self, m: SupplierModel) -> Supplier:
        return Supplier(
            id=m.id,
            name=m.name,
            contact_name=m.contact_name,
            email=m.email,
            phone=m.phone,
            address=m.address,
            is_active=m.is_active,
            created_at=m.created_at,
        )


class DjangoPurchaseOrderRepository(PurchaseOrderRepository):
    def get_by_id(self, purchase_order_id: UUID) -> PurchaseOrder | None:
        try:
            m = PurchaseOrderModel.objects.prefetch_related("lines").get(id=purchase_order_id)
            return self._to_domain(m)
        except PurchaseOrderModel.DoesNotExist:
            return None

    def save(self, purchase_order: PurchaseOrder) -> None:
        m, _ = PurchaseOrderModel.objects.update_or_create(
            id=purchase_order.id,
            defaults={
                "supplier_id": purchase_order.supplier_id,
                "supplier_name": purchase_order.supplier_name,
                "status": purchase_order.status.value,
                "reference": purchase_order.reference,
                "notes": purchase_order.notes,
                "total": purchase_order.total.amount,
                "ordered_at": purchase_order.ordered_at,
                "received_at": purchase_order.received_at,
            },
        )
        PurchaseOrderLineModel.objects.filter(purchase_order=m).delete()
        for line in purchase_order.lines:
            PurchaseOrderLineModel.objects.create(
                id=line.id,
                purchase_order=m,
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_cost=line.unit_cost.amount,
            )

    def list_orders(
        self,
        *,
        supplier_id: UUID | None = None,
        status: PurchaseOrderStatus | None = None,
    ) -> list[PurchaseOrder]:
        qs = PurchaseOrderModel.objects.prefetch_related("lines")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if status:
            qs = qs.filter(status=status.value)
        return [self._to_domain(m) for m in qs]

    def _to_domain(self, m: PurchaseOrderModel) -> PurchaseOrder:
        lines = [
            PurchaseOrderLine(
                id=line.id,
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_cost=Money(line.unit_cost),
            )
            for line in m.lines.all()
        ]
        return PurchaseOrder(
            id=m.id,
            supplier_id=m.supplier_id,
            supplier_name=m.supplier_name,
            status=PurchaseOrderStatus(m.status),
            reference=m.reference,
            notes=m.notes,
            lines=lines,
            created_at=m.created_at,
            ordered_at=m.ordered_at,
            received_at=m.received_at,
        )
