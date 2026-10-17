from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from shared.infrastructure.audit import AuditEntry


@pytest.fixture
def api_client():
    return APIClient()


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
def admin_user(db):
    return _make_user("admin@shop.com", Role.ADMIN)


@pytest.fixture
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.mark.django_db
def test_admin_can_read_audit_log(api_client, admin_user, cashier_user):
    DjangoAuditRepository().save(
        AuditEntry(
            id=uuid4(),
            user_id=cashier_user.id,
            action="sale.voided",
            entity_type="sale",
            entity_id="ST-2026-000001",
            before={"status": "completed"},
            after={"status": "voided"},
        )
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/accounts/audit-log/")

    assert response.status_code == 200
    assert len(response.data) == 1
    entry = response.data[0]
    assert entry["action"] == "sale.voided"
    assert entry["user_id"] == str(cashier_user.id)
    assert entry["user_name"] == "cashier User"
    assert entry["user_email"] == "cashier@shop.com"
    assert entry["entity_type"] == "sale"
    assert entry["before"] == {"status": "completed"}
    assert entry["timestamp"] is not None


@pytest.mark.django_db
def test_audit_log_filters_by_action(api_client, admin_user):
    repo = DjangoAuditRepository()
    repo.save(
        AuditEntry(
            id=uuid4(),
            user_id=None,
            action="product.created",
            entity_type="product",
            entity_id=str(uuid4()),
        )
    )
    repo.save(
        AuditEntry(
            id=uuid4(),
            user_id=None,
            action="sale.voided",
            entity_type="sale",
            entity_id="ST-2026-000002",
        )
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/accounts/audit-log/", {"action": "sale.voided"})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["action"] == "sale.voided"


@pytest.mark.django_db
def test_cashier_cannot_read_audit_log(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/accounts/audit-log/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_audit_log_requires_authentication(api_client):
    response = api_client.get("/api/v1/accounts/audit-log/")
    assert response.status_code == 403
