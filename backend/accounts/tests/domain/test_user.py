from accounts.domain.entities import Role, User


def test_create_user_with_valid_data():
    user = User(email="admin@shop.com", first_name="John", last_name="Doe", role=Role.ADMIN)
    assert user.email == "admin@shop.com"
    assert user.role == Role.ADMIN
    assert user.is_active is True


def test_user_equality_by_id():
    from uuid import uuid4

    uid = uuid4()
    user1 = User(id=uid, email="a@shop.com", first_name="A", last_name="B", role=Role.CASHIER)
    user2 = User(id=uid, email="b@shop.com", first_name="C", last_name="D", role=Role.MANAGER)
    assert user1 == user2


def test_deactivate_user():
    user = User(email="cashier@shop.com", first_name="Jane", last_name="Doe", role=Role.CASHIER)
    user.is_active = False
    assert user.is_active is False


def test_new_user_does_not_need_a_password_change():
    user = User(email="new@shop.com", first_name="New", last_name="User", role=Role.CASHIER)
    assert user.must_change_password is False


def test_requiring_a_password_change_sets_the_flag():
    user = User(email="new@shop.com", first_name="New", last_name="User", role=Role.CASHIER)
    user.require_password_change()
    assert user.must_change_password is True


def test_a_user_who_has_never_signed_in_is_on_their_first_login():
    user = User(email="new@shop.com", first_name="New", last_name="User", role=Role.CASHIER)

    assert user.is_first_login is True


def test_a_user_with_a_login_timestamp_has_signed_in_before():
    from datetime import UTC, datetime

    user = User(
        email="known@shop.com",
        first_name="Known",
        last_name="User",
        role=Role.CASHIER,
        last_login=datetime(2026, 10, 18, 9, 0, tzinfo=UTC),
    )

    assert user.is_first_login is False


def test_a_user_is_not_a_superuser_by_default():
    user = User(email="person@shop.com", first_name="Person", last_name="User", role=Role.ADMIN)

    assert user.is_superuser is False


def test_requiring_a_password_change_twice_keeps_the_flag():
    user = User(email="twice@shop.com", first_name="Twice", last_name="User", role=Role.CASHIER)

    user.require_password_change()
    user.require_password_change()

    assert user.must_change_password is True


def test_a_successful_login_ends_the_first_login():
    user = User(email="fresh@shop.com", first_name="Fresh", last_name="User", role=Role.CASHIER)
    user.register_successful_login()

    assert user.is_first_login is False
    assert user.last_login is not None


def test_a_new_user_has_no_login_timestamp():
    user = User(email="blank@shop.com", first_name="Blank", last_name="User", role=Role.CASHIER)

    assert user.last_login is None
