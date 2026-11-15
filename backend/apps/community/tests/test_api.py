"""API tests for the community app.

The project-wide URLconf mounts several apps other agents are still writing,
so every request runs against ``apps.community.urls`` in isolation via
``override_settings(ROOT_URLCONF=...)``. Paths are therefore relative to the
``api/community/`` prefix the real config applies.
"""

import base64
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.achievements.models import PointEvent
from apps.community.models import Comment, Engagement, Post, Project, Report
from apps.notifications.models import Notification
from apps.users.models import User

pytestmark = pytest.mark.django_db

# A minimal valid PNG so ImageFields get real file content.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def _isolated_urls(tmp_path):
    """Resolve only apps.community.urls and keep uploaded files out of the repo."""
    with override_settings(ROOT_URLCONF="apps.community.urls", MEDIA_ROOT=tmp_path):
        yield


def make_user(name, role="learner", with_avatar=False, level=3):
    user = User.objects.create_user(
        email=f"{name}@example.com",
        username=name,
        password="Str0ngPass!",
        display_name=name.title(),
        role=role,
    )
    # UserManager auto-provisions the Profile row; we only tune it here.
    profile = user.profile
    profile.level = level
    if with_avatar:
        profile.avatar.save("avatar.png", SimpleUploadedFile("avatar.png", PNG_BYTES, content_type="image/png"))
    profile.save()
    return user


def api(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def make_post(author, **overrides):
    defaults = {
        "user": author,
        "type": "discussion",
        "title": "How do you structure a Django project?",
        "body": "Looking for conventions that scale past one app.",
        "tags": ["django", "architecture"],
        "status": "published",
    }
    defaults.update(overrides)
    return Post.objects.create(**defaults)


def make_project(author, **overrides):
    defaults = {
        "user": author,
        "title": "Study streak tracker",
        "description": "A small PWA that keeps learners honest.",
        "technologies": ["javascript", "pwa"],
        "status": "published",
    }
    defaults.update(overrides)
    return Project.objects.create(**defaults)


def result_ids(payload):
    return [row["id"] for row in payload["results"]]


# ---------------------------------------------------------------- feed rules


def test_anonymous_feed_shows_only_published_posts():
    author = make_user("olivia")
    reader = make_user("robin")
    published = make_post(author)
    draft = make_post(author, title="My private draft", status="draft")
    other_published = make_post(reader, title="Show and tell", type="showcase")

    response = api().get("/posts/")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"count", "next", "previous", "results"}
    assert set(result_ids(body)) == {published.pk, other_published.pk}
    assert draft.pk not in result_ids(body)

    # The author sees their own draft; other authenticated users do not.
    mine = api(author).get("/posts/").json()["results"]
    assert draft.pk in [row["id"] for row in mine]
    theirs = api(reader).get("/posts/").json()["results"]
    assert draft.pk not in [row["id"] for row in theirs]


def test_feed_filters_by_type_tag_search_and_ordering():
    author = make_user("sana")
    question = make_post(author, type="question", title="Async views in DRF?", tags=["django"])
    discussion = make_post(author, type="discussion", title="Remote pairing rituals", tags=["culture"])
    question.likes_count = 9
    question.save(update_fields=["likes_count"])
    discussion.likes_count = 2
    discussion.save(update_fields=["likes_count"])

    by_type = api().get("/posts/", {"type": "question"}).json()
    assert result_ids(by_type) == [question.pk]

    by_tag = api().get("/posts/", {"tag": "culture"}).json()
    assert result_ids(by_tag) == [discussion.pk]

    searched = api().get("/posts/", {"search": "pairing"}).json()
    assert result_ids(searched) == [discussion.pk]

    ordered = api().get("/posts/", {"ordering": "-likes_count"}).json()
    assert result_ids(ordered) == [question.pk, discussion.pk]


# ------------------------------------------------------------------- posting


def test_create_post_requires_auth():
    response = api().post("/posts/", {"title": "Hello world", "body": "First post!", "type": "discussion"})
    assert response.status_code == 401


