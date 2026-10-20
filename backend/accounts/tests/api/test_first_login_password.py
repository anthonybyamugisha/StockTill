import importlib

import pytest
from django.apps import apps
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher

TEMPORARY_PASSWORD = "temporary1"
PERMANENT_PASSWORD = "permanent12"


def build_user(email: str, role: Role = Role.CASHIER, pending: bool = False) -> UserModel:
    user = User(email=email, first_name="Test", last_name="User", role=role)
    user.set_password(TEMPORARY_PASSWORD, DjangoPasswordHasher())
    if pending:
        user.require_password_change()
    return UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
        must_change_password=user.must_change_password,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return build_user("admin@shop.com", Role.ADMIN)


@pytest.fixture
def pending_user(db):
    return build_user("pending@shop.com", Role.CASHIER, pending=True)


def sign_in(client: APIClient, email: str, password: str = TEMPORARY_PASSWORD):
    return client.post("/api/v1/accounts/login/", {"email": email, "password": password})


@pytest.mark.django_db
def test_created_user_starts_with_a_pending_password(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "User",
            "role": "cashier",
            "password": "welcome123",
        },
    )

    assert response.status_code == 201
    assert response.data["must_change_password"] is True
    assert UserModel.objects.get(email="new@shop.com").must_change_password is True


