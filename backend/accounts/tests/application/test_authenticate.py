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


def test_first_login_requires_a_password_change():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="new@shop.com", first_name="New", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    result = AuthenticateUserUseCase(repo, hasher).execute("new@shop.com", "password123")

    assert result.must_change_password is True
    assert result.last_login is not None


def test_seeded_superuser_is_not_forced_to_change_their_password():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(
        email="admin@shop.com",
        first_name="Seed",
        last_name="Admin",
        role=Role.ADMIN,
        is_superuser=True,
    )
    user.set_password("password123", hasher)
    repo.save(user)

    result = AuthenticateUserUseCase(repo, hasher).execute("admin@shop.com", "password123")

    assert result.must_change_password is False


def test_second_login_does_not_reopen_the_first_login_rule():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="return@shop.com", first_name="Return", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    user.last_login = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    repo.save(user)

    result = AuthenticateUserUseCase(repo, hasher).execute("return@shop.com", "password123")

    assert result.must_change_password is False


def test_failed_login_does_not_open_the_first_login_rule():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="typo@shop.com", first_name="Typo", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    with pytest.raises(InvalidCredentialsError):
        AuthenticateUserUseCase(repo, hasher).execute("typo@shop.com", "wrong_password")

    assert user.must_change_password is False
    assert user.last_login is None


def test_inactive_first_login_is_not_forced_to_change_a_password():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="gone@shop.com", first_name="Gone", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    user.is_active = False
    repo.save(user)

    with pytest.raises(InvalidCredentialsError):
        AuthenticateUserUseCase(repo, hasher).execute("gone@shop.com", "password123")

    assert user.must_change_password is False
    assert user.last_login is None


def test_locked_first_login_is_not_forced_to_change_a_password():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    user = User(email="held@shop.com", first_name="Held", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
    repo.save(user)

    with pytest.raises(InvalidCredentialsError):
        AuthenticateUserUseCase(repo, hasher).execute("held@shop.com", "password123")

    assert user.must_change_password is False
    assert user.last_login is None


class RecordingAudit:
    def __init__(self):
        self.entries = []

    def record(self, **entry):
        self.entries.append(entry)


def test_first_login_is_recorded_in_the_audit_trail():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    audit = RecordingAudit()
    user = User(email="audit@shop.com", first_name="Audit", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    AuthenticateUserUseCase(repo, hasher, audit).execute("audit@shop.com", "password123")

    actions = [entry["action"] for entry in audit.entries]
    assert "auth.first_login" in actions
    assert "auth.login" in actions


def test_first_login_audit_entry_names_the_user_and_the_flag():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    audit = RecordingAudit()
    user = User(email="flagged@shop.com", first_name="Flag", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    repo.save(user)

    AuthenticateUserUseCase(repo, hasher, audit).execute("flagged@shop.com", "password123")

    entry = next(e for e in audit.entries if e["action"] == "auth.first_login")
    assert entry["user_id"] == user.id
    assert entry["after"] == {"email": "flagged@shop.com", "password_change_required": True}


def test_returning_user_does_not_get_a_first_login_entry():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    audit = RecordingAudit()
    user = User(email="steady@shop.com", first_name="Steady", last_name="User", role=Role.CASHIER)
    user.set_password("password123", hasher)
    user.last_login = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    repo.save(user)

    AuthenticateUserUseCase(repo, hasher, audit).execute("steady@shop.com", "password123")

    actions = [entry["action"] for entry in audit.entries]
    assert "auth.first_login" not in actions
    assert "auth.login" in actions
