from decimal import Decimal
from uuid import uuid4

from sales.application.audit_events import sale_completed, sale_refunded, sale_voided
from sales.domain.entities import Payment, PaymentMethod, Refund, Sale, SaleLine, SaleStatus
from shared.domain.money import Money


def _sale() -> Sale:
    line = SaleLine(
        product_id=uuid4(),
        product_name="Sugar 1kg",
        quantity=2,
        unit_price=Money(Decimal("1500.00")),
        unit_cost=Money(Decimal("1000.00")),
    )
    payment = Payment(method=PaymentMethod.CASH, amount=Money(Decimal("3000.00")))
    return Sale(
        id=uuid4(),
        receipt_number="ST-2026-000001",
        lines=[line],
        payments=[payment],
    )


def test_completed_entry_summarises_the_basket():
    sale = _sale()

    entry = sale_completed(sale)

    assert entry.action == "sale.completed"
    assert entry.before is None
    assert entry.after == {
        "receipt_number": "ST-2026-000001",
        "total": "3000.00",
        "line_count": 1,
        "payment_methods": ["cash"],
    }


def test_record_kwargs_name_the_sale_entity():
    sale = _sale()

    kwargs = sale_completed(sale).as_record_kwargs()

    assert kwargs["entity_type"] == "sale"
    assert kwargs["entity_id"] == str(sale.id)
    assert kwargs["user_id"] is None


def test_refunded_entry_keeps_the_previous_and_new_state():
    sale = _sale()
    sale.status = SaleStatus.PARTIALLY_REFUNDED
    refund = Refund(
        sale_id=sale.id,
        quantity=1,
        amount=Money(Decimal("1500.00")),
        reason="Damaged",
        restock=True,
        user_id=uuid4(),
    )

    entry = sale_refunded(sale, refund, "completed", "3000.00")

    assert entry.before == {"status": "completed", "refundable_amount": "3000.00"}
    assert entry.after["status"] == "partially_refunded"
    assert entry.after["restock"] is True
    assert entry.after["reason"] == "Damaged"


def test_voided_entry_records_the_reason():
    sale = _sale()
    sale.status = SaleStatus.VOIDED
    user_id = uuid4()

    entry = sale_voided(sale, user_id, "completed", "Wrong item")

    assert entry.user_id == user_id
    assert entry.before == {"status": "completed", "total": "3000.00"}
    assert entry.after == {"status": "voided", "reason": "Wrong item"}
