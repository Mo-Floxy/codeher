"""Mentorship API tests.

The sibling apps' `urls.py` modules are being written in parallel, so this module
doubles as a minimal URLconf that mounts only mentorship under `/api/` (see the
`api` fixture). Every scenario is built from real rows: nothing here pretends a
mentor is approved or a seat is free.
"""

from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test import RequestFactory
from django.urls import include, path
from django.utils import timezone
from rest_framework.test import APIClient

from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession
from apps.mentorship.serializers import MentorshipSessionSerializer
from apps.notifications.models import Notification
from apps.users.models import Profile, User

pytestmark = pytest.mark.django_db

# This module is used as settings.ROOT_URLCONF by the `api` fixture below.
urlpatterns = [path("api/mentorship/", include("apps.mentorship.urls"))]

MENTORS = "/api/mentorship/mentors/"
MENTOR_ME = "/api/mentorship/mentors/me/"
REQUESTS = "/api/mentorship/requests/"
INCOMING = "/api/mentorship/requests/incoming/"
SESSIONS = "/api/mentorship/sessions/"

FUTURE = timezone.now() + timedelta(days=2)
PAST = timezone.now() - timedelta(days=2)


@pytest.fixture
def api(settings):
    """Unsigned client bound to the mentorship-only URLconf."""
    settings.ROOT_URLCONF = __name__
    return APIClient()


def png_file(name="avatar.png"):
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=name)


def make_user(username, role="learner", headline=""):
    user = User.objects.create_user(
        email=f"{username}@codeher.test",
        username=username,
        display_name=username.replace("_", " ").title(),
        role=role,
    )
    # users.UserManager creates the Profile row; award_xp() and the user brief both need it.
    if headline:
        profile = user.profile
        profile.headline = headline
        profile.save(update_fields=["headline", "updated_at"])
    return user


def make_mentor(username, *, is_approved=True, expertise=None, capacity=3, headline="", **mentor_fields):
    user = make_user(username, role="mentor", headline=headline)
    mentor_fields.setdefault("bio", "Ships features and mentors learners.")
    return MentorProfile.objects.create(
        user=user,
        expertise=expertise if expertise is not None else ["Django", "React"],
        is_approved=is_approved,
        capacity=capacity,
        **mentor_fields,
    )


def make_request(learner, mentor_user, status=MentorshipRequest.STATUS_PENDING, **kwargs):
    kwargs.setdefault("goal", "Finish the React path")
    kwargs.setdefault("message", "Hi! I would like your feedback on my portfolio.")
    return MentorshipRequest.objects.create(learner=learner, mentor=mentor_user, status=status, **kwargs)


def make_session(request, mentor_user, learner, starts_at, **kwargs):
    return MentorshipSession.objects.create(
        request=request, mentor=mentor_user, learner=learner, starts_at=starts_at, **kwargs
    )


def as_request(user):
    """A plain request carrying `user`, for serializer-level visibility checks."""
    request = RequestFactory().get("/")
    request.user = user
    return request


def results(response):
    assert response["Content-Type"].startswith("application/json"), response.content
    return response.json()["results"]


def accepted_pair():
    """An accepted request plus its mentor and learner."""
    mentor = make_mentor("ada")
    learner = make_user("learner")
    request = make_request(learner, mentor.user, status=MentorshipRequest.STATUS_ACCEPTED)
    return mentor, learner, request


# --------------------------------------------------------------------- directory
def test_directory_lists_only_approved_mentors_without_auth(api):
    approved = make_mentor("ada")
    hidden = make_mentor("grace", is_approved=False)

    response = api.get(MENTORS)

    assert response.status_code == 200, response.content
    ids = {row["id"] for row in results(response)}
    assert ids == {approved.user_id}
    assert hidden.user_id not in ids


def test_directory_row_shape(api):
    mentor = make_mentor("linus", headline="Staff engineer", languages=["en"], availability_note="Saturdays")

    row = results(api.get(MENTORS))[0]

    assert set(row) == {
        "id",
        "user",
        "expertise",
        "current_role",
        "company",
        "years_experience",
        "bio",
        "availability_note",
        "languages",
        "capacity",
        "active_mentees",
        "has_capacity",
        "is_accepting",
        "matched_count",
        "rating_average",
    }
    assert set(row["user"]) == {"id", "display_name", "username", "avatar", "headline"}
    assert row["id"] == mentor.user_id  # the id used by the detail route and by POST `mentor`
    assert row["user"]["headline"] == "Staff engineer"
    assert row["user"]["avatar"] is None
    assert row["expertise"] == ["Django", "React"]
    assert row["languages"] == ["en"]
    assert row["availability_note"] == "Saturdays"
    assert row["has_capacity"] is True
    assert row["active_mentees"] == 0
    assert row["rating_average"] is None


