"""API tests for the notification inbox.

The inbox is the most personal surface in the platform, so isolation between
recipients is asserted explicitly: a foreign row must 404, never 403-with-data.
"""

import datetime

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications import services
from apps.notifications.models import Notification
from apps.users.models import Profile, User

pytestmark = pytest.mark.django_db


def make_member(username, email, display_name):
    user = User.objects.create_user(
        email=email, username=username, password="inbox-test-pass-1", display_name=display_name
    )
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def recipient(db):
    return make_member("inbox_owner", "inbox@codeher.test", "Inbox Owner")


@pytest.fixture
def intruder(db):
    return make_member("nosey", "nosey@codeher.test", "Nosey Parker")


@pytest.fixture
def api_client(recipient):
    client = APIClient()
    client.force_authenticate(user=recipient)
    return client


@pytest.fixture
def intruder_client(intruder):
    client = APIClient()
    client.force_authenticate(user=intruder)
    return client


def make_row(user, title="Someone replied to you", kind="reply", read=False, **kwargs):
    if read:
        kwargs["read_at"] = timezone.now()
    return Notification.objects.create(
        recipient=user, kind=kind, title=title, body="On your question about lists.", link="/community/posts/9", **kwargs
    )


# ------------------------------------------------------------------------ basics


def test_inbox_requires_authentication():
    client = APIClient()
    assert client.get("/api/notifications/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/notifications/unread-count/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/notifications/read-all/", {}, format="json").status_code == status.HTTP_401_UNAUTHORIZED


def test_list_is_paginated_and_newest_first(api_client, recipient):
    older = make_row(recipient, title="Older")
    newer = make_row(recipient, title="Newer")
    Notification.objects.filter(pk=older.pk).update(created_at=timezone.now() - datetime.timedelta(days=2))

    response = api_client.get("/api/notifications/")
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {"count", "next", "previous", "results"}
    assert response.data["count"] == 2
    assert [row["title"] for row in response.data["results"]] == ["Newer", "Older"]

    row = response.data["results"][0]
    assert row["id"] == newer.pk
    assert row["kind"] == "reply"
    assert row["kind_label"] == "Reply to you"
    assert row["link"] == row["url"] == "/community/posts/9"
    assert row["body"] == row["message"]
    assert row["is_read"] is False and row["is_unread"] is True
    assert row["actor"] is None


def test_unread_only_filter(api_client, recipient):
    make_row(recipient, title="Read one", read=True)
    make_row(recipient, title="Live one")
    assert api_client.get("/api/notifications/", {"unread_only": "true"}).data["count"] == 1
    assert api_client.get("/api/notifications/", {"unread_only": "1"}).data["count"] == 1
    assert api_client.get("/api/notifications/", {"unread_only": "false"}).data["count"] == 2
    assert api_client.get("/api/notifications/").data["count"] == 2
    assert api_client.get("/api/notifications/", {"kind": "achievement"}).data["count"] == 0


def test_archived_rows_stay_hidden(api_client, recipient):
    make_row(recipient, title="Dismissed earlier", archived_at=timezone.now())
    make_row(recipient, title="Still here")
    assert api_client.get("/api/notifications/").data["count"] == 1


# ------------------------------------------------------------- read / read-all


def test_unread_count_and_mark_one_read(api_client, recipient):
    first = make_row(recipient, title="First")
    make_row(recipient, title="Second")
    assert api_client.get("/api/notifications/unread-count/").data == {"count": 2}

    response = api_client.post("/api/notifications/{}/read/".format(first.pk), {}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_read"] is True
    assert response.data["read_at"] is not None
    assert api_client.get("/api/notifications/unread-count/").data["count"] == 1

    first.refresh_from_db()
    marked_at = first.read_at
    api_client.post("/api/notifications/{}/read/".format(first.pk), {}, format="json")
    first.refresh_from_db()
    assert first.read_at == marked_at  # idempotent, no timestamp churn


def test_read_all_marks_only_my_rows(api_client, intruder, recipient):
    mine = [make_row(recipient, title="Mine {}".format(index)) for index in range(3)]
    theirs = make_row(intruder, title="Theirs")

    response = api_client.post("/api/notifications/read-all/", {}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["updated"] == 3
    assert response.data["count"] == 0

    for row in mine:
        row.refresh_from_db()
        assert row.read_at is not None
    theirs.refresh_from_db()
    assert theirs.read_at is None
    assert services.unread_count(intruder) == 1


def test_dismiss_deletes_only_the_owner_row(api_client, recipient):
    row = make_row(recipient, title="Goodbye")
    response = api_client.delete("/api/notifications/{}/".format(row.pk))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Notification.objects.filter(pk=row.pk).exists()
    assert api_client.delete("/api/notifications/{}/".format(row.pk)).status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------- isolation


def test_another_members_rows_are_not_visible(intruder_client, recipient, intruder):
    row = make_row(recipient, title="Private")
    make_row(intruder, title="My own")

    listed = intruder_client.get("/api/notifications/").data["results"]
    assert [item["title"] for item in listed] == ["My own"]
    assert row.pk not in [item["id"] for item in listed]

    assert intruder_client.get("/api/notifications/{}/".format(row.pk)).status_code == status.HTTP_404_NOT_FOUND
    assert intruder_client.post("/api/notifications/{}/read/".format(row.pk), {}, format="json").status_code == 404
    assert intruder_client.delete("/api/notifications/{}/".format(row.pk)).status_code == 404
    assert intruder_client.get("/api/notifications/unread-count/").data["count"] == 1

    row.refresh_from_db()
    assert row.read_at is None
    assert row.recipient_id == recipient.pk


def test_notify_helper_dedupes_and_serialises_actor(intruder_client, recipient, intruder):
    created = services.notify(
        recipient, kind="comment", title="New comment", body="Nice try", actor=intruder, dedupe_key="comment:41"
    )
    assert created is not None
    assert services.notify(recipient, kind="comment", title="Again", dedupe_key="comment:41") is None
    assert Notification.objects.filter(recipient=recipient).count() == 1

    payload = intruder_client.get("/api/notifications/").data
    assert payload["count"] == 0  # the row belongs to the recipient, not the actor

    client = APIClient()
    client.force_authenticate(user=recipient)
    row = client.get("/api/notifications/").data["results"][0]
    assert row["actor"]["id"] == intruder.pk
    assert row["actor"]["display_name"] == "Nosey Parker"
    assert row["actor"]["avatar"] is None
