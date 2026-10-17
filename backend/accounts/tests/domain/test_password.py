import pytest

from accounts.domain.entities import Role, User
from accounts.domain.password import PasswordHasher


class FakePasswordHasher(PasswordHasher):
    def hash(self, raw_password: str) -> str:
        return f"hashed_{raw_password}"

    def verify(self, raw_password: str, hashed: str) -> bool:
        return hashed == f"hashed_{raw_password}"


def test_password_is_hashed_not_stored_raw():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    hasher = FakePasswordHasher()
    user.set_password("secure_password_123", hasher)
    assert user.password_hash != "secure_password_123"
    assert user.password_hash == "hashed_secure_password_123"


def test_verify_correct_password():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    hasher = FakePasswordHasher()
    user.set_password("my_password", hasher)
    assert user.check_password("my_password", hasher) is True


def test_verify_incorrect_password():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    hasher = FakePasswordHasher()
    user.set_password("my_password", hasher)
    assert user.check_password("wrong_password", hasher) is False
