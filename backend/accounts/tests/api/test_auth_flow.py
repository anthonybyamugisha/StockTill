import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cashier_user(db):
    user = User(email="cashier@shop.com", first_name="Cashier", last_name="User", role=Role.CASHIER)
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


@pytest.mark.django_db
def test_login_with_valid_credentials(api_client, cashier_user):
    response = api_client.post(
        "/api/v1/accounts/login/",
        {"email": "cashier@shop.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.data["email"] == "cashier@shop.com"


@pytest.mark.django_db
def test_login_with_invalid_password(api_client, cashier_user):
    response = api_client.post(
        "/api/v1/accounts/login/",
        {"email": "cashier@shop.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_with_nonexistent_user(api_client):
    response = api_client.post(
        "/api/v1/accounts/login/",
        {"email": "nobody@shop.com", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_logout(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.post("/api/v1/accounts/logout/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_current_user_returns_authenticated_user(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/accounts/me/")
    assert response.status_code == 200
    assert response.data["email"] == "cashier@shop.com"


@pytest.mark.django_db
def test_current_user_rejects_unauthenticated(api_client):
    response = api_client.get("/api/v1/accounts/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_increments_failed_attempts_on_wrong_password(api_client, cashier_user):
    api_client.post(
        "/api/v1/accounts/login/",
        {"email": "cashier@shop.com", "password": "wrong"},
    )
    user_model = UserModel.objects.get(id=cashier_user.id)
    assert user_model.failed_login_attempts == 1


@pytest.mark.django_db
def test_account_locks_after_5_failed_attempts(api_client, cashier_user):
    for _ in range(5):
        api_client.post(
            "/api/v1/accounts/login/",
            {"email": "cashier@shop.com", "password": "wrong"},
        )
    response = api_client.post(
        "/api/v1/accounts/login/",
        {"email": "cashier@shop.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert "locked" in response.data["detail"].lower()
