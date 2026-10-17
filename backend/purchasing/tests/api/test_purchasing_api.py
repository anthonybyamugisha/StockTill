import uuid

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


def _create_supplier(api_client, name="Acme Distributors"):
    return api_client.post(
        "/api/v1/purchasing/suppliers/",
        {
            "name": name,
            "contact_name": "Jane Doe",
            "email": "jane@acme.com",
            "phone": "+256700000000",
            "address": "Kampala",
        },
    )


@pytest.mark.django_db
def test_cashier_cannot_manage_suppliers(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    assert api_client.get("/api/v1/purchasing/suppliers/").status_code == 403


@pytest.mark.django_db
def test_manager_can_create_and_list_suppliers(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    created = _create_supplier(api_client)
    assert created.status_code == 201
    assert created.data["name"] == "Acme Distributors"

    listing = api_client.get("/api/v1/purchasing/suppliers/")
    assert listing.status_code == 200
    assert len(listing.data) == 1


@pytest.mark.django_db
def test_manager_can_update_a_supplier(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    supplier_id = _create_supplier(api_client).data["id"]

    response = api_client.patch(
        f"/api/v1/purchasing/suppliers/{supplier_id}/",
        {"name": "Acme Ltd", "phone": "+256711111111"},
    )

    assert response.status_code == 200
    assert response.data["name"] == "Acme Ltd"


@pytest.mark.django_db
def test_purchase_order_lifecycle_and_stock_intake(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    supplier_id = _create_supplier(api_client).data["id"]
    product_id = str(uuid.uuid4())

    created = api_client.post(
        "/api/v1/purchasing/orders/",
        {
            "supplier_id": supplier_id,
            "reference": "PO-001",
            "lines": [{"product_id": product_id, "quantity": 12, "unit_cost": "2000.00"}],
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.data["status"] == "draft"
    assert str(created.data["total"]) == "24000.00"
    order_id = created.data["id"]

    ordered = api_client.post(f"/api/v1/purchasing/orders/{order_id}/order/")
    assert ordered.status_code == 200
    assert ordered.data["status"] == "ordered"

    received = api_client.post(f"/api/v1/purchasing/orders/{order_id}/receive/")
    assert received.status_code == 200
    assert received.data["status"] == "received"

    stock = api_client.get(f"/api/v1/inventory/items/{product_id}/")
    assert stock.status_code == 200
    assert stock.data["quantity_on_hand"] == 12


@pytest.mark.django_db
def test_cannot_create_order_for_unknown_supplier(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/purchasing/orders/",
        {
            "supplier_id": str(uuid.uuid4()),
            "lines": [{"product_id": str(uuid.uuid4()), "quantity": 1, "unit_cost": "1000.00"}],
        },
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_cancelling_a_purchase_order(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    supplier_id = _create_supplier(api_client).data["id"]
    order_id = api_client.post(
        "/api/v1/purchasing/orders/",
        {
            "supplier_id": supplier_id,
            "lines": [{"product_id": str(uuid.uuid4()), "quantity": 1, "unit_cost": "1000.00"}],
        },
        format="json",
    ).data["id"]

    response = api_client.post(
        f"/api/v1/purchasing/orders/{order_id}/cancel/", {"reason": "changed mind"}
    )

    assert response.status_code == 200
    assert response.data["status"] == "cancelled"
