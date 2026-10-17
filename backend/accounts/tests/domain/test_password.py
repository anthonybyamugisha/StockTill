import pytest

from accounts.domain.entities import Role, User


def test_password_is_hashed_not_stored_raw():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.set_password("secure_password_123")
    assert user.password_hash != "secure_password_123"
    assert len(user.password_hash) > 0


def test_verify_correct_password():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.set_password("my_password")
    assert user.check_password("my_password") is True


def test_verify_incorrect_password():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.set_password("my_password")
    assert user.check_password("wrong_password") is False
