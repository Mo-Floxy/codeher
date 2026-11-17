"""`manage.py seed` must not mint published logins on somebody else's database.

The demo accounts' passwords are committed in `apps/core/seed/community_seed.py` and the
README instructs people to run the command, so the one configuration mistake that turns
them from a development convenience into a live admin login is a `.env` that points at
TiDB Cloud. Nothing else about the command changes; only that is refused.
"""

import pytest
from django.core.management.base import CommandError

from apps.core.management.commands import seed as seed_module
from apps.core.management.commands.seed import Command, local_database

SQLITE = {"ENGINE": "django.db.backends.sqlite3", "NAME": "dev.sqlite3", "HOST": ""}
TIDB = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "codeher",
    "HOST": "gateway01.us-central-1.prod.aws.tidbcloud.com",
}


@pytest.mark.parametrize(
    "database",
    [
        SQLITE,
        {**SQLITE, "ENGINE": "django.db.backends.mysql", "HOST": ""},
        {**TIDB, "HOST": "localhost"},
        {**TIDB, "HOST": "127.0.0.1"},
    ],
)
def test_databases_on_this_machine_are_seeded(database):
    assert local_database(database)


@pytest.mark.parametrize("database", [TIDB, {**TIDB, "HOST": "db.internal.example.com"}])
def test_databases_elsewhere_are_not_local(database):
    assert not local_database(database)


@pytest.fixture
def command_against_tidb(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(seed_module, "connections", {"default": SimpleNamespace(settings_dict=TIDB)})
    return Command()


def test_seeding_a_cluster_is_refused(command_against_tidb):
    with pytest.raises(CommandError, match="published passwords"):
        command_against_tidb.refuse_remote_database(force=False)


def test_the_owner_of_a_disposable_cluster_can_still_seed(command_against_tidb):
    command_against_tidb.refuse_remote_database(force=True)
