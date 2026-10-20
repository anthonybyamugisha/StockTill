import pytest

from accounts.domain.entities import Role, User
from accounts.domain.errors import WeakPasswordError
from accounts.domain.password import PasswordHasher, validate_password_strength


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


def test_changing_a_password_clears_the_first_login_flag():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    hasher = FakePasswordHasher()
    user.set_password("temporary1", hasher)
    user.require_password_change()
    user.change_password("permanent1", hasher)
    assert user.must_change_password is False
    assert user.check_password("permanent1", hasher) is True
    assert user.check_password("temporary1", hasher) is False


def test_password_strength_rejects_short_passwords():
    with pytest.raises(WeakPasswordError, match="at least 8"):
        validate_password_strength("abc123")


def test_password_strength_rejects_letters_only():
    with pytest.raises(WeakPasswordError, match="letter and one number"):
        validate_password_strength("onlyletters")


def test_password_strength_rejects_numbers_only():
    with pytest.raises(WeakPasswordError, match="letter and one number"):
        validate_password_strength("12345678")


def test_password_strength_accepts_a_mixed_password():
    validate_password_strength("GoodPass123")


def test_password_strength_accepts_exactly_eight_characters():
    validate_password_strength("abcdefg1")
