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
def admin_user(db):
    return _make_user("admin@shop.com", Role.ADMIN)


@pytest.fixture
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.mark.django_db
def test_successful_login_is_recorded(api_client, cashier_user):
    api_client.post(
        "/api/v1/accounts/login/", {"email": "cashier@shop.com", "password": "password123"}
    )

    entries = DjangoAuditRepository().list_entries(action="auth.login")
    assert len(entries) == 1
    assert entries[0].entity_id == str(cashier_user.id)
    assert entries[0].after["email"] == "cashier@shop.com"


@pytest.mark.django_db
def test_failed_login_is_recorded(api_client, cashier_user):
    api_client.post(
        "/api/v1/accounts/login/", {"email": "cashier@shop.com", "password": "wrong_password"}
    )

    entries = DjangoAuditRepository().list_entries(action="auth.login_failed")
    assert len(entries) == 1
    assert entries[0].user_id == cashier_user.id
    assert entries[0].after["email"] == "cashier@shop.com"


@pytest.mark.django_db
def test_logout_is_recorded(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    api_client.post("/api/v1/accounts/logout/")

    entries = DjangoAuditRepository().list_entries(action="auth.logout")
    assert len(entries) == 1
    assert entries[0].user_id == cashier_user.id


@pytest.mark.django_db
def test_admin_creating_a_user_is_recorded(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "Cashier",
            "role": "cashier",
            "password": "password123",
        },
    )

    entries = DjangoAuditRepository().list_entries(action="user.created")
    assert len(entries) == 1
    assert entries[0].entity_id == response.data["id"]
    assert entries[0].user_id == admin_user.id
    assert entries[0].after["role"] == "cashier"


@pytest.mark.django_db
def test_role_change_is_recorded(api_client, admin_user, cashier_user):
    api_client.force_authenticate(user=admin_user)

    api_client.patch(
        f"/api/v1/accounts/users/{cashier_user.id}/",
        {"role": "manager"},
        format="json",
    )

    role_entries = DjangoAuditRepository().list_entries(action="user.role_changed")
    assert len(role_entries) == 1
    assert role_entries[0].entity_id == str(cashier_user.id)
    assert role_entries[0].before == {"role": "cashier"}
    assert role_entries[0].after == {"role": "manager"}


@pytest.mark.django_db
def test_deactivating_a_user_is_recorded(api_client, admin_user, cashier_user):
    api_client.force_authenticate(user=admin_user)

    api_client.delete(f"/api/v1/accounts/users/{cashier_user.id}/")

    entries = DjangoAuditRepository().list_entries(action="user.deactivated")
    assert len(entries) == 1
    assert entries[0].entity_id == str(cashier_user.id)
    assert entries[0].after == {"is_active": False}
