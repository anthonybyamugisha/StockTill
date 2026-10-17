import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from sales.infrastructure.adapters import InventoryAdapter


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
        name="Rice 5kg",
        sku="RIC-005",
        selling_price="25000.00",
        buying_cost="20000.00",
    )


@pytest.mark.django_db
def test_manual_adjustment_is_recorded_with_before_and_after(api_client, manager_user, product):
    StockItemModel.objects.create(product_id=product.id, quantity_on_hand=10)
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": str(product.id),
            "quantity": 3,
            "movement_type": "write_off",
            "reason": "Damaged in transit",
        },
        format="json",
    )
    assert response.status_code == 201, response.data

    entries = DjangoAuditRepository().list_entries(action="stock.adjusted")
    assert len(entries) == 1
    assert entries[0].entity_id == str(product.id)
    assert entries[0].user_id == manager_user.id
    assert entries[0].before == {"quantity_on_hand": 10}
    assert entries[0].after["quantity_on_hand"] == 7
    assert entries[0].after["movement_type"] == "write_off"


@pytest.mark.django_db
def test_automatic_sale_stock_movement_is_not_audited(db, product):
    StockItemModel.objects.create(product_id=product.id, quantity_on_hand=10)

    InventoryAdapter().deduct_stock(product.id, 2, "ST-2026-000001")

    assert DjangoAuditRepository().list_entries(action="stock.adjusted") == []