def test_directory_avatar_is_an_absolute_url(api, settings, tmp_path):
    mentor = make_mentor("linus")
    settings.MEDIA_ROOT = str(tmp_path)
    mentor.user.profile.avatar.save("avatar.png", png_file(), save=True)

    row = results(api.get(MENTORS))[0]

    assert row["user"]["avatar"].startswith("http://testserver/media/avatars/avatar")


def test_directory_filters_expertise_search_and_accepting(api):
    pythonista = make_mentor("guido", expertise=["Python"], is_accepting=False)
    frontender = make_mentor("katie", expertise=["React", "CSS"], bio="CSS wizard and conference speaker.")

    def ids(**query):
        return [row["id"] for row in results(api.get(MENTORS, query))]

    assert ids(expertise="python") == [pythonista.user_id]
    assert ids(expertise="PYTHON") == [pythonista.user_id]  # case-insensitive JSON text match
    assert ids(search="css wizard") == [frontender.user_id]
    assert ids(search="guido") == [pythonista.user_id]
    assert ids(accepting="true") == [frontender.user_id]
    assert ids(accepting="false") == [pythonista.user_id]


def test_directory_capacity_uses_real_request_counts(api):
    mentor = make_mentor("margaret", capacity=2)
    for index in range(2):
        learner = make_user(f"learner{index}")
        make_request(learner, mentor.user, status=MentorshipRequest.STATUS_ACCEPTED)

    row = results(api.get(MENTORS))[0]

    assert row["active_mentees"] == 2
    assert row["has_capacity"] is False


def test_mentor_detail_by_user_id(api):
    mentor = make_mentor("radia", preferred_slots=["Weekday evenings"])

    response = api.get(f"{MENTORS}{mentor.user_id}/")

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["preferred_slots"] == ["Weekday evenings"]
    assert body["availability"] == ["Weekday evenings"]
    assert body["user"]["id"] == mentor.user_id


def test_mentor_detail_hides_unapproved_profiles(api):
    unapproved = make_mentor("grace", is_approved=False)
    plain = make_user("plain")

    assert api.get(f"{MENTORS}{unapproved.user_id}/").status_code == 404
    assert api.get(f"{MENTORS}{plain.pk}/").status_code == 404

    api.force_authenticate(user=make_user("boss", role="admin"))
    assert api.get(f"{MENTORS}{unapproved.user_id}/").status_code == 200


# ------------------------------------------------------------------- mentors/me
def test_learner_forbidden_on_mentors_me_and_incoming(api):
    learner = make_user("learner")
    api.force_authenticate(user=learner)

    assert api.get(MENTOR_ME).status_code == 403
    assert api.patch(MENTOR_ME, {"expertise": ["Everything"]}, format="json").status_code == 403
    assert not MentorProfile.objects.filter(user=learner).exists()

    incoming = api.get(INCOMING)
    assert incoming.status_code == 403
    assert incoming.json()["detail"] == "Mentor access is required."


def test_anonymous_cannot_reach_mentors_me_or_my_requests(api):
    assert api.get(MENTOR_ME).status_code == 401
    assert api.get(REQUESTS).status_code == 401
    assert api.get(SESSIONS).status_code == 401
    assert api.post(REQUESTS, {"mentor": 1, "goal": "G", "message": "M"}, format="json").status_code == 401


