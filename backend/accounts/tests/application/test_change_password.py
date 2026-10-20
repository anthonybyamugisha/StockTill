import pytest

from accounts.application.commands import ChangePasswordCommand
from accounts.application.use_cases import ChangePasswordUseCase
from accounts.domain.entities import Role, User
from accounts.domain.errors import InvalidCurrentPasswordError, WeakPasswordError
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
        self.saves = 0

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
        self.saves += 1
        if user not in self.users:
            self.users.append(user)

    def email_exists(self, email):
        return any(u.email == email for u in self.users)


class FakeAudit:
    def __init__(self):
        self.entries = []

    def record(self, **kwargs):
        self.entries.append(kwargs)


def make_user(hasher: PasswordHasher, password: str = "temporary1") -> User:
    user = User(
        email="cashier@shop.com",
        first_name="Cashier",
        last_name="User",
        role=Role.CASHIER,
    )
    user.set_password(password, hasher)
    user.require_password_change()
    return user


def test_change_password_updates_the_password_and_clears_the_flag():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    user = make_user(hasher)
    repo.save(user)

    result = ChangePasswordUseCase(repo, hasher).execute(
        ChangePasswordCommand(
            user_id=user.id,
            current_password="temporary1",
            new_password="permanent1",
        )
    )

    assert result is user
    assert user.must_change_password is False
    assert user.check_password("permanent1", hasher) is True
    assert repo.saves == 2


def test_change_password_rejects_a_wrong_current_password():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    user = make_user(hasher)
    repo.save(user)

    with pytest.raises(InvalidCurrentPasswordError, match="Current password is incorrect"):
        ChangePasswordUseCase(repo, hasher).execute(
            ChangePasswordCommand(
                user_id=user.id,
                current_password="wrong",
                new_password="permanent1",
            )
        )

    assert user.must_change_password is True
    assert repo.saves == 1


def test_change_password_rejects_a_short_new_password():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    user = make_user(hasher)
    repo.save(user)

    with pytest.raises(WeakPasswordError, match="at least 8"):
        ChangePasswordUseCase(repo, hasher).execute(
            ChangePasswordCommand(
                user_id=user.id, current_password="temporary1", new_password="short1"
            )
        )


def test_change_password_rejects_a_new_password_without_a_number():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    user = make_user(hasher)
    repo.save(user)

    with pytest.raises(WeakPasswordError, match="letter and one number"):
        ChangePasswordUseCase(repo, hasher).execute(
            ChangePasswordCommand(
                user_id=user.id,
                current_password="temporary1",
                new_password="onlyletters",
            )
        )


def test_change_password_rejects_reuse_of_the_current_password():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    user = make_user(hasher, "temporary1")
    repo.save(user)

    with pytest.raises(WeakPasswordError, match="must be different"):
        ChangePasswordUseCase(repo, hasher).execute(
            ChangePasswordCommand(
                user_id=user.id,
                current_password="temporary1",
                new_password="temporary1",
            )
        )


def test_change_password_rejects_an_unknown_user():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    from uuid import uuid4

    with pytest.raises(ValueError, match="User not found"):
        ChangePasswordUseCase(repo, hasher).execute(
            ChangePasswordCommand(
                user_id=uuid4(),
                current_password="temporary1",
                new_password="permanent1",
            )
        )


def test_change_password_records_an_audit_entry():
    hasher = FakePasswordHasher()
    repo = FakeUserRepository()
    audit = FakeAudit()
    user = make_user(hasher)
    repo.save(user)

    ChangePasswordUseCase(repo, hasher, audit).execute(
        ChangePasswordCommand(
            user_id=user.id,
            current_password="temporary1",
            new_password="permanent1",
        )
    )

    assert len(audit.entries) == 1
    entry = audit.entries[0]
    assert entry["action"] == "auth.password_changed"
    assert entry["entity_id"] == str(user.id)
    assert entry["user_id"] == user.id
    assert entry["after"] == {"email": user.email}
