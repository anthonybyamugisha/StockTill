from uuid import uuid4

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from payments.infrastructure.models import PaymentIntentModel
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
def cashier(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.fixture
def other_cashier(db):
    return _make_user("other@shop.com", Role.CASHIER)


@pytest.fixture
def manager(db):
    return _make_user("manager@shop.com", Role.MANAGER)


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


def _payload(product_id, key=None, **overrides):
    payload = {
        "method": "mobile_money",
        "amount": "50000.00",
        "phone": "0772123456",
        "network": "mtn",
        "idempotency_key": key or uuid4().hex,
        "sale": {
            "lines": [
                {
                    "product_id": str(product_id),
                    "product_name": "Rice 5kg",
                    "quantity": 2,
                    "unit_price": "25000.00",
                    "unit_cost": "20000.00",
                }
            ],
        },
    }
    payload.update(overrides)
    return payload


def _create_intent(api_client, product_id, key=None, **overrides):
    return api_client.post(
        "/api/v1/payments/intents/",
        _payload(product_id, key, **overrides),
        format="json",
    )


@pytest.mark.django_db
def test_cashier_can_request_a_mobile_money_payment(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)

    response = _create_intent(api_client, stocked_product.id)

    assert response.status_code == 201, response.data
    assert response.data["status"] == "pending"
    assert response.data["method"] == "mobile_money"
    assert response.data["network"] == "mtn"
    assert response.data["phone"] == "256772123456"
    assert response.data["amount"] == "50000.00"
    assert response.data["currency"] == "UGX"
    assert response.data["provider"] == "fake-mtn"
    assert response.data["tx_ref"].startswith("PAY-")


@pytest.mark.django_db
def test_a_replayed_idempotency_key_returns_the_same_intent(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    key = uuid4().hex

    first = _create_intent(api_client, stocked_product.id, key)
    second = _create_intent(api_client, stocked_product.id, key)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.data["id"] == second.data["id"]
    assert PaymentIntentModel.objects.count() == 1


@pytest.mark.django_db
def test_the_callback_completes_the_sale_and_reduces_stock(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data

    callback = api_client.post(
        "/api/v1/payments/callbacks/mtn/",
        {"tx_ref": intent["tx_ref"], "status": "successful"},
        format="json",
    )

    assert callback.status_code == 200, callback.data
    assert callback.data["status"] == "paid"

    detail = api_client.get(f"/api/v1/payments/intents/{intent['id']}/")
    assert detail.data["status"] == "paid"
    assert detail.data["sale_id"] is not None

    sale = api_client.get(f"/api/v1/sales/{detail.data['sale_id']}/")
    assert sale.status_code == 200
    assert sale.data["total"] == "50000.00"
    assert sale.data["payments"][0]["method"] == "mobile_money"
    assert sale.data["payments"][0]["provider"] == "fake-mtn"
    assert sale.data["payments"][0]["reference"].startswith("fake-")

    stock = StockItemModel.objects.get(product_id=stocked_product.id)
    assert stock.quantity_on_hand == 8


@pytest.mark.django_db
def test_mtn_can_deliver_the_callback_with_put(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data

    callback = api_client.put(
        "/api/v1/payments/callbacks/mtn/",
        {"tx_ref": intent["tx_ref"], "status": "successful"},
        format="json",
    )

    assert callback.status_code == 200, callback.data
    assert callback.data["status"] == "paid"
    stock = StockItemModel.objects.get(product_id=stocked_product.id)
    assert stock.quantity_on_hand == 8


@pytest.mark.django_db
def test_a_replayed_callback_does_not_complete_a_second_sale(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data
    payload = {"tx_ref": intent["tx_ref"], "status": "successful"}

    first = api_client.post("/api/v1/payments/callbacks/mtn/", payload, format="json")
    second = api_client.post("/api/v1/payments/callbacks/mtn/", payload, format="json")

    assert first.status_code == 200
    assert second.status_code == 200
    stock = StockItemModel.objects.get(product_id=stocked_product.id)
    assert stock.quantity_on_hand == 8


@pytest.mark.django_db
def test_cash_is_not_sent_through_the_gateway(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)

    response = _create_intent(api_client, stocked_product.id, method="cash")

    assert response.status_code == 400
    assert PaymentIntentModel.objects.count() == 0


@pytest.mark.django_db
def test_an_unknown_network_is_rejected(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)

    response = _create_intent(api_client, stocked_product.id, network="vodafone")

    assert response.status_code == 400
    assert PaymentIntentModel.objects.count() == 0


@pytest.mark.django_db
def test_a_cashier_cannot_read_another_cashiers_payment(
    api_client, cashier, other_cashier, stocked_product
):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data

    api_client.force_authenticate(user=other_cashier)
    response = api_client.get(f"/api/v1/payments/intents/{intent['id']}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_a_cashier_can_cancel_an_unpaid_payment(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data

    response = api_client.post(
        f"/api/v1/payments/intents/{intent['id']}/cancel/",
        {"reason": "Customer changed their mind"},
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["status"] == "cancelled"
    assert response.data["failure_reason"] == "Customer changed their mind"


@pytest.mark.django_db
def test_a_cancelled_payment_cannot_be_confirmed(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data
    api_client.post(f"/api/v1/payments/intents/{intent['id']}/cancel/", {}, format="json")

    response = api_client.post(
        "/api/v1/payments/callbacks/mtn/",
        {"tx_ref": intent["tx_ref"], "status": "successful"},
        format="json",
    )

    assert response.status_code == 400
    stock = StockItemModel.objects.get(product_id=stocked_product.id)
    assert stock.quantity_on_hand == 10


@pytest.mark.django_db
def test_an_unknown_callback_is_not_found(api_client):
    response = api_client.post(
        "/api/v1/payments/callbacks/mtn/",
        {"tx_ref": "PAY-DOESNOTEXIST", "status": "successful"},
        format="json",
    )

    assert response.status_code == 404


@override_settings(PAYMENTS_CALLBACK_SECRET="s3cret")
@pytest.mark.django_db
def test_the_callback_token_must_match_when_configured(api_client, cashier, stocked_product):
    api_client.force_authenticate(user=cashier)
    intent = _create_intent(api_client, stocked_product.id).data
    payload = {"tx_ref": intent["tx_ref"], "status": "successful"}

    forbidden = api_client.post(
        "/api/v1/payments/callbacks/mtn/?token=wrong", payload, format="json"
    )
    accepted = api_client.post(
        "/api/v1/payments/callbacks/mtn/?token=s3cret", payload, format="json"
    )

    assert forbidden.status_code == 403
    assert accepted.status_code == 200


@pytest.mark.django_db
def test_a_manager_can_list_every_cashiers_payments(
    api_client, cashier, other_cashier, manager, stocked_product
):
    api_client.force_authenticate(user=cashier)
    _create_intent(api_client, stocked_product.id)
    api_client.force_authenticate(user=other_cashier)
    _create_intent(api_client, stocked_product.id)

    api_client.force_authenticate(user=manager)
    response = api_client.get("/api/v1/payments/intents/")

    assert response.status_code == 200
    assert len(response.data) == 2


@pytest.mark.django_db
def test_a_cashier_only_lists_their_own_payments(
    api_client, cashier, other_cashier, stocked_product
):
    api_client.force_authenticate(user=cashier)
    _create_intent(api_client, stocked_product.id)
    api_client.force_authenticate(user=other_cashier)

    response = api_client.get("/api/v1/payments/intents/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_an_unknown_status_filter_is_rejected(api_client, cashier):
    api_client.force_authenticate(user=cashier)

    response = api_client.get("/api/v1/payments/intents/?status=banana")

    assert response.status_code == 400
    assert "banana" in response.data["detail"]


@pytest.mark.django_db
def test_creating_a_payment_requires_authentication(api_client, stocked_product):
    response = _create_intent(api_client, stocked_product.id)

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_cashier_discount_limit_is_checked_before_a_mobile_prompt(
    api_client, cashier, stocked_product
):
    BusinessSettingsModel.objects.update_or_create(
        key="main", defaults={"cashier_discount_limit": "10.00"}
    )
    api_client.force_authenticate(user=cashier)
    payload = _payload(stocked_product.id)
    payload["sale"]["lines"][0]["discount_type"] = "percentage"
    payload["sale"]["lines"][0]["discount_value"] = "11.00"

    response = api_client.post("/api/v1/payments/intents/", payload, format="json")

    assert response.status_code == 400
    assert "limited to 10" in response.data["detail"]
    assert not PaymentIntentModel.objects.exists()