def test_mentors_me_created_on_demand_and_admin_fields_are_not_writable(api):
    mentor_user = make_user("ada", role="mentor")
    stranger = make_user("stranger")
    api.force_authenticate(user=mentor_user)

    created = api.get(MENTOR_ME)
    assert created.status_code == 200, created.content
    assert created.json()["is_approved"] is False

    response = api.patch(
        MENTOR_ME,
        {
            "expertise": ["Django", "PostgreSQL"],
            "bio": "Ten years of production Python.",
            "availability_note": "Tuesday evenings",
            "preferred_slots": [{"weekday": "tuesday", "time": "18:00"}],
            "capacity": 4,
            "years_experience": 10,
            "current_role": "Backend engineer",
            "company": "Northwind",
            "linkedin_url": "https://linkedin.com/in/ada",
            "languages": ["en", "ha"],
            "is_accepting": False,
            # admin-controlled or structural: ignored, never written (§9)
            "is_approved": True,
            "matched_count": 99,
            "rating_average": "5.00",
            "id": stranger.pk,
            "user": stranger.pk,
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    profile = MentorProfile.objects.get(user=mentor_user)
    assert profile.expertise == ["Django", "PostgreSQL"]
    assert profile.capacity == 4
    assert profile.years_experience == 10
    assert profile.is_accepting is False
    assert profile.bio == "Ten years of production Python."
    assert profile.linkedin_url == "https://linkedin.com/in/ada"
    assert response.json()["preferred_slots"] == [{"weekday": "tuesday", "time": "18:00"}]
    assert response.json()["id"] == mentor_user.pk
    assert profile.is_approved is False
    assert profile.matched_count == 0
    assert profile.rating_average is None
    # the record still belongs to the requester
    assert MentorProfile.objects.count() == 1
    assert profile.user_id == mentor_user.pk


def test_a_bad_write_is_rejected_on_mentors_me(api):
    mentor_user = make_user("ada", role="mentor")
    api.force_authenticate(user=mentor_user)

    response = api.patch(MENTOR_ME, {"capacity": 0, "expertise": "Django"}, format="json")

    assert response.status_code == 400, response.content
    assert set(response.json()) >= {"capacity", "expertise"}


def test_directory_records_are_read_only(api):
    mentor = make_mentor("ada")
    api.force_authenticate(user=make_user("stranger"))

    assert api.patch(f"{MENTORS}{mentor.user_id}/", {"is_approved": False}, format="json").status_code == 405
    assert MentorProfile.objects.get(pk=mentor.pk).is_approved is True


# --------------------------------------------------------------------- requests
def test_learner_creates_request_and_mentor_is_notified(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    api.force_authenticate(user=learner)

    response = api.post(
        REQUESTS,
        {
            "mentor": mentor.user_id,
            "goal": "Ship my first portfolio",
            "message": "I am two modules from the end of the frontend path.",
            "preferred_slots": [{"weekday": "monday", "time": "19:00"}],
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == "pending"
    assert body["learner"]["id"] == learner.pk
    assert body["mentor"]["id"] == mentor.user_id
    assert body["preferred_slots"] == [{"weekday": "monday", "time": "19:00"}]

    created = MentorshipRequest.objects.get(pk=body["id"])
    assert created.preferred_slots == [{"weekday": "monday", "time": "19:00"}]
    assert Notification.objects.filter(recipient=mentor.user, kind="mentorship_update").exists()

    assert [row["id"] for row in results(api.get(REQUESTS))] == [created.pk]
    assert api.get(REQUESTS, {"status": "accepted"}).json()["count"] == 0


def test_learner_must_fill_the_request_fields(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    api.force_authenticate(user=learner)

    response = api.post(REQUESTS, {"mentor": mentor.user_id, "goal": "  ", "preferred_slots": "monday"}, format="json")

    assert response.status_code == 400, response.content
    errors = response.json()
    assert "message" in errors and "goal" in errors and "preferred_slots" in errors
    assert not MentorshipRequest.objects.exists()


def test_second_live_request_to_the_same_mentor_is_rejected(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    api.force_authenticate(user=learner)
    payload = {"mentor": mentor.user_id, "goal": "Goal", "message": "Message", "preferred_slots": []}

    assert api.post(REQUESTS, payload, format="json").status_code == 201
    conflict = api.post(REQUESTS, {**payload, "goal": "A different goal"}, format="json")
    assert conflict.status_code == 409, conflict.content
    assert "already have an open request" in conflict.json()["detail"]
    assert MentorshipRequest.objects.filter(learner=learner, mentor=mentor.user).count() == 1

    # once the live row closes, the pair can ask again
    open_request = MentorshipRequest.objects.get()
    assert api.post(f"{REQUESTS}{open_request.pk}/cancel/", {}, format="json").status_code == 200
    assert api.post(REQUESTS, payload, format="json").status_code == 201


def test_requests_are_refused_for_unapproved_self_or_full_mentors(api):
    pending_mentor = make_mentor("grace", is_approved=False)
    full_mentor = make_mentor("margaret", capacity=1)
    learner = make_user("learner")
    outsider = make_user("other")
    api.force_authenticate(user=learner)

    unapproved = api.post(REQUESTS, {"mentor": pending_mentor.user_id, "goal": "G", "message": "M"}, format="json")
    assert unapproved.status_code == 409
    assert "not available on CodeHer" in unapproved.json()["detail"]

    self_request = api.post(REQUESTS, {"mentor": learner.pk, "goal": "G", "message": "M"}, format="json")
    assert self_request.status_code == 409

    missing = api.post(REQUESTS, {"mentor": 424242, "goal": "G", "message": "M"}, format="json")
    assert missing.status_code == 400
    assert "mentor" in missing.json()

    make_request(outsider, full_mentor.user, status=MentorshipRequest.STATUS_ACCEPTED)
    assert MentorProfile.objects.get(pk=full_mentor.pk).has_capacity is False
    capped = api.post(REQUESTS, {"mentor": full_mentor.user_id, "goal": "G", "message": "M"}, format="json")
    assert capped.status_code == 409, capped.content
    assert "capacity" in capped.json()["detail"]
    assert MentorshipRequest.objects.filter(learner=learner).count() == 0


def test_a_mentor_not_accepting_new_mentees_is_refused(api):
    mentor = make_mentor("ada", is_accepting=False)
    api.force_authenticate(user=make_user("learner"))

    response = api.post(REQUESTS, {"mentor": mentor.user_id, "goal": "G", "message": "M"}, format="json")

    assert response.status_code == 409
    assert "not accepting new mentees" in response.json()["detail"]


def test_incoming_inbox_lists_only_the_mentors_own_requests(api):
    mentor = make_mentor("ada")
    other = make_mentor("radia")
    learner = make_user("learner")
    mine = make_request(learner, mentor.user)
    make_request(learner, other.user)
    api.force_authenticate(user=mentor.user)

    rows = results(api.get(INCOMING))

    assert [row["id"] for row in rows] == [mine.pk]
    assert rows[0]["mentor"]["id"] == mentor.user_id
    assert rows[0]["learner"]["id"] == learner.pk

    api.force_authenticate(user=other.user)
    assert [row["id"] for row in results(api.get(INCOMING))] != [mine.pk]


def test_request_detail_is_visible_to_the_pair_only(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    stranger = make_user("stranger")
    request = make_request(learner, mentor.user)

    for participant in (learner, mentor.user, make_user("boss", role="admin")):
        api.force_authenticate(user=participant)
        assert api.get(f"{REQUESTS}{request.pk}/").status_code == 200

    api.force_authenticate(user=stranger)
    assert api.get(f"{REQUESTS}{request.pk}/").status_code == 404


def test_learner_cannot_accept_their_own_request_and_a_wrong_mentor_cannot_either(api):
    mentor = make_mentor("ada")
    imposter = make_mentor("radia")
    learner = make_user("learner")
    stranger = make_user("stranger")
    request = make_request(learner, mentor.user)

    api.force_authenticate(user=learner)
    response = api.post(f"{REQUESTS}{request.pk}/accept/", {"note": "Sure!"}, format="json")
    assert response.status_code == 403, response.content
    assert response.json()["detail"] == "Only the assigned mentor can act on this request."

    api.force_authenticate(user=imposter.user)
    assert api.post(f"{REQUESTS}{request.pk}/accept/", {}, format="json").status_code == 403

    # any member outside the pair is refused by the service, and nothing is written
    api.force_authenticate(user=stranger)
    assert api.post(f"{REQUESTS}{request.pk}/accept/", {}, format="json").status_code == 403

    request.refresh_from_db()
    assert request.status == MentorshipRequest.STATUS_PENDING


def test_accept_transitions_status_counts_the_match_and_notifies_the_learner(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    request = make_request(learner, mentor.user)
    api.force_authenticate(user=mentor.user)

    response = api.post(f"{REQUESTS}{request.pk}/accept/", {"note": "Let us start Monday."}, format="json")

    assert response.status_code == 200, response.content
    assert response.json()["status"] == "accepted"

    request.refresh_from_db()
    assert request.status == MentorshipRequest.STATUS_ACCEPTED
    assert request.mentor_note == "Let us start Monday."
    assert request.responded_at is not None
    assert MentorProfile.objects.get(pk=mentor.pk).matched_count == 1

    notice = Notification.objects.filter(recipient=learner, kind="mentorship_update").first()
    assert notice is not None
    assert "accepted" in notice.title
    assert notice.body == "Let us start Monday."

    assert Profile.objects.get(user=mentor.user).total_xp > 0  # mentor_match XP, awarded by services

    again = api.post(f"{REQUESTS}{request.pk}/accept/", {"note": "again"}, format="json")
    assert again.status_code == 409


def test_decline_and_cancel_close_a_request(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    request = make_request(learner, mentor.user)
    api.force_authenticate(user=mentor.user)

    declined = api.post(f"{REQUESTS}{request.pk}/decline/", {"reason": "My calendar is full."}, format="json")
    assert declined.status_code == 200, declined.content
    request.refresh_from_db()
    assert request.status == MentorshipRequest.STATUS_DECLINED
    assert request.declined_reason == "My calendar is full."
    assert Notification.objects.filter(recipient=learner, title__contains="declined").exists()

    second = make_request(learner, mentor.user)  # closed history does not block a new live row
    api.force_authenticate(user=learner)
    cancelled = api.post(f"{REQUESTS}{second.pk}/cancel/", {}, format="json")
    assert cancelled.status_code == 200, cancelled.content
    second.refresh_from_db()
    assert second.status == MentorshipRequest.STATUS_CANCELLED

    # cancelling belongs to the learner; services raises PermissionError for the mentor
    third = make_request(learner, mentor.user)
    api.force_authenticate(user=mentor.user)
    assert api.post(f"{REQUESTS}{third.pk}/cancel/", {}, format="json").status_code == 403


def test_complete_closes_an_accepted_mentorship(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    request = make_request(learner, mentor.user, status=MentorshipRequest.STATUS_ACCEPTED)
    api.force_authenticate(user=mentor.user)

    response = api.post(f"{REQUESTS}{request.pk}/complete/", {}, format="json")

    assert response.status_code == 200, response.content
    request.refresh_from_db()
    assert request.status == MentorshipRequest.STATUS_COMPLETED
    assert api.post(f"{REQUESTS}{request.pk}/complete/", {}, format="json").status_code == 409


def test_unknown_request_action_is_a_404(api):
    mentor = make_mentor("ada")
    learner = make_user("learner")
    request = make_request(learner, mentor.user)
    api.force_authenticate(user=mentor.user)

    assert api.post(f"{REQUESTS}{request.pk}/approve/", {}, format="json").status_code == 404


# --------------------------------------------------------------------- sessions
def test_sessions_list_covers_both_roles_and_scopes(api):
    mentor, learner, request = accepted_pair()
    past = make_session(request, mentor.user, learner, PAST, agenda="Retro")
    upcoming = make_session(request, mentor.user, learner, FUTURE, agenda="Roadmap")

    api.force_authenticate(user=mentor.user)
    assert {row["id"] for row in results(api.get(SESSIONS))} == {past.id, upcoming.id}
    assert {row["id"] for row in results(api.get(SESSIONS, {"scope": "upcoming"}))} == {upcoming.id}
    assert {row["id"] for row in results(api.get(SESSIONS, {"scope": "past"}))} == {past.id}

    api.force_authenticate(user=learner)
    assert {row["id"] for row in results(api.get(SESSIONS))} == {past.id, upcoming.id}

    api.force_authenticate(user=make_user("stranger"))
    assert results(api.get(SESSIONS)) == []


def test_mentor_schedules_a_session_and_the_link_stays_private(api):
    mentor, learner, request = accepted_pair()
    stranger = make_user("stranger")
    api.force_authenticate(user=mentor.user)

    response = api.post(
        SESSIONS,
        {
            "request": request.pk,
            "starts_at": FUTURE.isoformat(),
            "duration_minutes": 30,
            "agenda": "Portfolio review",
            "meeting_url": "https://meet.example.test/room-42",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["meeting_url"] == "https://meet.example.test/room-42"
    assert body["mentor"]["id"] == mentor.user_id
    assert body["request"]["id"] == request.pk
    assert body["request"]["learner"]["id"] == learner.pk
    assert body["is_upcoming"] is True
    assert body["ends_at"] > body["starts_at"]

    session = MentorshipSession.objects.get(pk=body["id"])
    assert request.sessions.filter(pk=session.pk).exists()
    assert Notification.objects.filter(recipient=learner, kind="session_reminder").exists()

    api.force_authenticate(user=learner)
    learner_view = api.get(f"{SESSIONS}{session.id}/").json()
    assert learner_view["meeting_url"] == "https://meet.example.test/room-42"
    assert learner_view["notes"] is None  # the mentor's private notes stay private

    # an unrelated member never sees another pair's meeting link, list or detail
    api.force_authenticate(user=stranger)
    assert api.get(f"{SESSIONS}{session.id}/").status_code == 404
    assert results(api.get(SESSIONS)) == []
    assert api.get(f"{REQUESTS}{request.pk}/").status_code == 404
    payload = MentorshipSessionSerializer(session, context={"request": as_request(stranger)}).data
    assert payload["meeting_url"] is None
    assert payload["notes"] is None


def test_scheduling_requires_an_accepted_request_and_the_right_mentor(api):
    mentor, learner, request = accepted_pair()
    other_learner = make_user("learner2")
    pending = make_request(other_learner, mentor.user)
    outsider_mentor = make_mentor("radia")
    body = {"request": request.pk, "starts_at": FUTURE.isoformat(), "duration_minutes": 30}
    api.force_authenticate(user=mentor.user)

    too_early = api.post(SESSIONS, {**body, "starts_at": PAST.isoformat()}, format="json")
    assert too_early.status_code == 400, too_early.content
    assert "future" in too_early.json()["detail"]

    not_accepted = api.post(SESSIONS, {**body, "request": pending.pk}, format="json")
    assert not_accepted.status_code == 409
    assert "Accept the request" in not_accepted.json()["detail"]

    bad_duration = api.post(SESSIONS, {**body, "duration_minutes": 900}, format="json")
    assert bad_duration.status_code == 400
    assert "duration_minutes" in bad_duration.json()

    api.force_authenticate(user=outsider_mentor.user)
    assert api.post(SESSIONS, body, format="json").status_code == 403

    api.force_authenticate(user=learner)
    assert api.post(SESSIONS, body, format="json").status_code == 403
    assert MentorshipSession.objects.count() == 0


def test_session_patch_is_mentor_only(api):
    mentor, learner, request = accepted_pair()
    session = make_session(request, mentor.user, learner, FUTURE, agenda="Roadmap", meeting_url="https://meet.test/a")

    api.force_authenticate(user=learner)
    denied = api.patch(f"{SESSIONS}{session.id}/", {"agenda": "Mine now"}, format="json")
    assert denied.status_code == 403, denied.content
    assert denied.json()["detail"] == "Only the mentor on a session can change its details."
    session.refresh_from_db()
    assert session.agenda == "Roadmap"

    api.force_authenticate(user=mentor.user)
    updated = api.patch(
        f"{SESSIONS}{session.id}/",
        {"agenda": "Roadmap + hiring loop", "notes": "Bring the three projects.", "status": "completed"},
        format="json",
    )
    assert updated.status_code == 200, updated.content
    assert updated.json()["meeting_url"] == "https://meet.test/a"
    session.refresh_from_db()
    assert session.agenda == "Roadmap + hiring loop"
    assert session.status == "completed"
    assert session.learner_attended is None
    assert Notification.objects.filter(recipient=learner, title__contains="complete").exists()

    assert api.delete(f"{SESSIONS}{session.id}/").status_code == 204
    session.refresh_from_db()
    assert session.status == "cancelled"


def test_learner_confirms_their_own_attendance_after_the_session(api):
    mentor, learner, request = accepted_pair()
    upcoming = make_session(request, mentor.user, learner, FUTURE)
    finished = make_session(request, mentor.user, learner, PAST)
    api.force_authenticate(user=learner)

    too_early = api.post(f"{SESSIONS}{upcoming.id}/attendance/", {"attended": True}, format="json")
    assert too_early.status_code == 409, too_early.content
    upcoming.refresh_from_db()
    assert upcoming.learner_attended is None

    recorded = api.post(f"{SESSIONS}{finished.id}/attendance/", {"attended": True}, format="json")
    assert recorded.status_code == 200, recorded.content
    assert recorded.json()["attended"] is True
    finished.refresh_from_db()
    assert finished.learner_attended is True

    api.force_authenticate(user=make_user("stranger"))
    assert api.post(f"{SESSIONS}{finished.id}/attendance/", {"attended": True}, format="json").status_code == 404

    api.force_authenticate(user=mentor.user)
    assert api.post(f"{SESSIONS}{finished.id}/attendance/", {"attended": False}, format="json").status_code == 200
    finished.refresh_from_db()
    assert finished.learner_attended is False

    assert api.post(f"{SESSIONS}{finished.id}/attendance/", {"attended": "maybe"}, format="json").status_code == 400
