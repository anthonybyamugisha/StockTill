import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User(email="admin@shop.com", first_name="Admin", last_name="User", role=Role.ADMIN)
    user.set_password("admin_pass123", DjangoPasswordHasher())
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
def manager_user(db):
    user = User(email="manager@shop.com", first_name="Manager", last_name="User", role=Role.MANAGER)
    user.set_password("manager_pass123", DjangoPasswordHasher())
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
def cashier_user(db):
    user = User(email="cashier@shop.com", first_name="Cashier", last_name="User", role=Role.CASHIER)
    user.set_password("cashier_pass123", DjangoPasswordHasher())
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
def test_admin_can_list_users(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/accounts/users/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_manager_cannot_list_users(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/accounts/users/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_cashier_cannot_list_users(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/accounts/users/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_user(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "User",
            "role": "cashier",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    assert response.data["email"] == "new@shop.com"


@pytest.mark.django_db
def test_manager_cannot_create_user(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "User",
            "role": "cashier",
            "password": "password123",
        },
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_cashier_cannot_create_user(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "User",
            "role": "cashier",
            "password": "password123",
        },
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_manager_can_list_cashiers(api_client, manager_user, cashier_user):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/accounts/cashiers/")

    assert response.status_code == 200
    assert response.data == [
        {"id": str(cashier_user.id), "first_name": "Cashier", "last_name": "User"}
    ]


@pytest.mark.django_db
def test_cashier_cannot_list_cashiers(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.get("/api/v1/accounts/cashiers/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_cannot_access_users(api_client):
    response = api_client.get("/api/v1/accounts/users/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_deactivate_user(api_client, admin_user, cashier_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.delete(f"/api/v1/accounts/users/{cashier_user.id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_manager_cannot_deactivate_user(api_client, manager_user, cashier_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.delete(f"/api/v1/accounts/users/{cashier_user.id}/")
    assert response.status_code == 403
