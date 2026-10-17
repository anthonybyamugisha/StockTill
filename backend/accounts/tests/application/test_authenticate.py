from datetime import UTC, datetime, timedelta

import pytest

from accounts.application.use_cases import AuthenticateUserUseCase
from accounts.domain.entities import Role, User
from accounts.domain.errors import InvalidCredentialsError
from accounts.domain.password import PasswordHasher
from accounts.domain.repository import UserRepository


class FakePasswordHasher(PasswordHasher):
    def hash(self, raw_password: str) -> str:
        return f"hashed_{raw_password}"

    def verify(self, raw_password: str, hashed: str) -> bool:
        return hashed == f"hashed_{raw_password}"


class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users = []

    def get_by_id(self, user_id):
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    def get_by_email(self, email):
        for u in self.users:
            if u.email == email:
                return u
        return None

    def list_users(self, active_only=False):
        return [u for u in self.users if not active_only or u.is_active]

    def save(self, user):
        self.users.append(user)

    def email_exists(self, email):
        return any(u.email == email for u in self.users)


def test_authenticate_with_valid_credentials():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="user@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    use_case = AuthenticateUserUseCase(repo, hasher)
    result = use_case.execute("user@shop.com", "password123")

    assert result == user
    assert user.failed_login_attempts == 0
    assert user.last_login is not None


def test_authenticate_with_invalid_password():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="user@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    use_case = AuthenticateUserUseCase(repo, hasher)

    with pytest.raises(InvalidCredentialsError):
        use_case.execute("user@shop.com", "wrong_password")

    assert user.failed_login_attempts == 1


def test_authenticate_with_nonexistent_email():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = AuthenticateUserUseCase(repo, hasher)

    with pytest.raises(InvalidCredentialsError):
        use_case.execute("nobody@shop.com", "password123")


def test_authenticate_with_inactive_user():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(
        email="inactive@shop.com", first_name="Inactive", last_name="User", role=Role.CASHIER
    )
    user.set_password("password123", hasher)
    user.is_active = False
    repo.save(user)

    use_case = AuthenticateUserUseCase(repo, hasher)

    with pytest.raises(InvalidCredentialsError, match="Account deactivated"):
        use_case.execute("inactive@shop.com", "password123")


def test_authenticate_with_locked_account():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="locked@shop.com", first_name="Locked", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
    repo.save(user)

    use_case = AuthenticateUserUseCase(repo, hasher)

    with pytest.raises(InvalidCredentialsError, match="Account locked"):
        use_case.execute("locked@shop.com", "password123")
