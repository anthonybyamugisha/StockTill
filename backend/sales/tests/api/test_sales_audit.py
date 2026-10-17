from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel


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
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.fixture
def manager_user(db):
    return _make_user("manager@shop.com", Role.MANAGER)


@pytest.fixture
def stocked_product(db):
    product = ProductModel.objects.create(
        name="Rice 5kg",
        sku="RIC-005",
        selling_price="25000.00",
        buying_cost="20000.00",
    )
    StockItemModel.objects.create(product_id=product.id, quantity_on_hand=10)
    return product


def _payload(product_id):
    return {
        "lines": [
            {
                "product_id": str(product_id),
                "product_name": "Rice 5kg",
                "quantity": 2,
                "unit_price": "25000.00",
                "unit_cost": "20000.00",
            }
        ],
        "payments": [{"method": "cash", "amount": "50000.00", "tendered": "50000.00"}],
        "idempotency_key": uuid4().hex,
    }


@pytest.mark.django_db
def test_completing_a_sale_is_recorded(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)

    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")

    entries = DjangoAuditRepository().list_entries(action="sale.completed")
    assert len(entries) == 1
    assert entries[0].entity_id == sale.data["id"]
    assert entries[0].user_id == cashier_user.id
    assert entries[0].after["total"] == "50000.00"
    assert entries[0].after["line_count"] == 1
    assert entries[0].after["payment_methods"] == ["cash"]


@pytest.mark.django_db
def test_voiding_a_sale_is_recorded(api_client, cashier_user, manager_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")

    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/v1/sales/void/",
        {"sale_id": sale.data["id"], "reason": "customer changed mind"},
        format="json",
    )
    assert response.status_code == 200

    entries = DjangoAuditRepository().list_entries(action="sale.voided")
    assert len(entries) == 1
    assert entries[0].entity_id == sale.data["id"]
    assert entries[0].user_id == manager_user.id
    assert entries[0].before["status"] == "completed"
    assert entries[0].after["status"] == "voided"
    assert entries[0].after["reason"] == "customer changed mind"
