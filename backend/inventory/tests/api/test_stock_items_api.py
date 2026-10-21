import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
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
    return ProductModel.objects.create(name="Rice 5kg", sku="RIC-005")


@pytest.mark.django_db
def test_list_stock_items_returns_stocked_products(api_client, manager_user, product):
    api_client.force_authenticate(user=manager_user)
    api_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": str(product.id),
            "quantity": 7,
            "movement_type": "opening",
            "reason": "Opening stock",
        },
    )

    response = api_client.get("/api/v1/inventory/items/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["product_id"] == str(product.id)
    assert response.data[0]["product_name"] == "Rice 5kg"
    assert response.data[0]["sku"] == "RIC-005"
    assert response.data[0]["available_quantity"] == 7


@pytest.mark.django_db
def test_low_stock_items_include_product_name(api_client, manager_user, db):
    product = ProductModel.objects.create(name="Sugar 1kg", sku="SUG-001", minimum_stock_level=10)
    api_client.force_authenticate(user=manager_user)
    api_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": str(product.id),
            "quantity": 4,
            "movement_type": "opening",
            "reason": "Opening stock",
        },
    )

    response = api_client.get("/api/v1/inventory/low-stock/")

    assert response.status_code == 200
    assert response.data[0]["product_name"] == "Sugar 1kg"
    assert response.data[0]["sku"] == "SUG-001"


@pytest.mark.django_db
def test_out_of_stock_items_include_product_name(api_client, manager_user, product):
    api_client.force_authenticate(user=manager_user)
    api_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": str(product.id),
            "quantity": 5,
            "movement_type": "opening",
            "reason": "Opening stock",
        },
    )
    api_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": str(product.id),
            "quantity": 5,
            "movement_type": "adjustment_out",
            "reason": "Sold out",
        },
    )

    response = api_client.get("/api/v1/inventory/out-of-stock/")

    assert response.status_code == 200
    assert response.data[0]["product_name"] == "Rice 5kg"
    assert response.data[0]["sku"] == "RIC-005"


@pytest.mark.django_db
def test_never_stocked_product_is_out_of_stock(api_client, manager_user, product):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/inventory/out-of-stock/")

    assert response.status_code == 200
    assert [item["product_id"] for item in response.data] == [str(product.id)]


@pytest.mark.django_db
def test_never_stocked_product_below_minimum_is_low_stock(api_client, manager_user, db):
    product = ProductModel.objects.create(name="Salt 1kg", sku="SAL-001", minimum_stock_level=5)
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/inventory/low-stock/")

    assert response.status_code == 200
    assert [item["product_id"] for item in response.data] == [str(product.id)]


@pytest.mark.django_db
def test_inactive_products_are_not_out_of_stock(api_client, manager_user, db):
    ProductModel.objects.create(name="Old item", sku="OLD-001", is_active=False)
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/inventory/out-of-stock/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_unauthenticated_cannot_list_stock_items(api_client):
    response = api_client.get("/api/v1/inventory/items/")
    assert response.status_code == 403
