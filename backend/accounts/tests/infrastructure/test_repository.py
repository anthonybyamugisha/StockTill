from datetime import UTC
from uuid import uuid4

import pytest

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.repository import DjangoUserRepository


@pytest.mark.django_db
def test_save_and_get_by_id():
    repo = DjangoUserRepository()
    user = User(
        email="test@shop.com",
        first_name="Test",
        last_name="User",
        role=Role.CASHIER,
        password_hash="hashed_password",
    )
    repo.save(user)

    fetched = repo.get_by_id(user.id)
    assert fetched is not None
    assert fetched.email == "test@shop.com"
    assert fetched.role == Role.CASHIER


@pytest.mark.django_db
def test_get_by_email_case_insensitive():
    repo = DjangoUserRepository()
    user = User(
        email="Test@Shop.com",
        first_name="Test",
        last_name="User",
        role=Role.MANAGER,
        password_hash="hashed",
    )
    repo.save(user)

    fetched = repo.get_by_email("test@shop.com")
    assert fetched is not None
    assert fetched.email == "Test@Shop.com"


@pytest.mark.django_db
def test_get_by_id_returns_none_for_missing():
    repo = DjangoUserRepository()
    assert repo.get_by_id(uuid4()) is None


@pytest.mark.django_db
def test_get_by_email_returns_none_for_missing():
    repo = DjangoUserRepository()
    assert repo.get_by_email("nobody@shop.com") is None


@pytest.mark.django_db
def test_list_users_returns_all():
    repo = DjangoUserRepository()
    repo.save(
        User(
            email="a@shop.com", first_name="A", last_name="B", role=Role.CASHIER, password_hash="x"
        )
    )
    repo.save(
        User(email="b@shop.com", first_name="C", last_name="D", role=Role.ADMIN, password_hash="y")
    )

    users = repo.list_users()
    assert len(users) == 2


@pytest.mark.django_db
def test_list_users_active_only():
    repo = DjangoUserRepository()
    active = User(
        email="active@shop.com", first_name="A", last_name="B", role=Role.CASHIER, password_hash="x"
    )
    inactive = User(
        email="inactive@shop.com",
        first_name="C",
        last_name="D",
        role=Role.CASHIER,
        password_hash="y",
    )
    inactive.is_active = False
    repo.save(active)
    repo.save(inactive)

    users = repo.list_users(active_only=True)
    assert len(users) == 1
    assert users[0].email == "active@shop.com"


@pytest.mark.django_db
def test_email_exists():
    repo = DjangoUserRepository()
    repo.save(
        User(
            email="exists@shop.com",
            first_name="A",
            last_name="B",
            role=Role.CASHIER,
            password_hash="x",
        )
    )

    assert repo.email_exists("exists@shop.com") is True
    assert repo.email_exists("missing@shop.com") is False


@pytest.mark.django_db
def test_save_updates_existing_user():
    repo = DjangoUserRepository()
    user = User(
        email="update@shop.com",
        first_name="Old",
        last_name="Name",
        role=Role.CASHIER,
        password_hash="x",
    )
    repo.save(user)

    user.first_name = "New"
    repo.save(user)

    fetched = repo.get_by_id(user.id)
    assert fetched.first_name == "New"


@pytest.mark.django_db
def test_persists_lockout_fields():
    from datetime import datetime, timedelta

    repo = DjangoUserRepository()
    user = User(
        email="lock@shop.com",
        first_name="Lock",
        last_name="User",
        role=Role.CASHIER,
        password_hash="x",
    )
    user.failed_login_attempts = 3
    user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
    repo.save(user)

    fetched = repo.get_by_id(user.id)
    assert fetched.failed_login_attempts == 3
    assert fetched.locked_until is not None


@pytest.mark.django_db
def test_persists_first_login_flag():
    repo = DjangoUserRepository()
    user = User(
        email="pending@shop.com",
        first_name="Pending",
        last_name="User",
        role=Role.CASHIER,
        password_hash="x",
    )
    user.require_password_change()
    repo.save(user)

    fetched = repo.get_by_id(user.id)
    assert fetched.must_change_password is True


@pytest.mark.django_db
def test_existing_accounts_do_not_need_a_password_change():
    repo = DjangoUserRepository()
    repo.save(
        User(
            email="legacy@shop.com",
            first_name="Legacy",
            last_name="User",
            role=Role.CASHIER,
            password_hash="x",
        )
    )

    fetched = repo.get_by_id(repo.get_by_email("legacy@shop.com").id)
    assert fetched.must_change_password is False


@pytest.mark.django_db
def test_reads_the_superuser_flag_without_writing_through():
    repo = DjangoUserRepository()
    user = User(
        email="seed@shop.com",
        first_name="Seed",
        last_name="Admin",
        role=Role.ADMIN,
        password_hash="x",
    )
    repo.save(user)
    UserModel.objects.filter(id=user.id).update(is_superuser=True)

    fetched = repo.get_by_id(user.id)
    assert fetched is not None
    assert fetched.is_superuser is True

    fetched.first_name = "Renamed"
    repo.save(fetched)
    assert UserModel.objects.get(id=user.id).is_superuser is True
