import pytest
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher

TEMPORARY_PASSWORD = "temporary1"
PERMANENT_PASSWORD = "permanent12"


def build_user(email: str, role: Role = Role.CASHIER, pending: bool = False) -> UserModel:
    user = User(email=email, first_name="Test", last_name="User", role=role)
    user.set_password(TEMPORARY_PASSWORD, DjangoPasswordHasher())
    if pending:
        user.require_password_change()
    return UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
        must_change_password=user.must_change_password,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return build_user("admin@shop.com", Role.ADMIN)


@pytest.fixture
def pending_user(db):
    return build_user("pending@shop.com", Role.CASHIER, pending=True)


def sign_in(client: APIClient, email: str, password: str = TEMPORARY_PASSWORD):
    return client.post("/api/v1/accounts/login/", {"email": email, "password": password})


@pytest.mark.django_db
def test_created_user_starts_with_a_pending_password(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        "/api/v1/accounts/users/",
        {
            "email": "new@shop.com",
            "first_name": "New",
            "last_name": "User",
            "role": "cashier",
            "password": "welcome123",
        },
    )

    assert response.status_code == 201
    assert response.data["must_change_password"] is True
    assert UserModel.objects.get(email="new@shop.com").must_change_password is True


@pytest.mark.django_db
def test_login_reports_the_pending_flag(api_client, pending_user):
    response = sign_in(api_client, pending_user.email)

    assert response.status_code == 200
    assert response.data["must_change_password"] is True


@pytest.mark.django_db
def test_pending_user_is_blocked_from_business_endpoints(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/v1/catalog/products/")

    assert response.status_code == 403
    assert response.json()["code"] == "password_change_required"


@pytest.mark.django_db
def test_pending_user_can_read_their_profile(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.get("/api/v1/accounts/me/")

    assert response.status_code == 200
    assert response.data["email"] == pending_user.email
    assert response.data["must_change_password"] is True


@pytest.mark.django_db
def test_pending_user_can_change_the_password(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    assert response.status_code == 200
    assert response.data["must_change_password"] is False
    pending_user.refresh_from_db()
    assert DjangoPasswordHasher().verify(PERMANENT_PASSWORD, pending_user.password)


@pytest.mark.django_db
def test_old_password_stops_working_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    fresh_client = APIClient()
    response = sign_in(fresh_client, pending_user.email, TEMPORARY_PASSWORD)

    assert response.status_code == 401


@pytest.mark.django_db
def test_new_password_works_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    fresh_client = APIClient()
    response = sign_in(fresh_client, pending_user.email, PERMANENT_PASSWORD)

    assert response.status_code == 200
    assert response.data["must_change_password"] is False


@pytest.mark.django_db
def test_business_endpoints_reopen_after_a_change(api_client, pending_user):
    sign_in(api_client, pending_user.email)
    api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": PERMANENT_PASSWORD},
    )

    response = api_client.get("/api/v1/catalog/products/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_weak_password_is_rejected_over_the_api(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": "onlyletters"},
    )

    assert response.status_code == 400
    assert "letter and one number" in response.data["detail"]


@pytest.mark.django_db
def test_short_password_is_rejected_over_the_api(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": "short1"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_reusing_the_temporary_password_is_rejected(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": TEMPORARY_PASSWORD, "new_password": TEMPORARY_PASSWORD},
    )

    assert response.status_code == 400
    assert "must be different" in response.data["detail"]


@pytest.mark.django_db
def test_wrong_current_password_is_rejected(api_client, pending_user):
    sign_in(api_client, pending_user.email)

    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {"current_password": "not-the-password", "new_password": PERMANENT_PASSWORD},
    )

    assert response.status_code == 400
    assert "Current password is incorrect" in response.data["detail"]
