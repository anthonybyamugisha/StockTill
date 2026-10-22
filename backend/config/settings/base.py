import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "accounts",
    "catalog",
    "inventory",
    "sales",
    "payments",
    "shifts",
    "purchasing",
    "reporting",
    "settings",
]

AUTH_USER_MODEL = "accounts.UserModel"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.interfaces.api.middleware.RequirePasswordChangeMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES: dict[str, Any] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "stocktill"),
        "USER": os.environ.get("POSTGRES_USER", "stocktill"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "stocktill"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

if os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=os.environ["DATABASE_URL"].startswith(("postgres", "postgresql")),
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Kampala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "StockTill API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Point of Sale and Inventory Management System",
}


def _split_origins(variable: str, default: str) -> list[str]:
    raw = os.environ.get(variable, default)
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


CORS_ALLOWED_ORIGINS = _split_origins("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = _split_origins("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")

PAYMENTS_ALLOW_FAKE_GATEWAY = (
    os.environ.get("PAYMENTS_ALLOW_FAKE_GATEWAY", "false").lower() == "true"
)
PAYMENTS_CALLBACK_SECRET = os.environ.get("PAYMENTS_CALLBACK_SECRET", "")
PAYMENTS_INTENT_TTL_SECONDS = int(os.environ.get("PAYMENTS_INTENT_TTL_SECONDS", "300"))

MTN_MOMO_BASE_URL = os.environ.get("MTN_MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
MTN_MOMO_SUBSCRIPTION_KEY = os.environ.get("MTN_MOMO_SUBSCRIPTION_KEY", "")
MTN_MOMO_API_USER = os.environ.get("MTN_MOMO_API_USER", "")
MTN_MOMO_API_KEY = os.environ.get("MTN_MOMO_API_KEY", "")
MTN_MOMO_TARGET_ENVIRONMENT = os.environ.get("MTN_MOMO_TARGET_ENVIRONMENT", "sandbox")
MTN_MOMO_CALLBACK_URL = os.environ.get("MTN_MOMO_CALLBACK_URL", "")

AIRTEL_MONEY_BASE_URL = os.environ.get("AIRTEL_MONEY_BASE_URL", "https://openapiuat.airtel.ug")
AIRTEL_MONEY_CLIENT_ID = os.environ.get("AIRTEL_MONEY_CLIENT_ID", "")
AIRTEL_MONEY_CLIENT_SECRET = os.environ.get("AIRTEL_MONEY_CLIENT_SECRET", "")
AIRTEL_MONEY_COUNTRY = os.environ.get("AIRTEL_MONEY_COUNTRY", "UG")
AIRTEL_MONEY_CURRENCY = os.environ.get("AIRTEL_MONEY_CURRENCY", "UGX")
AIRTEL_MONEY_CALLBACK_URL = os.environ.get("AIRTEL_MONEY_CALLBACK_URL", "")
AIRTEL_MONEY_SIMULATE = os.environ.get("AIRTEL_MONEY_SIMULATE", "false").lower() == "true"
AIRTEL_MONEY_SIGN_REQUESTS = os.environ.get("AIRTEL_MONEY_SIGN_REQUESTS", "true").lower() == "true"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