@pytest.mark.django_db
def test_login_reports_the_pending_flag(api_client, pending_user):
    response = sign_in(api_client, pending_user.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/catalog/products/",
        "/api/v1/inventory/items/",
        "/api/v1/sales/",
        "/api/v1/shifts/current/",
        "/api/v1/reporting/dashboard/",
        "/api/v1/reporting/sales-summary/csv/",
        "/api/v1/accounts/users/",
        "/api/v1/accounts/audit-log/",
        "/api/v1/settings/",
    ],
)
def test_pending_user_is_blocked_from_business_endpoints(api_client, pending_user, path):
    sign_in(api_client, pending_user.email)

    response = api_client.get(path)

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_pending_user_can_read_their_profile(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/v1/accounts/me/")

    assert response.status_code == 200
    assert response.data["email"] == pending_user.email
    assert response.data["must_change_password"] is True


@pytest.mark.django_db
def test_pending_user_is_blocked_from_a_lookalike_path(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/v1/accounts/me/extra/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_pending_user_can_change_the_password(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    assert response.status_code == 200
    assert response.data["must_change_password"] is False
    pending_user.refresh_from_db()
    assert DjangoPasswordHasher().verify(PERMANENT_PASSWORD, pending_user.password)


@pytest.mark.django_db
def test_old_password_stops_working_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    fresh_client = APIClient()
    response = sign_in(fresh_client, pending_user.email, TEMPORARY_PASSWORD)

    assert response.status_code == 401


@pytest.mark.django_db
def test_new_password_works_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    fresh_client = APIClient()
    response = sign_in(fresh_client, pending_user.email, PERMANENT_PASSWORD)

    assert response.status_code == 200
    assert response.data["must_change_password"] is False


@pytest.mark.django_db
def test_business_endpoints_reopen_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    response = api_client.get("/api/v1/catalog/products/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_weak_password_is_rejected_over_the_api(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": "onlyletters"},
    )

    assert response.status_code == 400
    assert "letter and one number" in response.data["detail"]


@pytest.mark.django_db
def test_short_password_is_rejected_over_the_api(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": "short1"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_reusing_the_temporary_password_is_rejected(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": TEMPORARY_PASSWORD},
    )

    assert response.status_code == 400
    assert "must be different" in response.data["detail"]


@pytest.mark.django_db
def test_wrong_current_password_is_rejected(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": "not-the-password", "new_password": PERMANENT_PASSWORD},
    )

    assert response.status_code == 400
    assert "Current password is incorrect" in response.data["detail"]


@pytest.mark.django_db
def test_password_change_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_pending_user_can_log_out(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post("/api/v1/accounts/logout/")

    assert response.status_code == 204


@pytest.mark.django_db
def test_pending_admin_cannot_reach_user_management(api_client):
    pending_admin = build_user("pending-admin@shop.com", Role.ADMIN, pending=True)
    sign_in(api_client, pending_admin.email)

    response = api_client.get("/api/v1/accounts/users/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_weak_temporary_password_is_rejected(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "weak@shop.com",
            "first_name": "Weak",
            "last_name": "User",
            "role": "cashier",
            "password": "onlyletters",
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_pending_user_can_reach_the_health_check(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/v1/health/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_settled_user_logs_in_without_the_pending_flag(api_client, admin_user):
    admin_user.last_login = timezone.now()
    admin_user.save(update_fields=["last_login"])

    response = sign_in(api_client, admin_user.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is False


@pytest.mark.django_db
def test_password_change_appears_in_the_audit_log(api_client, admin_user, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    admin_client = APIClient()
    admin_user.last_login = timezone.now()
    admin_user.save(update_fields=["last_login"])
    sign_in(admin_client, admin_user.email)
    response = admin_client.get("/api/v1/accounts/audit-log/", {"action": "auth.password_changed"})

    assert response.status_code == 200
    assert any(entry["user_email"] == pending_user.email for entry in response.data)


@pytest.mark.django_db
def test_legacy_first_login_appears_in_the_audit_log(api_client, admin_user):
    legacy = build_user("legacy-audit@shop.com")
    sign_in(api_client, legacy.email)

    admin_client = APIClient()
    admin_user.last_login = timezone.now()
    admin_user.save(update_fields=["last_login"])
    sign_in(admin_client, admin_user.email)
    response = admin_client.get("/api/v1/accounts/audit-log/", {"action": "auth.first_login"})

    assert response.status_code == 200
    assert any(entry["user_email"] == legacy.email for entry in response.data)


@pytest.mark.django_db
def test_password_change_requires_both_fields(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD},
    )

    assert response.status_code == 400
    assert "new_password" in response.data


@pytest.mark.django_db
def test_short_temporary_password_is_rejected(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "short@shop.com",
            "first_name": "Short",
            "last_name": "User",
            "role": "cashier",
            "password": "short1",
        },
    )

    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_pending_user_can_open_the_api_docs(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/docs/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_legacy_account_is_flagged_on_its_first_login(api_client):
    legacy = build_user("legacy@shop.com")

    response = sign_in(api_client, legacy.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is True
    legacy.refresh_from_db()
    assert legacy.must_change_password is True


@pytest.mark.django_db
def test_legacy_account_cannot_reach_the_dashboard_before_changing(api_client):
    legacy = build_user("legacy-dash@shop.com")
    sign_in(api_client, legacy.email)

    response = api_client.get("/api/v1/reporting/dashboard/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_legacy_account_reaches_the_dashboard_after_changing(api_client):
    legacy = build_user("legacy-change@shop.com")
    sign_in(api_client, legacy.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    response = api_client.get("/api/v1/reporting/dashboard/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_seeded_superuser_logs_in_without_a_change(api_client):
    user = User(email="seed@shop.com", first_name="Seed", last_name="Admin", role=Role.ADMIN)
    user.set_password(TEMPORARY_PASSWORD, DjangoPasswordHasher())
    UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
        is_superuser=True,
    )

    response = sign_in(api_client, "seed@shop.com")

    assert response.status_code == 200
    assert response.data["must_change_password"] is False


@pytest.mark.django_db
def test_returning_user_is_not_flagged_again(api_client):
    user = build_user("returning@shop.com")
    UserModel.objects.filter(id=user.id).update(last_login=timezone.now())

    response = sign_in(api_client, user.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is False


@pytest.mark.django_db
def test_migrated_legacy_account_is_forced_over_http(api_client):
    legacy = build_user("legacy-migrated@shop.com")
    migration = importlib.import_module("accounts.migrations.0003_backfill_first_login_passwords")
    migration.mark_legacy_first_logins(apps, None)

    response = sign_in(api_client, legacy.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is True

    response = api_client.get("/api/v1/reporting/dashboard/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_migration_leaves_a_returning_account_unforced_over_http(api_client):
    user = build_user("legacy-returned@shop.com")
    UserModel.objects.filter(id=user.id).update(last_login=timezone.now())
    migration = importlib.import_module("accounts.migrations.0003_backfill_first_login_passwords")
    migration.mark_legacy_first_logins(apps, None)

    response = sign_in(api_client, user.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is False
