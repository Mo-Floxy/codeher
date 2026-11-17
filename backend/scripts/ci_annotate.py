"""Turn captured test output into a single workflow annotation.

GitHub only shows the last line of a failing step to anyone reading the check
run, and the raw log needs repository permissions. That leaves a red CI job with
no reachable explanation for the person who has to act on it — including a bot
reading the API. So the suite output is piped through here on failure:

    python -m pytest 2>&1 | tee /tmp/pytest.log
    tail -n 60 /tmp/pytest.log | python scripts/ci_annotate.py

The traceback tail is the part that identifies the failure. An annotation also
has a hard size limit and an over-long one is discarded rather than truncated,
so the budget below keeps the end of the capture and drops its beginning.
"""

import sys

# Character budget for the escaped message, leaving room for the command prefix.
MAX_CHARS = 3200


def escape(text: str) -> str:
    # GitHub's workflow command syntax reserves %, \r and \n inside the message.
    return (
        text.replace("%", "%25")
        .replace("\r", "")
        .replace("\n", "%0A")
    )


def main() -> int:
    body = sys.stdin.read().strip()
    if not body:
        body = "no output captured"
    message = escape(body)
    if len(message) > MAX_CHARS:
        message = "… truncated …%0A" + message[-MAX_CHARS:]
    print(f"::error::CI step failed%0A%0A{message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
