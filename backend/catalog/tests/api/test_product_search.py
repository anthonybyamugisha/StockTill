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
def test_search_matches_name(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    response = api_client.get("/api/v1/catalog/products/", {"q": "rice"})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["sku"] == "RIC-005"


@pytest.mark.django_db
def test_search_matches_sku(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    response = api_client.get("/api/v1/catalog/products/", {"q": "RIC-00"})

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_search_matches_barcode(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    api_client.post(
        "/api/v1/catalog/products/",
        {**PRODUCT_PAYLOAD, "barcode": "5901234123457"},
    )

    response = api_client.get("/api/v1/catalog/products/", {"q": "5901234123457"})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["barcode"] == "5901234123457"


@pytest.mark.django_db
def test_search_excludes_deactivated_products(api_client, manager_user, cashier_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)
    api_client.delete(f"/api/v1/catalog/products/{created.data['id']}/")

    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/catalog/products/", {"q": "rice"})

    assert response.status_code == 200
    assert response.data == []
