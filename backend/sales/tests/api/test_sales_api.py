from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from settings.infrastructure.models import BusinessSettingsModel


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
def product(db):
    return ProductModel.objects.create(
        name="Rice 5kg",
        sku="RIC-005",
        selling_price="25000.00",
        buying_cost="20000.00",
    )


@pytest.fixture
def stocked_product(db, product):
    StockItemModel.objects.create(product_id=product.id, quantity_on_hand=10)
    return product


def _payload(product_id, key=None):
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
        "idempotency_key": key or uuid4().hex,
    }


@pytest.mark.django_db
def test_cashier_can_complete_sale(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")

    assert response.status_code == 201, response.data
    assert response.data["total"] == "50000.00"
    assert response.data["status"] == "completed"

    stock = StockItemModel.objects.get(product_id=stocked_product.id)
    assert stock.quantity_on_hand == 8


@pytest.mark.django_db
def test_replayed_idempotency_key_returns_same_sale(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    key = uuid4().hex
    payload = _payload(stocked_product.id, key)

    first = api_client.post("/api/v1/sales/", payload, format="json")
    second = api_client.post("/api/v1/sales/", payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.data["id"] == second.data["id"]


@pytest.mark.django_db
def test_sale_without_stock_returns_400(api_client, cashier_user, product):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.post("/api/v1/sales/", _payload(product.id), format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_sale_line_uses_the_catalog_product_name_when_omitted(
    api_client, cashier_user, stocked_product
):
    api_client.force_authenticate(user=cashier_user)
    payload = _payload(stocked_product.id)
    del payload["lines"][0]["product_name"]

    response = api_client.post("/api/v1/sales/", payload, format="json")

    assert response.status_code == 201, response.data
    assert response.data["lines"][0]["product_name"] == "Rice 5kg"


@pytest.mark.django_db
def test_cashier_cannot_refund(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")

    response = api_client.post(
        "/api/v1/sales/refund/",
        {"sale_id": sale.data["id"], "quantity": 1, "reason": "test", "restock": True},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_sale_list_filters_by_status(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")

    completed = api_client.get("/api/v1/sales/?status=completed")
    assert completed.status_code == 200, completed.data
    assert [s["receipt_number"] for s in completed.data] == [sale.data["receipt_number"]]

    voided = api_client.get("/api/v1/sales/?status=voided")

    assert voided.status_code == 200
    assert voided.data == []


@pytest.mark.django_db
def test_sale_list_rejects_an_unknown_status(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.get("/api/v1/sales/?status=banana")

    assert response.status_code == 400
    assert "banana" in response.data["detail"]


@pytest.mark.django_db
def test_cashier_only_sees_their_own_sales(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")
    other_cashier = _make_user("other@shop.com", Role.CASHIER)

    api_client.force_authenticate(user=other_cashier)
    response = api_client.get(f"/api/v1/sales/?cashier_id={cashier_user.id}")

    assert response.status_code == 200
    assert response.data == []
    assert api_client.get(f"/api/v1/sales/{sale.data['id']}/").status_code == 404


@pytest.mark.django_db
def test_manager_can_filter_sales_by_cashier(api_client, cashier_user, stocked_product):
    api_client.force_authenticate(user=cashier_user)
    sale = api_client.post("/api/v1/sales/", _payload(stocked_product.id), format="json")
    manager = _make_user("manager@shop.com", Role.MANAGER)

    api_client.force_authenticate(user=manager)
    response = api_client.get(f"/api/v1/sales/?cashier_id={cashier_user.id}")

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [sale.data["id"]]


@pytest.mark.django_db
def test_cashier_discount_is_limited_by_settings(api_client, cashier_user, stocked_product):
    BusinessSettingsModel.objects.update_or_create(
        key="main", defaults={"cashier_discount_limit": "10.00"}
    )
    api_client.force_authenticate(user=cashier_user)
    payload = _payload(stocked_product.id)
    payload["lines"][0]["discount_type"] = "percentage"
    payload["lines"][0]["discount_value"] = "11.00"
    payload["payments"][0]["amount"] = "44500.00"
    payload["payments"][0]["tendered"] = "44500.00"

    response = api_client.post("/api/v1/sales/", payload, format="json")

    assert response.status_code == 400
    assert "limited to 10" in response.data["detail"]


@pytest.mark.django_db
def test_manager_can_apply_a_larger_discount(api_client, stocked_product):
    BusinessSettingsModel.objects.update_or_create(
        key="main", defaults={"cashier_discount_limit": "10.00"}
    )
    manager = _make_user("manager@shop.com", Role.MANAGER)
    api_client.force_authenticate(user=manager)
    payload = _payload(stocked_product.id)
    payload["lines"][0]["discount_type"] = "percentage"
    payload["lines"][0]["discount_value"] = "50.00"
    payload["payments"][0]["amount"] = "25000.00"
    payload["payments"][0]["tendered"] = "25000.00"

    response = api_client.post("/api/v1/sales/", payload, format="json")

    assert response.status_code == 201, response.data
    assert response.data["total"] == "25000.00"


@pytest.mark.django_db
def test_sale_list_rejects_an_invalid_cashier_id(api_client, cashier_user):
    manager = _make_user("manager@shop.com", Role.MANAGER)
    api_client.force_authenticate(user=manager)

    response = api_client.get("/api/v1/sales/?cashier_id=not-a-uuid")

    assert response.status_code == 400
