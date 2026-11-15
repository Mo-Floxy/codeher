"""HTTP client for the isolated code-runner service.

Django never executes learner code in its own process. Everything goes to the
separate Node runner (see codeher/runner/) which is authenticated with a shared
secret. If the runner is unreachable we raise RunnerUnavailable so the API says
503 — a missing sandbox is never reported as a passing solution.
"""

import json
import logging

import requests
from django.conf import settings

from apps.core.exceptions import RunnerUnavailable

logger = logging.getLogger("apps.challenges.runner")


class RunnerPayloadTooLarge(Exception):
    pass


def _headers():
    return {
        "Content-Type": "application/json",
        "X-Runner-Secret": settings.RUNNER_SHARED_SECRET,
    }


def run(code, language, function_name, tests, time_limit_ms=None, memory_limit_mb=None):
    """Execute `code` in the sandbox and return the runner's report dict."""
    if len(code.encode("utf-8")) > settings.RUNNER_MAX_CODE_BYTES:
        raise RunnerPayloadTooLarge("Your submission is larger than the runner allows.")

    payload = {
        "language": language,
        "code": code,
        "function_name": function_name,
        "time_limit_ms": int(time_limit_ms or settings.RUNNER_TIMEOUT_SECONDS * 1000),
        "memory_limit_mb": int(memory_limit_mb or 128),
        "tests": [
            {"name": test["name"], "args": test["args"], "expected": test["expected"]} for test in tests
        ],
    }

    url = f"{settings.RUNNER_BASE_URL.rstrip('/')}/run"
    try:
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=_headers(),
            timeout=settings.RUNNER_TIMEOUT_SECONDS + 5,
        )
    except requests.RequestException as exc:
        logger.warning("Runner unreachable at %s: %s", url, exc)
        raise RunnerUnavailable(
            "The code runner service is not reachable. Start it with the command in the README, then try again."
        ) from exc

    if response.status_code == 401:
        logger.error("Runner rejected the shared secret — check RUNNER_SHARED_SECRET in both services.")
        raise RunnerUnavailable("The code runner rejected this request. Check RUNNER_SHARED_SECRET in backend/.env.")

    if response.status_code >= 400:
        logger.error("Runner error %s: %s", response.status_code, response.text[:500])
        raise RunnerUnavailable("The code runner failed to process this submission.")

    try:
        report = response.json()
    except ValueError as exc:
        raise RunnerUnavailable("The code runner returned an unreadable response.") from exc

    report.setdefault("results", [])
    report.setdefault("runtime_ms", 0)
    return report
