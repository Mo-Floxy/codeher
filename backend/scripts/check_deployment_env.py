"""Say whether the current environment is safe to deploy into — without printing it.

Render and TiDB both accept an incomplete set of variables and quietly fall back to
development defaults, so a "successful" deploy can end up serving with DEBUG on, a
secret key of `insecure-dev-only-change-me`, a runner shared secret of
`dev-runner-secret`, or plaintext credentials to a serverless database. Every one of
those looks healthy in a deploy log until someone exploits it.

Run it where the real values are set — in Render's shell, or locally after sourcing
the file that holds them:

    python scripts/check_deployment_env.py --dotenv .env
    python scripts/check_deployment_env.py

Reports variable *names* and what is wrong with them, never their contents, so its
output is safe to paste into a bug report or a chat window.
"""

import argparse
import os
import sys

PLACEHOLDERS = {
    "",
    "replace-with-a-long-random-string",
    "replace-with-a-second-long-random-string",
    "insecure-dev-only-change-me",
    "change-me-and-match-runner-env",
    "ci-only-insecure-key",
    "dev-runner-secret",
    "set-during-database-setup",
    "changeme",
    "changeme-too",
    "change-me",
}

LOCAL_HOSTS = ("127.0.0.1", "localhost", "testserver", "0.0.0.0", "[::1]")

# render.yaml and README ship hostnames like `your-api.onrender.com`. They are syntactically
# valid and a real request to them fails, so they need their own message.
TEMPLATE_HOST = "your-"

issues = []


def fatal(name, reason):
    issues.append((True, name, reason))


def warn(name, reason):
    issues.append((False, name, reason))


def read(name):
    return os.environ.get(name, "")


def is_placeholder(value):
    return value.strip() in PLACEHOLDERS


def is_true(value):
    return value.strip().lower() in {"1", "true", "yes", "on"}


def has_local_host(value):
    return any(token in value for token in LOCAL_HOSTS)


def has_template_host(value):
    return TEMPLATE_HOST in value


def has_insecure_url(value):
    return "http://" in value


def check_secrets():
    if is_true(read("DJANGO_DEBUG")):
        fatal(
            "DJANGO_DEBUG",
            "True exposes tracebacks and /django-admin/ to the internet; production must set False",
        )
    key = read("DJANGO_SECRET_KEY")
    if is_placeholder(key):
        fatal("DJANGO_SECRET_KEY", "missing or still a placeholder — sessions and password-reset tokens are guessable")
    elif len(key) < 50:
        warn("DJANGO_SECRET_KEY", "shorter than 50 characters; use a full random string")
    if is_placeholder(read("JWT_SIGNING_KEY")):
        warn(
            "JWT_SIGNING_KEY",
            "not set, so tokens are signed with DJANGO_SECRET_KEY; a key rotation then logs everyone out and one leak becomes two",
        )


def check_database():
    engine = (read("DB_ENGINE") or "mysql").strip().lower()
    if engine == "sqlite":
        warn("DB_ENGINE", "sqlite is a smoke-test fallback, not the deployment target")
        return
    for name, reason in (
        ("MYSQL_HOST", "the cluster address, ending in .tidbcloud.com"),
        ("MYSQL_USER", "the database user, usually <user>%<cluster-id> on TiDB"),
        ("MYSQL_PASSWORD", "the database password"),
        ("MYSQL_DATABASE", "the schema name"),
    ):
        if is_placeholder(read(name)):
            fatal(name, f"missing — {reason}")
    host = read("MYSQL_HOST").strip().lower()
    port = read("MYSQL_PORT").strip()
    if host.endswith(".tidbcloud.com") and port not in {"", "4000"}:
        fatal(
            "MYSQL_PORT",
            "TiDB Cloud Serverless listens on 4000; a wrong port hangs until it times out "
            "and looks exactly like a blocked network allowlist",
        )
    if is_placeholder(read("MYSQL_SSL_CA")) and not is_true(read("MYSQL_SSL")):
        warn(
            "MYSQL_SSL_CA",
            "unset, so credentials and rows travel unencrypted; TiDB Cloud publishes a CA bundle for the Starter tier",
        )


