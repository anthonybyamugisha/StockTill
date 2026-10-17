import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher


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


@pytest.fixture
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


PRODUCT_PAYLOAD = {
    "name": "Rice 5kg",
    "sku": "RIC-005",
    "selling_price": "25000.00",
    "buying_cost": "20000.00",
}


@pytest.mark.django_db
def test_unauthenticated_cannot_list_products(api_client):
    response = api_client.get("/api/v1/catalog/products/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_cashier_can_list_products(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/catalog/products/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_cashier_cannot_create_product(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)
    assert response.status_code == 403


@pytest.mark.django_db
def test_manager_can_create_product(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)
    assert response.status_code == 201
    assert response.data["sku"] == "RIC-005"
