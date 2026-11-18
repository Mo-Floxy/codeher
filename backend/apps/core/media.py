"""How a saved record may refer to a file this API uploaded.

`/api/uploads/` takes the file and returns a URL; the forms then send that URL back
when they save. DRF's `ImageField` only understands a file riding in the same
multipart request, so a profile or project save that carried the avatar URL it had
been handed was rejected with "The submitted data was not a file" — which, because
those pages echo the current value on every save, failed whether or not the member
had uploaded anything new.
"""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from django.conf import settings
from rest_framework import serializers

# The folders `UploadView` will write into, and the only ones a stored URL may point
# at. One list for both, so the two cannot drift apart.
MEDIA_FOLDERS = ("avatars", "project-screenshots", "course-thumbnails", "uploads")


def storage_name(value):
    """The storage name behind one of our media URLs, or None if it is not one.

    Absolute (`https://host/media/avatars/x.png`, what a browser is given) and
    relative (`/media/…`) both arrive. The prefix must be ours and the remainder must
    stay inside a known folder: this string becomes a path the storage backend opens,
    and an avatar is fetched by everyone who views that profile.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    path = urlsplit(value.strip()).path
    prefix = settings.MEDIA_URL if settings.MEDIA_URL.startswith("/") else "/" + settings.MEDIA_URL
    if not path.startswith(prefix):
        return None
    parts = PurePosixPath(unquote(path[len(prefix) :])).parts
    if len(parts) < 2 or ".." in parts or parts[0] not in MEDIA_FOLDERS:
        return None
    return "/".join(parts)


class MediaUrlField(serializers.ImageField):
    """An image the client already parked in our media storage, named by its URL.

    A file in the request is still validated by PIL, exactly as `ImageField` does;
    a URL is trusted only as a pointer, because its bytes were checked when
    `UploadView` accepted them. Empty or null clears the field — all of these model
    fields are `null=True`, and the settings page sends `""` for "no image".
    """

    def to_internal_value(self, data):
        if data is None or data == "":
            return None
        if isinstance(data, str):
            name = storage_name(data)
            if name is None:
                raise serializers.ValidationError("That is not a file this API uploaded.")
            return name
        return super().to_internal_value(data)
