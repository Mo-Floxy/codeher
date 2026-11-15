"""API tests for the gamification surface.

Everything asserted here is derived from stored rows (`PointEvent`, `Submission`,
`ActivityLog`), which is the point of the service layer.
"""

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.achievements import services
from apps.achievements.models import Achievement, UserAchievement
from apps.challenges.models import Challenge, Submission
from apps.users.models import Profile, User

pytestmark = pytest.mark.django_db


def make_member(username, email, display_name):
    user = User.objects.create_user(
        email=email, username=username, password="badge-test-pass-1", display_name=display_name
    )
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def member(db):
    return make_member("badge_hunter", "badge@codeher.test", "Badge Hunter")


@pytest.fixture
def peer(db):
    return make_member("peer", "peer@codeher.test", "Peer Member")


@pytest.fixture
def api_client(member):
    client = APIClient()
    client.force_authenticate(user=member)
    return client


@pytest.fixture
def badge(db):
    return Achievement.objects.create(
        code="first-solve",
        title="First Solve",
        description="Solve your first challenge.",
        metric="challenges_solved",
        requirement_value=1,
        category="challenges",
        xp_reward=50,
    )


def solved_challenge(member, title="Flip the switch"):
    challenge = Challenge.objects.create(title=title, description="d", points=20)
    return Submission.objects.create(
        user=member, challenge=challenge, language="javascript", code="return 1;", passed=True, score=100, total_tests=1, passed_count=1
    )


# ------------------------------------------------------------------- catalogue


def test_catalogue_requires_authentication():
    client = APIClient()
    assert client.get("/api/achievements/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/achievements/me/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/achievements/leaderboard/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/achievements/me/goals/").status_code == status.HTTP_401_UNAUTHORIZED


def test_catalogue_reports_progress_without_a_badge(api_client, badge):
    response = api_client.get("/api/achievements/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    row = response.data["results"][0]
    assert row["code"] == "first-solve"
    assert row["is_earned"] is False
    assert row["current_value"] == 0
    assert row["progress_percent"] == 0
    assert row["earned_at"] is None
    assert row["requirement"] == "1 challenges solved"


def test_is_earned_flips_once_real_activity_lands(api_client, member, badge):
    before = api_client.get("/api/achievements/").data["results"][0]
    assert before["is_earned"] is False

    solved_challenge(member)
    services.evaluate_achievements(member)

    after = api_client.get("/api/achievements/").data["results"][0]
    assert after["is_earned"] is True
    assert after["current_value"] == 1
    assert after["progress_percent"] == 100
    assert after["earned_at"] is not None
    assert UserAchievement.objects.filter(user=member, achievement=badge).count() == 1

    me = api_client.get("/api/achievements/me/").data
    assert me["earned_count"] == 1
    assert me["earned"][0]["badge"] == "first-solve"
    assert me["xp"]["total"] == 50  # the badge's own XP reward
    assert me["metrics"]["challenges_solved"] == 1


def test_catalogue_filters_and_pagination(api_client, badge, db):
    for index in range(12):
        Achievement.objects.create(
            code="badge-{}".format(index),
            title="Badge {}".format(index),
            description="d",
            metric="lessons_completed",
            requirement_value=index + 2,
            category="learning" if index % 2 == 0 else "consistency",
        )
    assert api_client.get("/api/achievements/", {"page_size": 5}).data["count"] == 13
    response = api_client.get("/api/achievements/", {"category": "challenges"})
    assert [row["code"] for row in response.data["results"]] == ["first-solve"]
    assert api_client.get("/api/achievements/", {"search": "First"}).data["count"] == 1
    assert api_client.get("/api/achievements/", {"ordering": "-requirement_value"}).data["results"][0]["code"] == "badge-11"


# ------------------------------------------------------------------ weekly goal


def test_goal_progress_comes_from_activity_logs(api_client, member, badge):
    response = api_client.get("/api/achievements/me/goals/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["target_minutes"] == 90
    assert response.data["weekly_goal_minutes"] == 90
    assert response.data["actual_minutes"] == 0
    assert response.data["achieved"] is False

    services.touch_activity(member, minutes=30)
    body = api_client.get("/api/achievements/me/goals/").data
    assert body["actual_minutes"] == 30
    assert body["progress_percent"] == 33
    assert body["remaining_minutes"] == 60
    assert body["achieved"] is False


def test_goal_can_be_patched_and_validated(api_client, member):
    response = api_client.patch("/api/achievements/me/goals/", {"weekly_goal_minutes": 30}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["target_minutes"] == 30
    member.profile.refresh_from_db()
    assert member.profile.weekly_goal_minutes == 30

    services.touch_activity(member, minutes=45)
    assert api_client.get("/api/achievements/me/goals/").data["achieved"] is True

    bad = api_client.patch("/api/achievements/me/goals/", {"weekly_goal_minutes": 999999}, format="json")
    assert bad.status_code == status.HTTP_400_BAD_REQUEST
    assert "weekly_goal_minutes" in bad.data
    member.profile.refresh_from_db()
    assert member.profile.weekly_goal_minutes == 30


# ------------------------------------------------------------------------ levels


def test_levels_marks_the_current_level(api_client, member):
    services.award_xp(member, 260, reason="level_test", source_type="lesson", source_id="level-test")
    data = api_client.get("/api/achievements/me/levels/").data
    assert len(data["levels"]) == len(settings.LEVEL_THRESHOLDS)
    assert data["current_level"] == 3 == services.level_for_xp(260)
    assert data["total_xp"] == 260
    assert data["next_level_xp"] == settings.LEVEL_THRESHOLDS[3]
    assert data["progress_percent"] == services.level_progress(260, 3) == 5
    assert [row["level"] for row in data["levels"] if row["is_current"]] == [3]
    assert [row["level"] for row in data["levels"] if row["is_reached"]] == [1, 2, 3]
    assert data["levels"][0]["min_xp"] == 0


# -------------------------------------------------------------------- leaderboard


def test_leaderboard_ranks_xp_from_the_service(api_client, member, peer):
    services.award_xp(member, 120, reason="xp_a", source_type="lesson", source_id="a")
    services.award_xp(peer, 300, reason="xp_b", source_type="lesson", source_id="b")

    response = api_client.get("/api/achievements/leaderboard/", {"period": "alltime", "scope": "xp"})
    assert response.status_code == status.HTTP_200_OK
    rows = response.data["results"]
    assert [row["rank"] for row in rows] == [1, 2]
    assert [row["display_name"] for row in rows] == ["Peer Member", "Badge Hunter"]
    assert rows[0]["value"] == 300
    assert rows[0]["total_xp"] == 300
    assert rows[0]["user"]["id"] == peer.pk
    assert rows[0]["avatar"] is None
    assert "email" not in rows[0]["user"]

    weekly = api_client.get("/api/achievements/leaderboard/", {"period": "weekly", "scope": "xp"}).data["results"]
    assert [row["user"]["id"] for row in weekly] == [peer.pk, member.pk]


def test_leaderboard_can_rank_streaks(api_client, member, peer):
    Profile.objects.filter(user=peer).update(current_streak=9)
    Profile.objects.filter(user=member).update(current_streak=2)
    rows = api_client.get("/api/achievements/leaderboard/", {"scope": "streak"}).data["results"]
    assert [row["user"]["id"] for row in rows] == [peer.pk, member.pk]
    assert rows[0]["current_streak"] == 9
    assert api_client.get("/api/achievements/leaderboard/", {"scope": "streak", "limit": 1}).data["count"] == 1
