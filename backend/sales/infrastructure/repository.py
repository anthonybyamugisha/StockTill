from uuid import UUID

from sales.domain.entities import (
    Discount,
    DiscountType,
    Payment,
    PaymentMethod,
    Refund,
    Sale,
    SaleLine,
    SaleStatus,
)
from sales.domain.repository import RefundRepository, SaleRepository
from sales.infrastructure.models import PaymentModel, RefundModel, SaleLineModel, SaleModel
from shared.domain.money import Money


class DjangoSaleRepository(SaleRepository):
    def get_by_id(self, sale_id: UUID) -> Sale | None:
        try:
            m = SaleModel.objects.prefetch_related("lines", "payments", "refunds").get(id=sale_id)
            return self._to_domain(m)
        except SaleModel.DoesNotExist:
            return None

    def get_by_receipt_number(self, receipt_number: str) -> Sale | None:
        try:
            m = SaleModel.objects.prefetch_related("lines", "payments", "refunds").get(
                receipt_number=receipt_number
            )
            return self._to_domain(m)
        except SaleModel.DoesNotExist:
            return None

    def get_by_idempotency_key(self, key: str) -> Sale | None:
        try:
            m = SaleModel.objects.prefetch_related("lines", "payments", "refunds").get(
                idempotency_key=key
            )
            return self._to_domain(m)
        except SaleModel.DoesNotExist:
            return None

    def save(self, sale: Sale) -> None:
        m, _ = SaleModel.objects.update_or_create(
            id=sale.id,
            defaults={
                "receipt_number": sale.receipt_number,
                "cashier_id": sale.cashier_id,
                "shift_id": sale.shift_id,
                "status": sale.status.value,
                "subtotal": sale.subtotal.amount,
                "total_discount": sale.total_discount.amount,
                "total": sale.total.amount,
                "notes": sale.notes,
                "idempotency_key": sale.idempotency_key,
            },
        )
        SaleLineModel.objects.filter(sale=m).delete()
        for line in sale.lines:
            SaleLineModel.objects.create(
                id=line.id,
                sale=m,
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_price=line.unit_price.amount,
                unit_cost=line.unit_cost.amount,
                discount_type=line.discount.type.value if line.discount else None,
                discount_value=line.discount.value if line.discount else 0,
                discount_amount=line.discount.amount.amount if line.discount else 0,
            )
        PaymentModel.objects.filter(sale=m).delete()
        for payment in sale.payments:
            PaymentModel.objects.create(
                id=payment.id,
                sale=m,
                method=payment.method.value,
                amount=payment.amount.amount,
                tendered=payment.tendered.amount if payment.tendered else None,
                change=payment.change.amount if payment.change else None,
                reference=payment.reference,
                provider=payment.provider,
            )

    def list_sales(
        self,
        *,
        cashier_id: UUID | None = None,
        status: SaleStatus | None = None,
        payment_method: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        receipt_number: str | None = None,
    ) -> list[Sale]:
        qs = SaleModel.objects.prefetch_related("lines", "payments", "refunds")
        if cashier_id:
            qs = qs.filter(cashier_id=cashier_id)
        if status:
            qs = qs.filter(status=status.value)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if receipt_number:
            qs = qs.filter(receipt_number__icontains=receipt_number)
        if payment_method:
            qs = qs.filter(payments__method=payment_method)
        return [self._to_domain(m) for m in qs]

    def exists_by_idempotency_key(self, key: str) -> bool:
        return SaleModel.objects.filter(idempotency_key=key).exists()

    def _to_domain(self, m: SaleModel) -> Sale:
        lines = [
            SaleLine(
                id=ln.id,
                product_id=ln.product_id,
                product_name=ln.product_name,
                quantity=ln.quantity,
                unit_price=Money(ln.unit_price),
                unit_cost=Money(ln.unit_cost),
                discount=Discount(
                    type=DiscountType(ln.discount_type),
                    value=ln.discount_value,
                    amount=Money(ln.discount_amount),
                )
                if ln.discount_type
                else None,
            )
            for ln in m.lines.all()
        ]
        payments = [
            Payment(
                id=p.id,
                method=PaymentMethod(p.method),
                amount=Money(p.amount),
                tendered=Money(p.tendered) if p.tendered else None,
                change=Money(p.change) if p.change else None,
                reference=p.reference,
                provider=p.provider,
            )
            for p in m.payments.all()
        ]
        refunds = [
            Refund(
                id=r.id,
                sale_id=r.sale_id,
                line_id=r.line_id,
                quantity=r.quantity,
                amount=Money(r.amount),
                reason=r.reason,
                restock=r.restock,
                user_id=r.user_id,
                created_at=r.created_at,
            )
            for r in m.refunds.all()
        ]
        return Sale(
            id=m.id,
            receipt_number=m.receipt_number,
            cashier_id=m.cashier_id,
            shift_id=m.shift_id,
            lines=lines,
            payments=payments,
            refunds=refunds,
            status=SaleStatus(m.status),
            created_at=m.created_at,
            notes=m.notes,
            idempotency_key=m.idempotency_key,
        )


class DjangoRefundRepository(RefundRepository):
    def save(self, refund: Refund) -> None:
        RefundModel.objects.create(
            id=refund.id,
            sale_id=refund.sale_id,
            line_id=refund.line_id,
            quantity=refund.quantity,
            amount=refund.amount.amount,
            reason=refund.reason,
            restock=refund.restock,
            user_id=refund.user_id,
        )

    def list_by_sale(self, sale_id: UUID) -> list[Refund]:
        return [
            Refund(
                id=r.id,
                sale_id=r.sale_id,
                line_id=r.line_id,
                quantity=r.quantity,
                amount=Money(r.amount),
                reason=r.reason,
                restock=r.restock,
                user_id=r.user_id,
                created_at=r.created_at,
            )
            for r in RefundModel.objects.filter(sale_id=sale_id)
        ]
