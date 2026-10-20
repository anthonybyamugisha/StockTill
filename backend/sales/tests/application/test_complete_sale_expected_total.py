from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from sales.application.commands import CompleteSaleCommand, LineItem, PaymentInput
from sales.application.use_cases.complete_sale import CompleteSaleUseCase
from sales.domain.entities import PaymentMethod
from sales.domain.errors import InvalidPaymentError
from shared.domain.money import Money

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class StubSaleRepository:
    def __init__(self):
        self.saved = []

    def get_by_id(self, sale_id: UUID):
        return None

    def get_by_idempotency_key(self, key: str):
        return None

    def save(self, sale):
        self.saved.append(sale)


class StubInventory:
    def __init__(self):
        self.deductions = []

    def deduct_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        self.deductions.append((product_id, quantity, reference))

    def restore_stock(self, product_id: UUID, quantity: int, reference: str) -> None:
        pass

    def get_available_stock(self, product_id: UUID) -> int:
        return 100


class StubCatalog:
    def get_product(self, product_id: UUID):
        return {"name": "Sugar 1kg"}


class StubReceiptNumber:
    def generate(self) -> str:
        return "R-0001"


class StubIdempotency:
    def exists(self, key: str) -> bool:
        return False

    def store(self, key: str, sale_id: UUID) -> None:
        pass


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _use_case(repository, inventory):
    return CompleteSaleUseCase(
        repository,
        inventory,
        StubCatalog(),
        StubReceiptNumber(),
        StubIdempotency(),
        FixedClock(),
    )


def _command(**overrides):
    values = {
        "cashier_id": uuid4(),
        "lines": [
            LineItem(
                product_id=uuid4(),
                quantity=1,
                unit_price=Money(Decimal("25000")),
                unit_cost=Money(Decimal("20000")),
            )
        ],
        "payments": [
            PaymentInput(
                method=PaymentMethod.MOBILE_MONEY,
                amount=Money(Decimal("25000")),
                reference="MTN-123",
            )
        ],
        "idempotency_key": "key-1",
    }
    values.update(overrides)
    return CompleteSaleCommand(**values)


def test_the_expected_total_must_match_the_sale_total():
    repository = StubSaleRepository()
    inventory = StubInventory()

    with pytest.raises(InvalidPaymentError):
        _use_case(repository, inventory).execute(_command(expected_total=Money(Decimal("24000"))))

    assert repository.saved == []
    assert inventory.deductions == []


def test_a_matching_expected_total_completes_the_sale():
    repository = StubSaleRepository()
    inventory = StubInventory()

    sale = _use_case(repository, inventory).execute(
        _command(expected_total=Money(Decimal("25000")))
    )

    assert sale.total == Money(Decimal("25000"))
    assert repository.saved == [sale]
    assert len(inventory.deductions) == 1


def test_omitting_the_expected_total_keeps_the_old_behaviour():
    repository = StubSaleRepository()
    inventory = StubInventory()

    sale = _use_case(repository, inventory).execute(_command())

    assert sale.total == Money(Decimal("25000"))
    assert repository.saved == [sale]
