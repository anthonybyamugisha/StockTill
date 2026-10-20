from decimal import Decimal
from uuid import UUID, uuid4

from sales.application.commands import LineItem
from sales.application.sale_lines import build_sale_line, build_sale_lines
from sales.domain.entities import DiscountType
from shared.domain.money import Money


class StubCatalog:
    def __init__(self, names: dict[UUID, str]):
        self._names = names
        self.lookups = 0

    def get_product(self, product_id: UUID):
        self.lookups += 1
        name = self._names.get(product_id)
        return {"name": name} if name else None


def _item(product_id: UUID, **overrides) -> LineItem:
    values = {
        "product_id": product_id,
        "quantity": 2,
        "unit_price": Money(Decimal("500.00")),
        "unit_cost": Money(Decimal("300.00")),
    }
    values.update(overrides)
    return LineItem(**values)


def test_keeps_the_name_supplied_by_the_client():
    product_id = uuid4()
    catalog = StubCatalog({product_id: "From the catalog"})

    line = build_sale_line(_item(product_id, product_name="From the client"), catalog)

    assert line.product_name == "From the client"
    assert catalog.lookups == 0


def test_fills_a_missing_name_from_the_catalog():
    product_id = uuid4()
    catalog = StubCatalog({product_id: "Sugar 1kg"})

    line = build_sale_line(_item(product_id), catalog)

    assert line.product_name == "Sugar 1kg"


def test_leaves_the_name_empty_when_the_product_is_unknown():
    catalog = StubCatalog({})

    line = build_sale_line(_item(uuid4()), catalog)

    assert line.product_name == ""


def test_turns_a_percentage_discount_into_an_amount():
    catalog = StubCatalog({})

    line = build_sale_line(
        _item(
            uuid4(),
            product_name="Soap",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
        ),
        catalog,
    )

    assert line.discount is not None
    assert line.discount.amount.amount == Decimal("100.00")


def test_builds_one_line_per_item_in_order():
    catalog = StubCatalog({})

    lines = build_sale_lines(
        [_item(uuid4(), product_name="A"), _item(uuid4(), product_name="B")], catalog
    )

    assert [line.product_name for line in lines] == ["A", "B"]
