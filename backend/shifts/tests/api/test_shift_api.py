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
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.mark.django_db
def test_unauthenticated_cannot_open_shift(api_client):
    response = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_cashier_can_open_a_shift(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.post(
        "/api/v1/shifts/open/", {"opening_float": "100000.00", "notes": "morning"}
    )

    assert response.status_code == 201
    assert response.data["status"] == "open"
    assert response.data["opening_float"] == "100000.00"


@pytest.mark.django_db
def test_cannot_open_two_shifts_for_the_same_cashier(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})

    response = api_client.post("/api/v1/shifts/open/", {"opening_float": "50000.00"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_current_shift_returns_the_open_shift(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})

    response = api_client.get("/api/v1/shifts/current/")

    assert response.status_code == 200
    assert response.data["shift"]["id"] == opened.data["id"]


@pytest.mark.django_db
def test_current_shift_is_null_when_none_open(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/shifts/current/")
    assert response.status_code == 200
    assert response.data["shift"] is None


@pytest.mark.django_db
def test_cash_movement_changes_expected_cash(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})
    shift_id = opened.data["id"]

    movement = api_client.post(
        "/api/v1/shifts/cash-movement/",
        {"shift_id": shift_id, "type": "payout", "amount": "30000.00", "reason": "taxi"},
    )
    assert movement.status_code == 201

    report = api_client.get(f"/api/v1/shifts/{shift_id}/")
    assert report.status_code == 200
    assert str(report.data["expected_cash"]) == "70000.00"


@pytest.mark.django_db
def test_closing_a_shift_reports_variance(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})
    shift_id = opened.data["id"]

    response = api_client.post(
        "/api/v1/shifts/close/",
        {"shift_id": shift_id, "counted_cash": "99000.00"},
    )

    assert response.status_code == 200
    assert str(response.data["expected_cash"]) == "100000.00"
    assert str(response.data["variance"]) == "-1000.00"
    assert response.data["shift"]["status"] == "closed"


@pytest.mark.django_db
def test_closing_includes_recorded_cash_movements(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    opened = api_client.post("/api/v1/shifts/open/", {"opening_float": "100000.00"})
    shift_id = opened.data["id"]
    api_client.post(
        "/api/v1/shifts/cash-movement/",
        {"shift_id": shift_id, "type": "payout", "amount": "25000.00", "reason": "transport"},
    )

    response = api_client.post(
        "/api/v1/shifts/close/",
        {"shift_id": shift_id, "counted_cash": "74000.00"},
    )

    assert response.status_code == 200
    assert str(response.data["net_cash_movements"]) == "-25000.00"
    assert str(response.data["expected_cash"]) == "75000.00"
    assert str(response.data["variance"]) == "-1000.00"


@pytest.mark.django_db
def test_report_for_unknown_shift_returns_404(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/shifts/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404
