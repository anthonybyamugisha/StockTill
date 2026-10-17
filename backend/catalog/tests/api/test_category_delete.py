import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import CategoryModel


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


@pytest.mark.django_db
def test_manager_can_deactivate_category(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    created = api_client.post("/api/v1/catalog/categories/", {"name": "DiagCat"})
    assert created.status_code == 201
    category_id = created.data["id"]

    response = api_client.delete(f"/api/v1/catalog/categories/{category_id}/")

    assert response.status_code == 204
    assert CategoryModel.objects.get(id=category_id).is_active is False

    listing = api_client.get("/api/v1/catalog/categories/")
    assert all(category["id"] != category_id for category in listing.data)


@pytest.mark.django_db
def test_cashier_cannot_deactivate_category(api_client, cashier_user):
    category = CategoryModel.objects.create(name="DiagCat")

    api_client.force_authenticate(user=cashier_user)
    response = api_client.delete(f"/api/v1/catalog/categories/{category.id}/")

    assert response.status_code == 403
    assert CategoryModel.objects.get(id=category.id).is_active is True


@pytest.mark.django_db
def test_deactivating_unknown_category_is_rejected(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    response = api_client.delete("/api/v1/catalog/categories/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 400
