import os
from pathlib import Path

from dotenv import load_dotenv

from integration_utils.bitrix24.local_settings_class import LocalSettingsClass

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in the environment variables.")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

CSRF_TRUSTED_ORIGINS = []
if os.getenv("DOMAIN"):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('DOMAIN')}")
if os.getenv("NGROK_URL"):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('NGROK_URL')}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "integration_utils.bitrix24",
    "apps.home",
    "apps.deals",
    "apps.product_qr",
    "apps.employees",
    "apps.companies_map",
    "apps.contact_manager",
]

MIDDLEWARE = [
    "config.middleware.NgrokSkipWarningMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST", "localhost"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

X_FRAME_OPTIONS = "ALLOWALL"

APP_SETTINGS = LocalSettingsClass(
    portal_domain=os.getenv("DOMAIN"),
    app_domain=os.getenv("NGROK_URL"),
    app_name=os.getenv("APP_NAME", "deal_management"),
    salt=os.getenv("BITRIX_SALT", os.getenv("SECRET_KEY")),
    secret_key=os.getenv("SECRET_KEY"),
    application_bitrix_client_id=os.getenv("CLIENT_ID"),
    application_bitrix_client_secret=os.getenv("CLIENT_SECRET"),
    application_index_path=os.getenv("APP_INDEX_PATH", "/"),
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "deals": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "integration_utils": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

CUSTOM_FIELD_NAME = os.getenv("CUSTOM_FIELD_NAME", "UF_CRM_1759500436")
DEFAULT_STAGE = os.getenv("DEFAULT_STAGE", "NEW")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "RUB")
