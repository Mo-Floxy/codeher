"""Upload validation: the bytes decide, not the client's `Content-Type`.

The endpoint used to map the declared MIME type to a file extension, which meant a
request saying `image/png` was stored whatever it actually contained. These tests keep
the sniffing honest in both directions — a real image is accepted even when the
declaration is wrong, and a non-image is refused even when the declaration is perfect.
"""

import io
from pathlib import Path

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = "CodeHer!Test2026"


def image_bytes(fmt="PNG", size=(8, 8)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (219, 112, 147)).save(buffer, format=fmt)
    return buffer.getvalue()


def stored_files(storage):
    root = Path(storage.location)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def upload(client, body, content_type, **extra):
    file_field = SimpleUploadedFile("submission", body, content_type=content_type)
    return client.post("/api/uploads/", {"file": file_field, **extra}, format="multipart")


@pytest.fixture
def member(tmp_path, monkeypatch):
    from apps.core import views

    storage = FileSystemStorage(location=str(tmp_path), base_url="/media/")
    # Patched where it is used: the view imported the lazy default storage by name.
    monkeypatch.setattr(views, "default_storage", storage)
    user = User.objects.create_user(email="ada@example.com", username="ada", password=PASSWORD)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, storage


class TestSniffedContentType:
    def test_a_real_image_is_stored_under_the_extension_of_its_own_format(self, member):
        client, storage = member
        # Declared as plain text on purpose: the declaration is not consulted.
        response = upload(client, image_bytes("PNG"), "text/html")
        assert response.status_code == 201, response.data
        assert response.json()["path"].endswith(".png")
        assert len(stored_files(storage)) == 1

    def test_the_format_in_the_bytes_wins_over_the_declaration(self, member):
        client, _ = member
        response = upload(client, image_bytes("JPEG"), "image/png")
        assert response.status_code == 201, response.data
        assert response.json()["path"].endswith(".jpg")

    @pytest.mark.parametrize("fmt,extension", [("PNG", ".png"), ("JPEG", ".jpg"), ("WEBP", ".webp"), ("GIF", ".gif")])
    def test_every_advertised_format_round_trips(self, member, fmt, extension):
        client, _ = member
        response = upload(client, image_bytes(fmt), f"image/{fmt.lower()}")
        assert response.status_code == 201, response.data
        assert response.json()["path"].endswith(extension)

    def test_html_disguised_as_a_png_is_refused_and_never_written(self, member):
        """The original hole: this used to be stored and served from the API's origin."""
        client, storage = member
        body = b"<html><body><script>alert('hi')</script></body></html>"
        response = upload(client, body, "image/png")
        assert response.status_code == 415
        assert "file" in response.data
        assert stored_files(storage) == []

    def test_svg_is_refused_because_it_can_carry_script(self, member):
        client, storage = member
        body = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        assert upload(client, body, "image/svg+xml").status_code == 415
        assert stored_files(storage) == []

    def test_arbitrary_bytes_are_not_an_image(self, member):
        client, _ = member
        assert upload(client, b"\x00\x01\x02MZ\x90\x00 executable-shaped", "image/png").status_code == 415


class TestUploadLimits:
    def test_oversized_files_are_rejected_before_they_are_read(self, member):
        client, _ = member
        big = image_bytes("PNG") + b"\x00" * (4 * 1024 * 1024)
        assert upload(client, big, "image/png").status_code == 413

    def test_an_absent_file_is_a_400_not_a_500(self, member):
        client, _ = member
        assert client.post("/api/uploads/", {}, format="multipart").status_code == 400

    def test_an_unlisted_folder_falls_back_rather_than_writing_wherever(self, member):
        client, storage = member
        response = upload(client, image_bytes("PNG"), "image/png", folder="../../etc/cron.d")
        assert response.status_code == 201, response.data
        assert response.json()["path"].startswith("/media/uploads/")
        assert stored_files(storage) == [response.json()["path"].removeprefix("/media/")]

    def test_signed_out_callers_cannot_upload(self):
        assert upload(APIClient(), image_bytes("PNG"), "image/png").status_code == 401
