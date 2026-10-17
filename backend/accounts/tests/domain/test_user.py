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
