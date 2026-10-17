from datetime import datetime
from uuid import UUID, uuid4

import pytest

from sales.infrastructure.models import SaleModel
from sales.infrastructure.receipt_number import DatabaseReceiptNumberPort


def _prefix() -> str:
    return f"ST-{datetime.now().year}-"


def _make_sale(receipt_number: str, **kwargs) -> SaleModel:
    return SaleModel.objects.create(cashier_id=uuid4(), receipt_number=receipt_number, **kwargs)


@pytest.mark.django_db
def test_generate_starts_at_one_when_no_sales_exist():
    assert DatabaseReceiptNumberPort().generate() == f"{_prefix()}000001"


@pytest.mark.django_db
def test_generate_continues_after_the_highest_sequence():
    _make_sale(f"{_prefix()}000001", id=UUID("ffffffff-0000-0000-0000-000000000000"))
    _make_sale(f"{_prefix()}000002", id=UUID("00000000-0000-0000-0000-000000000000"))

    assert DatabaseReceiptNumberPort().generate() == f"{_prefix()}000003"


@pytest.mark.django_db
def test_generate_uses_the_highest_sequence_even_with_gaps():
    _make_sale(f"{_prefix()}000001")
    _make_sale(f"{_prefix()}000003")

    assert DatabaseReceiptNumberPort().generate() == f"{_prefix()}000004"
