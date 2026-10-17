import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher

PRODUCT_PAYLOAD = {
    "name": "Sugar 1kg",
    "sku": "SUG-001",
    "selling_price": "5000.00",
    "buying_cost": "4000.00",
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


@pytest.mark.django_db
def test_creating_a_product_is_recorded(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    entries = DjangoAuditRepository().list_entries(action="product.created")
    assert len(entries) == 1
    assert entries[0].entity_id == response.data["id"]
    assert entries[0].user_id == manager_user.id
    assert entries[0].after["sku"] == "SUG-001"
    assert entries[0].after["selling_price"] == "5000.00"


@pytest.mark.django_db
def test_opening_stock_on_creation_is_recorded(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/catalog/products/", {**PRODUCT_PAYLOAD, "opening_stock": 25}
    )

    entries = DjangoAuditRepository().list_entries(action="stock.opening")
    assert len(entries) == 1
    assert entries[0].entity_id == response.data["id"]
    assert entries[0].after["quantity_on_hand"] == 25


@pytest.mark.django_db
def test_price_change_is_recorded_as_a_diff(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    api_client.patch(
        f"/api/v1/catalog/products/{created.data['id']}/",
        {"selling_price": "6500.00"},
        format="json",
    )

    entries = DjangoAuditRepository().list_entries(action="product.updated")
    assert len(entries) == 1
    assert entries[0].before == {"selling_price": "5000.00"}
    assert entries[0].after == {"selling_price": "6500.00"}


@pytest.mark.django_db
def test_deactivating_a_product_is_recorded(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/products/", PRODUCT_PAYLOAD)

    api_client.delete(f"/api/v1/catalog/products/{created.data['id']}/")

    entries = DjangoAuditRepository().list_entries(action="product.deactivated")
    assert len(entries) == 1
    assert entries[0].entity_id == created.data["id"]
    assert entries[0].after["is_active"] is False


@pytest.mark.django_db
def test_creating_and_deleting_a_category_are_recorded(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    created = api_client.post("/api/v1/catalog/categories/", {"name": "Snacks"})
    api_client.delete(f"/api/v1/catalog/categories/{created.data['id']}/")

    events = {entry.action for entry in DjangoAuditRepository().list_entries()}
    assert "category.created" in events
    assert "category.deactivated" in events
