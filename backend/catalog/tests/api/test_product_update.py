import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher

PRODUCT_PAYLOAD = {
    "name": "Rice 5kg",
    "sku": "RIC-005",
    "selling_price": "25000.00",
    "buying_cost": "20000.00",
}


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


@pytest.mark.django_db
def test_manager_can_update_product_name_and_sku(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)
    product_id = created.data["id"]

    response = api_client.patch(
        f"/api/v1/catalog/products/{product_id}/",
        {"name": "Rice 10kg", "sku": "RIC-010"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["name"] == "Rice 10kg"
    assert response.data["sku"] == "RIC-010"


@pytest.mark.django_db
def test_update_rejects_duplicate_sku(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    first = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)
    second = api_client.post(
        "/api/v1/catalog/products/",
        {**PRODUCT_PAYLOAD, "sku": "RIC-006"},
    )

    response = api_client.patch(
        f"/api/v1/catalog/products/{second.data['id']}/",
        {"sku": "RIC-005"},
        format="json",
    )

    assert response.status_code == 400
    assert first.status_code == 201


@pytest.mark.django_db
def test_cashier_cannot_update_product(api_client, cashier_user, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    api_client.force_authenticate(user=cashier_user)
    response = api_client.patch(
        f"/api/v1/catalog/products/{created.data['id']}/",
        {"name": "Nope"},
        format="json",
    )

    assert response.status_code == 403
