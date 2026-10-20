import pytest

from accounts.interfaces.api.middleware import PENDING_PASSWORD_PATHS, is_password_change_path


@pytest.mark.parametrize("path", PENDING_PASSWORD_PATHS)
def test_allowed_paths_are_exact(path):
    assert is_password_change_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/catalog/products/",
        "/api/v1/accounts/users/",
        "/api/v1/accounts/me/extra/",
        "/api/v1/accounts/login/extra/",
        "/api/v1/health/deep/",
    ],
)
def test_lookalike_paths_are_blocked(path):
    assert is_password_change_path(path) is False
