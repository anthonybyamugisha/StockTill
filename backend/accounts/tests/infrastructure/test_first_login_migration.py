import importlib

import pytest
from django.apps import apps
from django.utils import timezone

from accounts.infrastructure.models import UserModel

migration = importlib.import_module("accounts.migrations.0003_backfill_first_login_passwords")


def build_model_user(email: str, **overrides) -> UserModel:
    fields = {
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "role": "cashier",
        "is_active": True,
        "must_change_password": False,
    }
    fields.update(overrides)
    return UserModel.objects.create(**fields)


@pytest.mark.django_db
def test_migration_flags_legacy_accounts():
    legacy = build_model_user("legacy@shop.com")

    migration.mark_legacy_first_logins(apps, None)

    legacy.refresh_from_db()
    assert legacy.must_change_password is True


@pytest.mark.django_db
def test_migration_leaves_returning_accounts_alone():
    returning = build_model_user("returning@shop.com", last_login=timezone.now())

    migration.mark_legacy_first_logins(apps, None)

    returning.refresh_from_db()
    assert returning.must_change_password is False


@pytest.mark.django_db
def test_migration_leaves_superusers_alone():
    superuser = build_model_user("owner@shop.com", is_superuser=True)

    migration.mark_legacy_first_logins(apps, None)

    superuser.refresh_from_db()
    assert superuser.must_change_password is False


@pytest.mark.django_db
def test_migration_keeps_an_existing_pending_flag():
    pending = build_model_user("pending@shop.com", must_change_password=True)

    migration.mark_legacy_first_logins(apps, None)

    pending.refresh_from_db()
    assert pending.must_change_password is True
