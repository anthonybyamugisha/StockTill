from datetime import UTC, datetime, timedelta

from accounts.domain.entities import Role, User


def test_account_locks_after_max_failed_attempts():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.register_failed_login(max_attempts=5)
    assert user.is_locked() is False
    for _ in range(4):
        user.register_failed_login(max_attempts=5)
    assert user.is_locked() is True


def test_account_unlocks_after_lock_duration():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.register_failed_login(max_attempts=5)
    for _ in range(4):
        user.register_failed_login(max_attempts=5)
    assert user.is_locked() is True
    user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    assert user.is_locked() is False


def test_successful_login_resets_failed_attempts():
    user = User(email="test@shop.com", first_name="Test", last_name="User", role=Role.CASHIER)
    user.failed_login_attempts = 3
    user.register_successful_login()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
