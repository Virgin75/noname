import os
from pathlib import Path

APP_VERSION = "0.0.1"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_ROOT = os.path.join(BASE_DIR, "exports")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-pa(=xebpjhbwm79yj^=rqv7bh-(-%h=2y3fa&_4cdp_vdiwy%z"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

if os.environ.get("NPM_BIN_PATH", None):
    NPM_BIN_PATH = os.environ.get("NPM_BIN_PATH")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "tailwind",
    "theme",
    "django_filters",
    "commons",
    "users",
    "contacts",
    "django.forms",
    "django_rq",
    "noname.apps.MainAppConfig",
]
PLUGIN_APPS = []
if os.getenv("env") == "local":
    INSTALLED_APPS.append("django_browser_reload")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = "noname.urls"

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

WSGI_APPLICATION = "noname.wsgi.application"
AUTH_USER_MODEL = "users.Account"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES_POSTGRES_LOCAL = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "default_database",
    "USER": "username",
    "PASSWORD": "password",
    "HOST": "localhost",
    "PORT": 5432,
}

DATABASES = {}
ENV = os.environ.get("env")
match ENV:
    case "local":
        DATABASES["default"] = DATABASES_POSTGRES_LOCAL
    case "test":
        pass
    case "prod":
        pass


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static/"),)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TAILWIND_APP_NAME = "theme"
INTERNAL_IPS = ["127.0.0.1"]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "password")

RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": 0,
        "PASSWORD": REDIS_PASSWORD,
        "DEFAULT_TIMEOUT": 360,
    },
    "high": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": 0,
        "PASSWORD": REDIS_PASSWORD,
        "DEFAULT_TIMEOUT": 360,
    },
    "low": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": 0,
        "PASSWORD": REDIS_PASSWORD,
        "DEFAULT_TIMEOUT": 360,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "rq_console": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "rq_console": {
            "level": "INFO",
            "class": "rq.logutils.ColorizingStreamHandler",
            "formatter": "rq_console",
            "exclude": ["%(asctime)s"],
        },
    },
    "loggers": {
        "rq.worker": {
            "handlers": ["rq_console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}",
    }
}

LOGIN_URL = "/login"

ASYNC_TASK = os.getenv("ASYNC_TASK", "django_rq")  # DJANGO_RQ or MODAL.COM
