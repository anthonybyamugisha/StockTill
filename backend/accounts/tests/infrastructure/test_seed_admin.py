import pytest
from django.core.management import call_command

from accounts.infrastructure.models import UserModel

SUPERUSER_EMAIL = "root@stocktill.com"
SUPERUSER_PASSWORD = "Anthony@2026.#"


@pytest.mark.django_db
def test_seed_creates_an_unforced_superuser(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", SUPERUSER_EMAIL)
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", SUPERUSER_PASSWORD)

    call_command("seed_admin")

    user = UserModel.objects.get(email=SUPERUSER_EMAIL)
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.role == "admin"
    assert user.must_change_password is False


@pytest.mark.django_db
def test_seed_clears_a_pending_flag_on_the_superuser(monkeypatch):
    UserModel.objects.create(
        email=SUPERUSER_EMAIL,
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True,
        is_superuser=True,
        must_change_password=True,
    )
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", SUPERUSER_EMAIL)
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", SUPERUSER_PASSWORD)

    call_command("seed_admin")

    user = UserModel.objects.get(email=SUPERUSER_EMAIL)
    assert user.must_change_password is False


@pytest.mark.django_db
def test_seed_without_a_password_creates_nothing(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", SUPERUSER_EMAIL)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

    call_command("seed_admin")

    assert UserModel.objects.filter(email=SUPERUSER_EMAIL).exists() is False
