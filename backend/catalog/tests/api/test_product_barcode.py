import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher

PRODUCT_PAYLOAD = {
    "name": "Rice 5kg",
    "sku": "RIC-005",
    "barcode": "5901234123457",
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
def test_cashier_can_lookup_product_by_barcode(api_client, manager_user, cashier_user):
    api_client.force_authenticate(user=manager_user)
    api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/catalog/products/by-barcode/", {"barcode": "5901234123457"})

    assert response.status_code == 200
    assert response.data["sku"] == "RIC-005"


@pytest.mark.django_db
def test_unknown_barcode_returns_404(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/catalog/products/by-barcode/", {"barcode": "0000000000000"})
    assert response.status_code == 404


@pytest.mark.django_db
def test_missing_barcode_returns_400(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/catalog/products/by-barcode/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_barcode_lookup_is_rejected(api_client):
    response = api_client.get("/api/v1/catalog/products/by-barcode/", {"barcode": "5901234123457"})
    assert response.status_code == 403
