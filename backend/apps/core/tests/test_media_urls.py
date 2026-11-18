"""The URL-to-storage-name rule on its own.

`MediaUrlField` uses this to turn what a browser was handed back into a path the
storage backend may open, so the refusals are the interesting half: a name that
climbs out of the media root becomes a file the site serves as its own, and the
encoded form of that climb is what a client actually sends.
"""

import pytest
from django.test import override_settings

from apps.core.media import storage_name


@pytest.mark.parametrize(
    "value,expected",
    [
        ("/media/avatars/9f2c.png", "avatars/9f2c.png"),
        ("http://127.0.0.1:8000/media/uploads/ab.jpg", "uploads/ab.jpg"),
        ("/media/project-screenshots/x.png?v=2", "project-screenshots/x.png"),
        ("/media/avatars//9f2c.png", "avatars/9f2c.png"),
    ],
)
def test_our_own_media_urls_resolve_to_a_storage_name(value, expected):
    assert storage_name(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "/media/../secrets.png",
        "/media/avatars/../../private/keys.txt",
        "/media/%2e%2e/secrets.png",
        "/media/secret-folder/x.png",
        "/media/avatars",
        "/static/x.png",
        "https://elsewhere.example/x.png",
        "avatars/9f2c.png",
        "",
        "   ",
        None,
        17,
    ],
)
def test_anything_that_is_not_a_stored_image_of_ours_is_refused(value):
    assert storage_name(value) is None


def test_a_media_url_without_a_leading_slash_still_works():
    """`MEDIA_URL` is operator-set, and the prefix match must not depend on it."""
    with override_settings(MEDIA_URL="media/"):
        assert storage_name("/media/avatars/x.png") == "avatars/x.png"
        assert storage_name("/other/avatars/x.png") is None
