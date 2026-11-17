"""Settings for running the suite against a real MySQL-family server.

`config.test_settings` deliberately uses in-memory SQLite so `pytest` needs no
database server. That is also why the schema guarantees that MySQL and TiDB skip
were never executed in CI: SQLite honours conditional unique indexes, so the
tests pass on the one backend that will never have to hold them in production.

This module keeps every other test setting and swaps only the engine, so a CI
job with a disposable MySQL container exercises the generated-column migrations
and the IntegrityError handling for real.

    .venv/Scripts/python.exe -m pytest -o DJANGO_SETTINGS_MODULE=config.mysql_test_settings

The container's credentials come from the environment, exactly as in production:

    DB_ENGINE=mysql MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=root \
    MYSQL_DATABASE=codeher_test DJANGO_SECRET_KEY=... JWT_SIGNING_KEY=...
"""

import os

os.environ["DB_ENGINE"] = "mysql"

from config.settings import *  # noqa: E402,F401,F403
from config.settings import env  # noqa: E402

# The local container is reached over a plain socket, so the TiDB CA bundle in
# .env must never be picked up here. Both flags have to be set before config.settings
# builds DATABASES, which reads the environment at import time.
os.environ.setdefault("MYSQL_SSL", "false")
os.environ.pop("MYSQL_SSL_CA", None)

DATABASES = {
    "default": {
        **DATABASES["default"],
        # A test database is created and dropped by the runner; the container is
        # disposable, but the name is still kept distinct from the real schema.
        "NAME": env("MYSQL_TEST_DATABASE", "codeher_test"),
        "USER": env("MYSQL_USER", "root"),
        "PASSWORD": env("MYSQL_PASSWORD", ""),
        "HOST": env("MYSQL_HOST", "127.0.0.1"),
        "PORT": env("MYSQL_PORT", "3306"),
        # The container answers on the same machine, so the serverless reconnect
        # tuning from production is noise here.
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_unicode_ci"},
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
MEDIA_ROOT = str(BASE_DIR / "media-test")  # noqa: F405

REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"auth": "1000/min", "sandbox": "1000/min"}}  # noqa: F405

# The runner is never reachable during tests; the challenge tests mock the client.
RUNNER_BASE_URL = "http://127.0.0.1:1"
