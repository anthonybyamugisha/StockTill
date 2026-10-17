import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
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
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.mark.django_db
def test_opening_a_shift_is_recorded(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})

    entries = DjangoAuditRepository().list_entries(action="shift.opened")
    assert len(entries) == 1
    assert entries[0].entity_id == opened.data["id"]
    assert entries[0].user_id == cashier_user.id
    assert entries[0].after["opening_float"] == "100000.00"


@pytest.mark.django_db
def test_cash_movement_is_recorded(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})

    api_client.post(
        "/api/v1/shifts/cash-movement/",
        {
            "shift_id": opened.data["id"],
            "type": "payout",
            "amount": "30000.00",
            "reason": "taxi",
        },
    )

    entries = DjangoAuditRepository().list_entries(action="shift.cash_movement")
    assert len(entries) == 1
    assert entries[0].after["type"] == "payout"
    assert entries[0].after["amount"] == "30000.00"


@pytest.mark.django_db
def test_closing_a_shift_records_the_variance(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})

    api_client.post(
        "/api/v1/shifts/close/",
        {"shift_id": opened.data["id"], "counted_cash": "99000.00"},
    )

    entries = DjangoAuditRepository().list_entries(action="shift.closed")
    assert len(entries) == 1
    assert entries[0].after["expected_cash"] == "100000.00"
    assert entries[0].after["variance"] == "-1000.00"
