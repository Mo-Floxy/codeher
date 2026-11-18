"""Django settings for CodeHer.

Everything environment-specific comes from backend/.env (see .env.example).
Database credentials and secrets must never be committed or duplicated in the frontend.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key, default=None):
    value = os.environ.get(key, default)
    return None if value == "" else value


def env_bool(key, default=False):
    value = env(key)
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes", "on"}


def env_list(key, default=None):
    value = env(key)
    if not value:
        return list(default or [])
    return [item.strip() for item in str(value).split(",") if item.strip()]


LOCAL_DB_HOSTS = {"", "127.0.0.1", "localhost", "::1", "0.0.0.0"}


def mysql_ssl_options(host, ca="", check_hostname=True, force=False):
    """Build the PyMySQL ``ssl`` argument that actually authenticates the server.

    PyMySQL encrypts even with no ``ssl`` argument, but only sets
    ``check_hostname=False`` and ``verify_mode=CERT_NONE`` in that case, so "encrypted"
    there still means anyone on the path can terminate TLS and read the credentials.
    Handing it a non-empty dict restores the OpenSSL defaults, and ``{"ca": ""}`` means
    "use the operating system trust store" - which already contains the Let's Encrypt root
    that TiDB Cloud Starter serves, so no certificate file has to be shipped.

    Local hosts are left unverified on purpose: a development MySQL uses a self-signed
    certificate, and CI's container must keep connecting.
    """
    if ca:
        return {"ca": ca, "check_hostname": bool(check_hostname)}
    if check_hostname and (force or str(host).strip().lower() not in LOCAL_DB_HOSTS):
        return {"ca": ""}
    return {}


# ------------------------------------------------------------------ security
SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-dev-only-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["127.0.0.1", "localhost", "testserver"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", ["http://127.0.0.1:5173", "http://localhost:5173"])

# Render injects each service's own hostname. Trusting it means a service that is renamed in
# the dashboard, or deployed before DJANGO_ALLOWED_HOSTS was filled in, still serves traffic
# instead of Django answering 400 (and /django-admin/ answering 403) before any view runs.
RENDER_HOST = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    if RENDER_HOST not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_HOST)
    render_origin = f"https://{RENDER_HOST}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# ---------------------------------------------------------------------- apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "apps.core",
    "apps.users",
    "apps.courses",
    "apps.progress",
    "apps.challenges",
    "apps.community",
    "apps.mentorship",
    "apps.achievements",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Serves the collected admin/static assets from the web process, which is what a
    # single Render service without an nginx sidecar needs.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLogMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# ------------------------------------------------------------------ database
DB_ENGINE = (env("DB_ENGINE") or "mysql").lower()

if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev.sqlite3",
        }
    }
else:
    # MySQL and TiDB Cloud share this branch: TiDB speaks the MySQL wire protocol and
    # Django uses the same backend for both.
    mysql_options = {
        "charset": "utf8mb4",
        # Every text column is utf8mb4 so emoji and accents survive round-trips.
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        # Serverless proxies answer slowly while an instance wakes up; without this a
        # cold start holds a request open indefinitely instead of failing fast.
        "connect_timeout": int(env("MYSQL_CONNECT_TIMEOUT", 10)),
        "read_timeout": int(env("MYSQL_READ_TIMEOUT", 30)),
        "write_timeout": int(env("MYSQL_WRITE_TIMEOUT", 30)),
    }
    # TiDB Cloud enforces TLS ("Connections using insecure transport are prohibited"), so
    # the only question is whether the server is verified as well. It is, by default.
    ssl_options = mysql_ssl_options(
        env("MYSQL_HOST", "127.0.0.1"),
        ca=env("MYSQL_SSL_CA", ""),
        check_hostname=env_bool("MYSQL_SSL_CHECK_HOSTNAME", True),
        force=env_bool("MYSQL_SSL", False),
    )
    if ssl_options:
        mysql_options["ssl"] = ssl_options

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("MYSQL_DATABASE", "codeher"),
            "USER": env("MYSQL_USER", "codeher_app"),
            "PASSWORD": env("MYSQL_PASSWORD", ""),
            "HOST": env("MYSQL_HOST", "127.0.0.1"),
            "PORT": env("MYSQL_PORT", "3306"),
            # A pooled connection to a serverless instance can be closed server-side at
            # any moment; health checks turn that into a reconnect instead of a 500.
            "CONN_MAX_AGE": int(env("MYSQL_CONN_MAX_AGE", 0 if not DEBUG else 60)),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": mysql_options,
            "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_unicode_ci"},
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------- auth
AUTH_USER_MODEL = "users.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Frontend registration mirrors these rules client-side; keep them in sync.
MIN_PASSWORD_LENGTH = 8

# ------------------------------------------------------------------ rest jwt
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 12,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "NON_FIELD_ERRORS_KEY": "detail",
    "DEFAULT_THROTTLE_RATES": {
        "auth": env("THROTTLE_AUTH", "30/min"),
        "sandbox": env("THROTTLE_SANDBOX", "20/min"),
        # Uploads are the one endpoint where a request costs disk instead of CPU, and
        # a logged-in account is cheap to make: cap the bytes one user can park.
        "uploads": env("THROTTLE_UPLOADS", "30/hr"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", 30))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_REFRESH_MINUTES", 60 * 24 * 14))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "SIGNING_KEY": env("JWT_SIGNING_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------- cors
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    ["http://127.0.0.1:5173", "http://localhost:5173"],
)
CORS_ALLOW_CREDENTIALS = False

# ------------------------------------------------------------------ static/media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    # Hashed, gzipped/brotli assets served by WhiteNoise from this process.
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
MEDIA_URL = env("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(env("MEDIA_ROOT") or BASE_DIR / "media")
# Uploaded avatars and project screenshots are files, not database rows. Render's free
# instance filesystem is wiped on each deploy, so serving them from disk is a
# development convenience: set SERVE_MEDIA_IN_PRODUCTION=1 only with a disk attached,
# and point Django at object storage for anything that must survive a re-deploy.
SERVE_MEDIA_IN_PRODUCTION = env_bool("SERVE_MEDIA_IN_PRODUCTION", False)

# --------------------------------------------------------------------- languages
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------- sandbox
# The runner service executes user code. Django only ever talks HTTP to it and
# never imports or eval()s submission code in-process.
RUNNER_BASE_URL = env("RUNNER_BASE_URL", "http://127.0.0.1:8090")
RUNNER_SHARED_SECRET = env("RUNNER_SHARED_SECRET", "dev-runner-secret")
RUNNER_TIMEOUT_SECONDS = float(env("RUNNER_TIMEOUT_SECONDS", 12))
RUNNER_MAX_CODE_BYTES = int(env("RUNNER_MAX_CODE_BYTES", 20000))

# ---------------------------------------------------------------------- email
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", 587))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "CodeHer <no-reply@codeher.local>")
PASSWORD_RESET_TIMEOUT_HOURS = int(env("PASSWORD_RESET_TIMEOUT_HOURS", 24))
PASSWORD_RESET_TIMEOUT = PASSWORD_RESET_TIMEOUT_HOURS * 3600
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", "http://127.0.0.1:5173")

# ------------------------------------------------------------------- logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {
        "apps": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO"), "propagate": False},
        "codeher.runner": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# --------------------------------------------------------------- gamification
# Tuning knobs for XP/levels. Kept here so rewards are consistent and auditable.
XP_RULES = {
    "lesson_complete": int(env("XP_LESSON", 20)),
    "quiz_pass": int(env("XP_QUIZ_PASS", 40)),
    "course_complete": int(env("XP_COURSE", 150)),
    "challenge_solve": int(env("XP_CHALLENGE", 0)),  # uses the challenge's own points
    "project_publish": int(env("XP_PROJECT", 60)),
    "mentor_match": int(env("XP_MENTOR_MATCH", 50)),
}

LEVEL_THRESHOLDS = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000, 5000]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", "same-origin")

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    )
