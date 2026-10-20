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
def test_manager_can_rename_a_category(api_client, manager_user):
    category = CategoryModel.objects.create(name="Drinks")
    api_client.force_authenticate(user=manager_user)

    response = api_client.patch(
        f"/api/v1/catalog/categories/{category.id}/",
        {"name": "Beverages", "description": "Cold drinks"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["name"] == "Beverages"
    assert response.data["description"] == "Cold drinks"
    assert CategoryModel.objects.get(id=category.id).name == "Beverages"


@pytest.mark.django_db
def test_manager_can_reactivate_a_category(api_client, manager_user):
    category = CategoryModel.objects.create(name="Drinks", is_active=False)
    api_client.force_authenticate(user=manager_user)

    response = api_client.patch(
        f"/api/v1/catalog/categories/{category.id}/", {"is_active": True}, format="json"
    )

    assert response.status_code == 200
    assert response.data["is_active"] is True


@pytest.mark.django_db
def test_a_category_cannot_become_its_own_parent(api_client, manager_user):
    category = CategoryModel.objects.create(name="Drinks")
    api_client.force_authenticate(user=manager_user)

    response = api_client.patch(
        f"/api/v1/catalog/categories/{category.id}/",
        {"parent_id": str(category.id)},
        format="json",
    )

    assert response.status_code == 400
    assert "own parent" in response.data["detail"]


@pytest.mark.django_db
def test_manager_can_remove_a_parent_category(api_client, manager_user):
    parent = CategoryModel.objects.create(name="Food")
    child = CategoryModel.objects.create(name="Rice", parent_id=parent.id)
    api_client.force_authenticate(user=manager_user)

    response = api_client.patch(
        f"/api/v1/catalog/categories/{child.id}/", {"parent_id": None}, format="json"
    )

    assert response.status_code == 200
    assert response.data["parent_id"] is None
    assert CategoryModel.objects.get(id=child.id).parent_id is None


@pytest.mark.django_db
def test_cashier_cannot_update_a_category(api_client, cashier_user):
    category = CategoryModel.objects.create(name="Drinks")
    api_client.force_authenticate(user=cashier_user)

    response = api_client.patch(
        f"/api/v1/catalog/categories/{category.id}/", {"name": "Beverages"}, format="json"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_inactive_categories_can_be_listed(api_client, manager_user):
    CategoryModel.objects.create(name="Drinks", is_active=False)
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/catalog/categories/?active_only=false")

    assert response.status_code == 200
    assert [category["name"] for category in response.data] == ["Drinks"]
