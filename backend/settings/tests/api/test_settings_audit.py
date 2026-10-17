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


def _settings_payload(**overrides):
    payload = {
        "business_name": "StockTill Shop",
        "address": "Kampala",
        "phone": "+256700000000",
        "email": "shop@stocktill.com",
        "currency": "UGX",
        "receipt_header": "Thank you",
        "receipt_footer": "Come again",
        "cashier_discount_limit": "5.00",
        "tax_rate": "0.00",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_updating_settings_records_a_diff(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.put(
        "/api/v1/settings/",
        _settings_payload(business_name="StockTill Supermarket"),
        format="json",
    )
    assert response.status_code == 200, response.data

    entries = DjangoAuditRepository().list_entries(action="settings.updated")
    assert len(entries) == 1
    assert entries[0].entity_type == "settings"
    assert entries[0].user_id == admin_user.id
    assert entries[0].after["business_name"] == "StockTill Supermarket"


@pytest.mark.django_db
def test_unchanged_settings_write_no_entry(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    payload = _settings_payload()

    api_client.put("/api/v1/settings/", payload, format="json")
    api_client.put("/api/v1/settings/", payload, format="json")

    entries = DjangoAuditRepository().list_entries(action="settings.updated")
    assert len(entries) == 1
