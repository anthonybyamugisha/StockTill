from accounts.application.commands import DeactivateUserCommand, UpdateUserCommand
from accounts.application.use_cases import DeactivateUserUseCase, UpdateUserUseCase
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


def test_update_user_changes_name():
    repo = FakeUserRepository()
    user = User(email="user@shop.com", first_name="Old", last_name="Name", role=Role.CASHIER)
    repo.save(user)

    use_case = UpdateUserUseCase(repo)
    updated = use_case.execute(UpdateUserCommand(user_id=user.id, first_name="New"))

    assert updated.first_name == "New"


def test_update_user_changes_role():
    repo = FakeUserRepository()
    user = User(email="user@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    repo.save(user)

    use_case = UpdateUserUseCase(repo)
    updated = use_case.execute(UpdateUserCommand(user_id=user.id, role=Role.MANAGER))

    assert updated.role == Role.MANAGER


def test_deactivate_user():
    repo = FakeUserRepository()
    user = User(email="user@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    repo.save(user)

    use_case = DeactivateUserUseCase(repo)
    deactivated = use_case.execute(DeactivateUserCommand(user_id=user.id))

    assert deactivated.is_active is False
