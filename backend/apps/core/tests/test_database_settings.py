"""The TLS decision for the MySQL/TiDB branch, tested as a pure function.

Reaching these rules through `settings.DATABASES` would need the module re-imported with a
different environment, which re-runs every side effect in settings. The rules were pulled into
`mysql_ssl_options` for that reason as much as for clarity: this is the one place where the
default behaviour of the driver is silently insecure, so it should not be behind an import.
"""

import pytest

from config.settings import LOCAL_DB_HOSTS, mysql_ssl_options


def test_a_remote_database_is_verified_even_without_a_certificate_file():
    # This is the case that used to be wrong: no MYSQL_SSL_CA anywhere. PyMySQL still
    # encrypts then, but with check_hostname=False and verify_mode=CERT_NONE, which a
    # machine-in-the-middle can terminate and read. Non-empty here means verified.
    assert mysql_ssl_options("gateway01.eu-central-1.prod.aws.tidbcloud.com") == {"ca": ""}


def test_a_pinned_bundle_is_still_honoured():
    assert mysql_ssl_options("gateway01.eu-central-1.prod.aws.tidbcloud.com", ca="/etc/tidb/ca.pem") == {
        "ca": "/etc/tidb/ca.pem",
        "check_hostname": True,
    }


def test_turning_off_hostname_checking_only_outranks_verification_when_a_bundle_is_pinned():
    # Without `ca` there is nothing to check the chain against, so declining to verify the
    # name must not quietly drop the connection back to unauthenticated-by-default.
    assert mysql_ssl_options("db.example.com", ca="", check_hostname=False) == {}
    assert mysql_ssl_options("db.example.com", ca="/etc/ssl/db.pem", check_hostname=False) == {
        "ca": "/etc/ssl/db.pem",
        "check_hostname": False,
    }


@pytest.mark.parametrize("host", sorted(LOCAL_DB_HOSTS))
def test_local_databases_stay_unverified(host):
    # A development MySQL and CI's container both present self-signed certificates. Forcing
    # verification there does not make anyone safer and would break the suite outright.
    assert mysql_ssl_options(host) == {}


def test_the_explicit_switch_verifies_a_local_host_too():
    assert mysql_ssl_options("127.0.0.1", force=True) == {"ca": ""}
