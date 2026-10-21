from uuid import UUID

from purchasing.domain.entities import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
    SupplierInvoice,
    SupplierInvoiceLine,
    SupplierInvoiceStatus,
)
from purchasing.domain.repository import (
    PurchaseOrderRepository,
    SupplierInvoiceRepository,
    SupplierRepository,
)
from purchasing.infrastructure.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    SupplierInvoiceLineModel,
    SupplierInvoiceModel,
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


class DjangoSupplierInvoiceRepository(SupplierInvoiceRepository):
    def get_by_id(self, invoice_id: UUID) -> SupplierInvoice | None:
        try:
            m = SupplierInvoiceModel.objects.prefetch_related("lines").get(id=invoice_id)
            return self._to_domain(m)
        except SupplierInvoiceModel.DoesNotExist:
            return None

    def save(self, invoice: SupplierInvoice) -> None:
        m, _ = SupplierInvoiceModel.objects.update_or_create(
            id=invoice.id,
            defaults={
                "supplier_id": invoice.supplier_id,
                "supplier_name": invoice.supplier_name,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "purchase_order_id": invoice.purchase_order_id,
                "status": invoice.status.value,
                "notes": invoice.notes,
                "amount_paid": invoice.amount_paid.amount,
                "total": invoice.total.amount,
            },
        )
        SupplierInvoiceLineModel.objects.filter(invoice=m).delete()
        for line in invoice.lines:
            SupplierInvoiceLineModel.objects.create(
                id=line.id,
                invoice=m,
                product_id=line.product_id,
                product_name=line.product_name,
                description=line.description,
                quantity=line.quantity,
                unit_cost=line.unit_cost.amount,
            )

    def list_invoices(
        self,
        *,
        supplier_id: UUID | None = None,
        status: SupplierInvoiceStatus | None = None,
    ) -> list[SupplierInvoice]:
        qs = SupplierInvoiceModel.objects.prefetch_related("lines")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if status:
            qs = qs.filter(status=status.value)
        return [self._to_domain(m) for m in qs]

    def invoice_number_exists(
        self, supplier_id: UUID, invoice_number: str, exclude_id: UUID | None = None
    ) -> bool:
        qs = SupplierInvoiceModel.objects.filter(
            supplier_id=supplier_id, invoice_number__iexact=invoice_number
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def _to_domain(self, m: SupplierInvoiceModel) -> SupplierInvoice:
        lines = [
            SupplierInvoiceLine(
                id=line.id,
                product_id=line.product_id,
                product_name=line.product_name,
                description=line.description,
                quantity=line.quantity,
                unit_cost=Money(line.unit_cost),
            )
            for line in m.lines.all()
        ]
        return SupplierInvoice(
            id=m.id,
            supplier_id=m.supplier_id,
            supplier_name=m.supplier_name,
            invoice_number=m.invoice_number,
            invoice_date=m.invoice_date,
            due_date=m.due_date,
            purchase_order_id=m.purchase_order_id,
            status=SupplierInvoiceStatus(m.status),
            notes=m.notes,
            lines=lines,
            amount_paid=Money(m.amount_paid),
            created_at=m.created_at,
        )