def check_origins():
    hosts = read("DJANGO_ALLOWED_HOSTS")
    if "*" in hosts:
        fatal("DJANGO_ALLOWED_HOSTS", "wildcard turns off Host-header validation, which is what blocks cache poisoning")
    elif is_placeholder(hosts) or has_local_host(hosts.replace("testserver", "")):
        fatal("DJANGO_ALLOWED_HOSTS", "still only local hosts — every request to the real domain answers 400")
    elif has_template_host(hosts):
        fatal("DJANGO_ALLOWED_HOSTS", "still the placeholder hostname from the template")
    for name in ("CORS_ALLOWED_ORIGINS", "DJANGO_CSRF_TRUSTED_ORIGINS", "FRONTEND_ORIGIN"):
        value = read(name)
        if is_placeholder(value):
            extra = " It also decides where password-reset links point." if name == "FRONTEND_ORIGIN" else ""
            warn(name, f"unset, so the development default applies and the deployed frontend is not in it.{extra}")
            continue
        if has_local_host(value):
            fatal(name, "points at 127.0.0.1/localhost, which no browser on the internet can be")
        elif has_template_host(value):
            fatal(
                name,
                "still the placeholder hostname from the template — replace it with the URL "
                "Render or Vercel actually gave you, or the site loads and every request is refused",
            )
        elif has_insecure_url(value):
            warn(name, "uses http://; Render and Vercel both serve https and cookies here are Secure-only")


def check_runner():
    if is_placeholder(read("RUNNER_SHARED_SECRET")):
        fatal(
            "RUNNER_SHARED_SECRET",
            "missing or left at the development default — settings falls back to the literal dev-runner-secret, and anyone who reads the repo can run code on your runner",
        )
    base = read("RUNNER_BASE_URL")
    if is_placeholder(base):
        fatal("RUNNER_BASE_URL", "missing, so submissions cannot reach the runner at all")
    elif has_local_host(base):
        fatal("RUNNER_BASE_URL", "points at 127.0.0.1; on Render that is the API container itself, not the runner")
    elif has_template_host(base):
        fatal("RUNNER_BASE_URL", "still the placeholder hostname from the template — use the URL the runner service actually has")
    elif has_insecure_url(base):
        warn("RUNNER_BASE_URL", "uses http://, so the shared secret crosses the network in the clear")


def check_email_and_media():
    backend = read("DJANGO_EMAIL_BACKEND")
    if "console" in backend or is_placeholder(backend):
        warn(
            "DJANGO_EMAIL_BACKEND",
            "writes mail to the log instead of sending it, so password-reset emails never arrive (the link still prints in DEBUG)",
        )
    elif "smtp" in backend:
        for name in ("EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL"):
            if is_placeholder(read(name)):
                fatal(name, "needed by the SMTP backend; without it every reset attempt raises after the token is issued")
    if is_true(read("SERVE_MEDIA_IN_PRODUCTION")):
        warn(
            "SERVE_MEDIA_IN_PRODUCTION",
            "Render's free filesystem is wiped on each deploy — uploads survive only on a persistent disk"
        )


def main():
    # Windows consoles open on cp1252, which turns the prose dashes in this report into
    # question marks - and a report nobody can read is not a report.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dotenv", help="load this file first (e.g. .env) instead of the ambient environment")
    args = parser.parse_args()

    if args.dotenv:
        from dotenv import load_dotenv

        load_dotenv(args.dotenv, override=True)

    if not os.environ.get("DJANGO_SECRET_KEY") and not args.dotenv:
        warn("(environment)", "no DJANGO_SECRET_KEY at all — did you mean --dotenv .env, or to run this on Render?")

    check_secrets()
    check_database()
    check_origins()
    check_runner()
    check_email_and_media()

    fatal_count = 0
    for is_fatal, name, reason in issues:
        fatal_count += 1 if is_fatal else 0
        print(f"{'FATAL' if is_fatal else 'warn '}  {name} — {reason}")

    if fatal_count:
        print(f"\n{fatal_count} blocking issue(s): fix them before deploying, this is not a warning list.")
        return 1
    if issues:
        print("\nNo blockers. The warnings above are features that will not work as advertised.")
    else:
        print("OK: this environment looks safe to deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
