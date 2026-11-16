"""Notification dedupe is enforced by the schema, not only by `notify()`'s pre-check.

The old constraint was conditional (`~Q(dedupe_key="")`) and MySQL/TiDB never created it,
so a re-triggered achievement or an edited comment could double up in an inbox. Rows with
a blank key get a NULL `dedupe_ref` and stay exempt from the new plain index.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.notifications.models import Notification
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def recipient(db):
    return User.objects.create_user(
        email="ada@example.com", username="ada", password="Str0ngPass!", display_name="Ada"
    )


def make_notification(recipient, dedupe_key, title="Something happened"):
    return Notification.objects.create(recipient=recipient, kind="achievement", title=title, dedupe_key=dedupe_key)


def test_the_same_dedupe_key_cannot_be_delivered_twice(recipient):
    make_notification(recipient, "achievement:first-commit")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_notification(recipient, "achievement:first-commit", title="Re-triggered")

    assert Notification.objects.count() == 1


def test_keyless_notifications_are_not_deduplicated(recipient):
    """An announcement has no natural key, so each one must still reach the inbox."""
    make_notification(recipient, "")
    make_notification(recipient, "")

    assert Notification.objects.count() == 2
    assert set(Notification.objects.values_list("dedupe_ref", flat=True)) == {None}


def test_dedupe_is_scoped_per_recipient_and_kind(recipient, db):
    other = User.objects.create_user(
        email="nia@example.com", username="nia", password="Str0ngPass!", display_name="Nia"
    )
    Notification.objects.create(recipient=recipient, kind="achievement", title="T", dedupe_key="shared")
    Notification.objects.create(recipient=other, kind="achievement", title="T", dedupe_key="shared")
    Notification.objects.create(recipient=recipient, kind="follow", title="T", dedupe_key="shared")

    assert Notification.objects.count() == 3
