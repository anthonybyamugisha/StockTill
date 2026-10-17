import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel


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
def product(db):
    return ProductModel.objects.create(
        name="Sugar 1kg",
        sku="SUG-001",
        selling_price="5000.00",
        buying_cost="4000.00",
    )


@pytest.mark.django_db
def test_creating_and_updating_a_supplier_is_recorded(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post(
        "/api/v1/purchasing/suppliers/",
        {"name": "Acme", "contact_name": "Jane", "email": "jane@acme.com"},
    )

    api_client.patch(
        f"/api/v1/purchasing/suppliers/{created.data['id']}/",
        {"name": "Acme Ltd", "contact_name": "Jane", "email": "jane@acme.com"},
    )

    repo = DjangoAuditRepository()
    assert len(repo.list_entries(action="supplier.created")) == 1
    updates = repo.list_entries(action="supplier.updated")
    assert len(updates) == 1
    assert updates[0].before == {"name": "Acme"}
    assert updates[0].after == {"name": "Acme Ltd"}


@pytest.mark.django_db
def test_purchase_order_lifecycle_is_recorded(api_client, manager_user, product):
    api_client.force_authenticate(user=manager_user)
    supplier = api_client.post(
        "/api/v1/purchasing/suppliers/",
        {"name": "Acme", "contact_name": "Jane", "email": "jane@acme.com"},
    )
    order = api_client.post(
        "/api/v1/purchasing/orders/",
        {
            "supplier_id": supplier.data["id"],
            "reference": "PO-001",
            "notes": "",
            "lines": [
                {
                    "product_id": str(product.id),
                    "product_name": "Sugar 1kg",
                    "quantity": 10,
                    "unit_cost": "4000.00",
                }
            ],
        },
        format="json",
    )
    order_id = order.data["id"]

    created = DjangoAuditRepository().list_entries(action="purchase_order.created")
    assert len(created) == 1
    assert created[0].after["supplier_name"] == "Acme"
    assert created[0].after["reference"] == "PO-001"

    api_client.post(f"/api/v1/purchasing/orders/{order_id}/order/")
    ordered = DjangoAuditRepository().list_entries(action="purchase_order.ordered")
    assert len(ordered) == 1
    assert ordered[0].before == {"status": "draft"}
    assert ordered[0].after["status"] == "ordered"

    api_client.post(f"/api/v1/purchasing/orders/{order_id}/receive/")
    received = DjangoAuditRepository().list_entries(action="purchase_order.received")
    assert len(received) == 1
    assert received[0].after["status"] == "received"


@pytest.mark.django_db
def test_cancelling_a_purchase_order_is_recorded(api_client, manager_user, product):
    api_client.force_authenticate(user=manager_user)
    supplier = api_client.post(
        "/api/v1/purchasing/suppliers/",
        {"name": "Acme", "contact_name": "Jane", "email": "jane@acme.com"},
    )
    order = api_client.post(
        "/api/v1/purchasing/orders/",
        {
            "supplier_id": supplier.data["id"],
            "reference": "PO-002",
            "notes": "",
            "lines": [
                {
                    "product_id": str(product.id),
                    "product_name": "Sugar 1kg",
                    "quantity": 5,
                    "unit_cost": "4000.00",
                }
            ],
        },
        format="json",
    )

    api_client.post(
        f"/api/v1/purchasing/orders/{order.data['id']}/cancel/",
        {"reason": "supplier out of stock"},
        format="json",
    )

    entries = DjangoAuditRepository().list_entries(action="purchase_order.cancelled")
    assert len(entries) == 1
    assert entries[0].after["status"] == "cancelled"
    assert entries[0].after["reason"] == "supplier out of stock"