def test_create_post_validates_title_and_body_length():
    author = make_user("tessa")
    client = api(author)

    short = client.post("/posts/", {"title": "hi", "body": "Too short a title."})
    assert short.status_code == 400
    assert "title" in short.json()

    empty_body = client.post("/posts/", {"title": "Valid title", "body": ""})
    assert empty_body.status_code == 400
    assert "body" in empty_body.json()

    created = client.post(
        "/posts/",
        {"title": "Shipping my first API", "body": "Notes from building the community app.", "type": "experience",
         "tags": ["django"]},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "published"
    assert body["author"]["id"] == author.pk
    assert body["author"]["display_name"] == author.display_name
    assert body["author"]["username"] == author.username
    assert body["author"]["level"] == 3
    assert body["author"]["avatar"] is None


def test_avatar_is_a_full_url_when_available():
    author = make_user("amara", with_avatar=True)
    post = make_post(author)
    body = api().get(f"/posts/{post.pk}/").json()
    avatar = body["author"]["avatar"]
    assert avatar is not None
    assert avatar.startswith("http://testserver/media/")
    assert avatar.endswith("avatar.png")


def test_non_author_cannot_edit_or_delete_someone_elses_post():
    author = make_user("ivy")
    other = make_user("noor")
    post = make_post(author)

    patch = api(other).patch(f"/posts/{post.pk}/", {"title": "Vandalised title"})
    assert patch.status_code == 403
    delete = api(other).delete(f"/posts/{post.pk}/")
    assert delete.status_code == 403
    assert Post.objects.filter(pk=post.pk, title=post.title).exists()

    ok = api(author).patch(f"/posts/{post.pk}/", {"title": "Edited by the author"})
    assert ok.status_code == 200
    assert ok.json()["title"] == "Edited by the author"

    admin = make_user("rooty", role="admin")
    assert api(admin).delete(f"/posts/{post.pk}/").status_code == 204


# ---------------------------------------------------------------- engagement


def test_like_toggle_flips_state_and_keeps_likes_count_consistent():
    author = make_user("maya")
    reader = make_user("chidi")
    post = make_post(author)

    client = api(reader)
    first = client.post(f"/posts/{post.pk}/like/")
    assert first.status_code == 200
    assert first.json() == {"liked": True, "likes_count": 1}

    post.refresh_from_db()
    assert post.likes_count == Engagement.objects.filter(post=post, kind="like").count() == 1

    detail = api(reader).get(f"/posts/{post.pk}/").json()
    assert detail["liked"] is True
    assert api().get(f"/posts/{post.pk}/").json()["liked"] is False

    second = client.post(f"/posts/{post.pk}/like/")
    assert second.json() == {"liked": False, "likes_count": 0}
    assert Engagement.objects.filter(post=post, kind="like").count() == 0

    assert api().post(f"/posts/{post.pk}/like/").status_code == 401


def test_project_like_and_bookmark_toggles_report_counts():
    author = make_user("lena")
    fan = make_user("zoe")
    project = make_project(author)

    liked = api(fan).post(f"/projects/{project.pk}/like/")
    assert liked.json() == {"liked": True, "likes_count": 1}
    marked = api(fan).post(f"/projects/{project.pk}/bookmark/")
    assert marked.json() == {"bookmarked": True, "bookmarks_count": 1}
    project.refresh_from_db()
    assert project.likes_count == 1 and project.bookmarks_count == 1


# ------------------------------------------------------------------- comments


def test_comment_creation_notifies_and_lists_one_level_of_nesting():
    author = make_user("priya")
    reader = make_user("ben")
    post = make_post(author)

    root = api(reader).post(f"/posts/{post.pk}/comments/", {"body": "Use service layers for writes."})
    assert root.status_code == 201
    assert Notification.objects.filter(recipient=author, kind="comment").exists()

    reply = api(author).post(
        f"/posts/{post.pk}/comments/", {"body": "Agreed, thanks!", "parent": root.json()["id"]}
    )
    assert reply.status_code == 201
    assert Notification.objects.filter(recipient=reader, kind="reply").exists()

    post.refresh_from_db()
    assert post.comments_count == 2

    listed = api().get(f"/posts/{post.pk}/comments/").json()
    assert result_ids(listed) == [root.json()["id"]]
    assert [r["id"] for r in listed["results"][0]["replies"]] == [reply.json()["id"]]
    assert listed["results"][0]["replies"][0]["replies"] == []

    assert api().post(f"/posts/{post.pk}/comments/", {"body": "sneaky"}).status_code == 401


def test_comment_delete_is_author_or_admin_and_recounts_post():
    author = make_user("quey")
    reader = make_user("tom")
    post = make_post(author)
    comment = Comment.objects.create(post=post, user=reader, body="An aside.")
    post.comments_count = 1
    post.save(update_fields=["comments_count"])

    assert api(author).delete(f"/comments/{comment.pk}/").status_code == 403

    deleted = api(reader).delete(f"/comments/{comment.pk}/")
    assert deleted.status_code == 204
    post.refresh_from_db()
    assert post.comments_count == 0

    admin = make_user("mod", role="admin")
    second = Comment.objects.create(post=post, user=reader, body="Spam-ish.")
    assert api(admin).delete(f"/comments/{second.pk}/").status_code == 204


# -------------------------------------------------------------------- helpful


def test_helpful_is_restricted_to_post_author_or_admin():
    author = make_user("ade")
    answerer = make_user("kim")
    stranger = make_user("leo")
    question = make_post(author, type="question", title="Which ORM query is faster?")
    answer = Comment.objects.create(post=question, user=answerer, body="Filter before annotate.")
    admin = make_user("boss", role="admin")

    denied = api(stranger).post(f"/posts/{question.pk}/helpful/", {"comment_id": answer.pk})
    assert denied.status_code == 403
    assert api().post(f"/posts/{question.pk}/helpful/", {"comment_id": answer.pk}).status_code == 401

    accepted = api(author).post(f"/posts/{question.pk}/helpful/", {"comment_id": answer.pk})
    assert accepted.status_code == 200
    assert accepted.json()["is_solved"] is True
    assert accepted.json()["helpful_comment"] == answer.pk
    assert Notification.objects.filter(recipient=answerer, kind="comment").exists()

    # An admin may also mark an answer helpful.
    assert api(admin).post(f"/posts/{question.pk}/helpful/", {"comment_id": answer.pk}).status_code == 200

    # A comment from a different post is rejected by the service.
    other_post = make_post(stranger, title="Totally unrelated thread")
    other_comment = Comment.objects.create(post=other_post, user=answerer, body="Wrong thread.")
    bad = api(author).post(f"/posts/{question.pk}/helpful/", {"comment_id": other_comment.pk})
    assert bad.status_code == 400


# -------------------------------------------------------------------- reports


def test_duplicate_report_returns_the_existing_row():
    author = make_user("nia")
    reporter = make_user("sam")
    post = make_post(author)

    first = api(reporter).post(f"/posts/{post.pk}/report/", {"reason": "spam", "details": "Ads again."})
    assert first.status_code == 201
    report_id = first.json()["id"]
    assert Report.objects.filter(created_by=reporter, post=post).count() == 1

    second = api(reporter).post(f"/posts/{post.pk}/report/", {"reason": "spam", "details": "Ads again."})
    assert second.status_code == 200
    assert second.json()["id"] == report_id

    bad_reason = api(reporter).post(f"/posts/{post.pk}/report/", {"reason": "rude"})
    assert bad_reason.status_code == 400
    assert "reason" in bad_reason.json()

    project = make_project(author)
    on_project = api(reporter).post(f"/projects/{project.pk}/report/", {"reason": "plagiarism"})
    assert on_project.status_code == 201


# ------------------------------------------------------------------ bookmarks


def test_my_bookmarks_only_returns_the_requesters_bookmarks():
    author = make_user("dana")
    first = make_user("erin")
    second = make_user("fay")
    post_mine = make_post(author, title="A thread I saved")
    post_theirs = make_post(author, title="A thread they saved")
    project = make_project(author, title="A project I saved")

    assert api(first).post(f"/posts/{post_mine.pk}/bookmark/").json()["bookmarked"] is True
    assert api(second).post(f"/posts/{post_theirs.pk}/bookmark/").json()["bookmarked"] is True
    assert api(first).post(f"/projects/{project.pk}/bookmark/").json()["bookmarked"] is True

    body = api(first).get("/me/bookmarks/").json()
    assert set(body) == {"posts", "projects"}
    assert [row["id"] for row in body["posts"]] == [post_mine.pk]
    assert [row["id"] for row in body["projects"]] == [project.pk]

    other = api(second).get("/me/bookmarks/").json()
    assert [row["id"] for row in other["posts"]] == [post_theirs.pk]
    assert other["projects"] == []

    assert api().get("/me/bookmarks/").status_code == 401


# ------------------------------------------------------------------- projects


def test_project_ordering_by_trending_follows_the_stored_score():
    author = make_user("gina")
    low = make_project(author, title="Low buzz", trending_score=0.5)
    high = make_project(author, title="High buzz", trending_score=9.25)
    mid = make_project(author, title="Mid buzz", trending_score=4.0)

    trending = api().get("/projects/", {"ordering": "trending"}).json()
    assert result_ids(trending) == [high.pk, mid.pk, low.pk]

    default = api().get("/projects/").json()
    assert result_ids(default) == [high.pk, mid.pk, low.pk]

    liked = make_project(author, title="Beloved", likes_count=42, trending_score=0.1)
    most_liked = api().get("/projects/", {"ordering": "most_liked"}).json()
    assert result_ids(most_liked)[0] == liked.pk

    # Push the newest row clearly ahead in time so ?ordering=recent is deterministic.
    Project.objects.filter(pk=liked.pk).update(created_at=timezone.now() + timedelta(days=1))
    recent = api().get("/projects/", {"ordering": "recent"}).json()
    assert result_ids(recent)[0] == liked.pk

    by_tech = api().get("/projects/", {"technology": "javascript"}).json()
    assert set(result_ids(by_tech)) == {low.pk, high.pk, mid.pk, liked.pk}

    hidden = make_project(author, title="Not ready", status="draft")
    anon_ids = result_ids(api().get("/projects/").json())
    assert hidden.pk not in anon_ids
    assert hidden.pk in result_ids(api(author).get("/projects/").json())


def test_project_create_awards_publish_xp_exactly_once():
    author = make_user("hana")
    client = api(author)

    draft = client.post(
        "/projects/",
        {"title": "Habit garden", "description": "Tracks study habits.", "technologies": ["python"],
         "status": "draft"},
    )
    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"
    assert PointEvent.objects.filter(user=author, reason="project_publish").count() == 0

    published = client.patch(f"/projects/{draft.json()['id']}/", {"status": "published"})
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert PointEvent.objects.filter(user=author, reason="project_publish").count() == 1

    # Re-publishing (no status change) never awards XP again.
    client.patch(f"/projects/{draft.json()['id']}/", {"title": "Habit garden v2"})
    client.patch(f"/projects/{draft.json()['id']}/", {"status": "published"})
    assert PointEvent.objects.filter(user=author, reason="project_publish").count() == 1


def test_project_publish_via_create_and_screenshot_upload():
    author = make_user("iris")
    screenshot = SimpleUploadedFile("shot.png", PNG_BYTES, content_type="image/png")
    response = api(author).post(
        "/projects/",
        {
            "title": "Flashcard finder",
            "description": "Spaced repetition for community answers.",
            "technologies": ["javascript", "pwa"],
            "repo_url": "https://example.com/repo",
            "status": "published",
            "screenshot": screenshot,
        },
        format="multipart",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "published"
    assert body["technologies"] == ["javascript", "pwa"]
    assert body["screenshot"] is not None
    assert body["screenshot"].startswith("http://testserver/media/")
    assert PointEvent.objects.filter(user=author, reason="project_publish").count() == 1


def test_project_view_endpoint_counts_traffic():
    author = make_user("june")
    project = make_project(author)

    first = api().post(f"/projects/{project.pk}/view/")
    assert first.status_code == 200
    assert first.json()["views_count"] == 1
    second = api().post(f"/projects/{project.pk}/view/")
    assert second.json()["views_count"] == 2

    project.refresh_from_db()
    assert project.views_count == 2
