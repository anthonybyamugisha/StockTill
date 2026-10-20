from uuid import uuid4

import pytest

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from reporting.infrastructure.directories import CashierDirectory


def _user(email: str, first_name: str, last_name: str) -> UserModel:
    user = User(email=email, first_name=first_name, last_name=last_name, role=Role.CASHIER)
    user.set_password("password123", DjangoPasswordHasher())
    return UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
    )


@pytest.mark.django_db
def test_labels_join_the_first_and_last_name():
    cashier = _user("grace@shop.com", "Grace", "Nakato")

    labels = CashierDirectory.load()

    assert labels.label_for(cashier.id) == "Grace Nakato"


@pytest.mark.django_db
def test_labels_fall_back_to_the_email_when_both_names_are_blank():
    cashier = _user("anon@shop.com", "", "")

    labels = CashierDirectory.load()

    assert labels.label_for(cashier.id) == "anon@shop.com"


@pytest.mark.django_db
def test_unknown_cashiers_get_an_empty_label():
    assert CashierDirectory.load().label_for(uuid4()) == ""
