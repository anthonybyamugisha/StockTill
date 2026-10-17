import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from inventory.infrastructure.models import StockItemModel, StockMovementModel


def _make_user(email, role):
    user = User(email=email, first_name=role, last_name="User", role=role)
    user.set_password("password123", DjangoPasswordHasher())
    return UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def manager_user(db):
    return _make_user("manager@shop.com", Role.MANAGER)


PRODUCT_PAYLOAD = {
    "name": "Sugar 1kg",
    "sku": "SUG-001",
    "selling_price": "5000.00",
    "buying_cost": "4000.00",
}


@pytest.mark.django_db
def test_creating_a_product_with_opening_stock_records_it(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/catalog/products/", {**PRODUCT_PAYLOAD, "opening_stock": 25}
    )

    assert response.status_code == 201, response.data
    product_id = response.data["id"]

    item = StockItemModel.objects.get(product_id=product_id)
    assert item.quantity_on_hand == 25

    movement = StockMovementModel.objects.get(product_id=product_id)
    assert movement.movement_type == "opening"
    assert movement.quantity == 25


@pytest.mark.django_db
def test_creating_a_product_without_opening_stock_creates_no_stock(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    assert response.status_code == 201, response.data
    product_id = response.data["id"]
    assert not StockItemModel.objects.filter(product_id=product_id).exists()
    assert not StockMovementModel.objects.filter(product_id=product_id).exists()
