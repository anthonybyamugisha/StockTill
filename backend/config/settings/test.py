from .base import *  # noqa: F401, F403

DATABASES["default"]["NAME"] = "test_stocktill"  # noqa: F405
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # noqa: F405

PAYMENTS_ALLOW_FAKE_GATEWAY = True
