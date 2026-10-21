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


@pytest.fixture
def supplier(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.post("/api/v1/purchasing/suppliers/", {"name": "Acme"})
    assert response.status_code == 201
    return response.data


def _invoice_payload(supplier_id, number="INV-001"):
    return {
        "supplier_id": supplier_id,
        "invoice_number": number,
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-20",
        "lines": [
            {"product_name": "Rice", "quantity": 2, "unit_cost": "3000.00"},
            {"product_name": "Sugar", "quantity": 1, "unit_cost": "4000.00"},
        ],
    }


@pytest.mark.django_db
def test_manager_can_create_an_invoice(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )

    assert response.status_code == 201, response.data
    assert response.data["invoice_number"] == "INV-001"
    assert response.data["supplier_name"] == "Acme"
    assert response.data["total"] == "10000.00"
    assert response.data["balance"] == "10000.00"
    assert response.data["status"] == "unpaid"


@pytest.mark.django_db
def test_duplicate_invoice_number_for_same_supplier_is_rejected(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)
    first = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )
    second = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )

    assert first.status_code == 201
    assert second.status_code == 400
    assert "already exists" in second.data["detail"]


@pytest.mark.django_db
def test_invoice_requires_a_known_supplier(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.post(
        "/api/v1/purchasing/invoices/",
        _invoice_payload("00000000-0000-0000-0000-000000000000"),
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_partial_payments_track_the_balance(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )
    invoice_id = created.data["id"]

    partial = api_client.post(
        f"/api/v1/purchasing/invoices/{invoice_id}/payments/",
        {"amount": "4000.00"},
        format="json",
    )

    assert partial.status_code == 200
    assert partial.data["status"] == "partial"
    assert partial.data["amount_paid"] == "4000.00"
    assert partial.data["balance"] == "6000.00"

    final = api_client.post(
        f"/api/v1/purchasing/invoices/{invoice_id}/payments/",
        {"amount": "6000.00"},
        format="json",
    )

    assert final.status_code == 200
    assert final.data["status"] == "paid"
    assert final.data["balance"] == "0.00"


@pytest.mark.django_db
def test_payment_cannot_exceed_the_balance(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )

    response = api_client.post(
        f"/api/v1/purchasing/invoices/{created.data['id']}/payments/",
        {"amount": "10001.00"},
        format="json",
    )

    assert response.status_code == 400
    assert "outstanding balance" in response.data["detail"]


@pytest.mark.django_db
def test_unpaid_invoice_can_be_voided_but_paid_invoice_cannot(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)
    first = api_client.post(
        "/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json"
    )
    second = api_client.post(
        "/api/v1/purchasing/invoices/",
        _invoice_payload(supplier["id"], number="INV-002"),
        format="json",
    )
    api_client.post(
        f"/api/v1/purchasing/invoices/{second.data['id']}/payments/",
        {"amount": "10000.00"},
        format="json",
    )

    voided = api_client.post(
        f"/api/v1/purchasing/invoices/{first.data['id']}/void/",
        {"reason": "Duplicate"},
        format="json",
    )
    rejected = api_client.post(
        f"/api/v1/purchasing/invoices/{second.data['id']}/void/",
        {"reason": "Mistake"},
        format="json",
    )

    assert voided.status_code == 200
    assert voided.data["status"] == "void"
    assert rejected.status_code == 400


@pytest.mark.django_db
def test_invoices_can_be_filtered_by_status(api_client, manager_user, supplier):
    api_client.force_authenticate(user=manager_user)
    api_client.post("/api/v1/purchasing/invoices/", _invoice_payload(supplier["id"]), format="json")

    response = api_client.get("/api/v1/purchasing/invoices/?status=paid")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_cashier_cannot_manage_invoices(api_client, cashier_user, supplier):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/purchasing/invoices/")
    assert response.status_code == 403
