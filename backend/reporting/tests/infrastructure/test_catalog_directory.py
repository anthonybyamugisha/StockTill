from uuid import uuid4

import pytest

from catalog.infrastructure.models import ProductModel
from reporting.infrastructure.directories import CatalogDirectory


@pytest.mark.django_db
def test_loads_every_product_by_id():
    product = ProductModel.objects.create(
        name="Sugar 1kg", sku="SUG-001", buying_cost="1000.00", selling_price="1500.00"
    )

    catalog = CatalogDirectory.load()

    assert catalog.get(product.id).name == "Sugar 1kg"


@pytest.mark.django_db
def test_returns_none_for_an_unknown_product():
    assert CatalogDirectory.load().get(uuid4()) is None
