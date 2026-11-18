"""Settings for the automated test suite.

Tests run on SQLite even when the developer's `.env` points at MySQL, so
`pytest` never needs a database server, and so a test can never touch real data.
"""

from config.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {"timeout": 20},
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
MEDIA_ROOT = BASE_DIR / "media-test"  # noqa: F405

# Throttling would make a suite of 200 requests fail for the wrong reason, so every
# scope in settings is lifted to an unreachable rate rather than listed — a new scope
# left out of a hardcoded list would surface as ImproperlyConfigured, not as a
# meaningful failure. The limits themselves are tested where they matter, by
# overriding the rate inside the test (see test_throttles.py and the challenges API).
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        scope: "1000/min" for scope in REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})  # noqa: F405
    },
}

# The runner is never reachable during tests; the challenge tests mock the client.
RUNNER_BASE_URL = "http://127.0.0.1:1"
