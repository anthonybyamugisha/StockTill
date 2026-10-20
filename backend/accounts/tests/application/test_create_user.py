import pytest

from accounts.application.commands import CreateUserCommand
from accounts.application.use_cases import CreateUserUseCase
from accounts.domain.entities import Role, User
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


def test_create_user_succeeds():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = CreateUserUseCase(repo, hasher)

    user = use_case.execute(
        CreateUserCommand(
            email="new@shop.com",
            first_name="New",
            last_name="User",
            role=Role.CASHIER,
            password="secure123",
        )
    )

    assert user.email == "new@shop.com"
    assert user.password_hash == "hashed_secure123"
    assert repo.get_by_email("new@shop.com") == user


def test_create_user_raises_on_duplicate_email():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    repo.save(
        User(email="exists@shop.com", first_name="Exists", last_name="User", role=Role.CASHIER)
    )
    use_case = CreateUserUseCase(repo, hasher)

    with pytest.raises(ValueError, match="Email already registered"):
        use_case.execute(
            CreateUserCommand(
                email="exists@shop.com",
                first_name="New",
                last_name="User",
                role=Role.CASHIER,
                password="secure123",
            )
        )


def test_created_user_must_change_the_initial_password():
    repo = FakeUserRepository()
    use_case = CreateUserUseCase(repo, FakePasswordHasher())

    user = use_case.execute(
        CreateUserCommand(
            email="temp@shop.com",
            first_name="Temp",
            last_name="User",
            role=Role.CASHIER,
            password="temporary1",
        )
    )

    assert user.must_change_password is True
