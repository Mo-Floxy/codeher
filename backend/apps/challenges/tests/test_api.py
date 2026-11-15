"""API tests for the challenge catalogue and the sandbox proxy.

The runner is always faked here: these tests must prove what the API reports,
never that a local sandbox happens to be running.
"""

import datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.achievements.models import PointEvent
from apps.achievements.services import award_xp
from apps.challenges import services
from apps.challenges.models import Challenge, ChallengeTestCase, Submission
from apps.core.exceptions import RunnerUnavailable
from apps.users.models import Profile, User

HIDDEN_NAME = "hidden: rounding guard"
HIDDEN_EXPECTED = "HIDDEN-EXPECTED-918273"
PUBLIC_NAME = "adds two numbers"

pytestmark = pytest.mark.django_db


def make_member(username, email, display_name):
    user = User.objects.create_user(
        email=email, username=username, password="runner-test-pass-1", display_name=display_name
    )
    # The users app creates the profile for us; get_or_create keeps this true either way.
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def learner(db):
    return make_member("learner", "learner@codeher.test", "Lear One")


@pytest.fixture
def other_member(db):
    return make_member("someone", "someone@codeher.test", "Some Other")


@pytest.fixture
def anonymous():
    return APIClient()


@pytest.fixture
def auth_client(learner):
    client = APIClient()
    client.force_authenticate(user=learner)
    return client


@pytest.fixture
def challenge(db):
    item = Challenge.objects.create(
        title="Two Sum",
        summary="Find the pair that adds up.",
        description="Implement `two_sum(numbers, target)`.",
        difficulty="beginner",
        category="javascript",
        points=20,
        function_name="two_sum",
        allowed_languages=["javascript", "python"],
        starter_code={"javascript": "function two_sum(numbers, target) {}", "python": "def two_sum(numbers, target): pass"},
        examples=[{"input": [1, 2], "explanation": "returns 3"}],
    )
    ChallengeTestCase.objects.create(
        challenge=item, name=PUBLIC_NAME, args=[[1, 2], 3], expected=3, is_public=True, position=1
    )
    ChallengeTestCase.objects.create(
        challenge=item, name=HIDDEN_NAME, args=[[99, 1], 100], expected=HIDDEN_EXPECTED, is_public=False, position=2
    )
    return item


def passing_runner(*, fail_names=()):
    """Stand-in for `services.runner_run` that mirrors the runner's report shape."""

    def _fake(code, language, function_name, tests, time_limit_ms=None, memory_limit_mb=None):
        results = []
        for case in tests:
            passed = case["name"] not in fail_names
            results.append(
                {
                    "name": case["name"],
                    "passed": passed,
                    "expected": case["expected"],
                    "actual": case["expected"] if passed else "wrong",
                    "error": None if passed else "assertion failed",
                }
            )
        return {"ok": all(row["passed"] for row in results), "runtime_ms": 17, "results": results}

    return _fake


# --------------------------------------------------------------------- catalogue


def test_anonymous_can_list_challenges(anonymous, challenge):
    response = anonymous.get("/api/challenges/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    card = response.data["results"][0]
    assert card["slug"] == "two-sum"
    # Cards carry metadata only — no grading data of any kind.
    assert "test_cases" not in card
    assert "public_tests" not in card
    assert HIDDEN_EXPECTED not in response.content.decode()


def test_challenge_list_pagination_envelope(anonymous, challenge):
    for index in range(14):
        Challenge.objects.create(title="Extra {} ".format(index), description="d", category="javascript")
    response = anonymous.get("/api/challenges/", {"page_size": 5})
    assert response.data["count"] == 15
    assert len(response.data["results"]) == 5
    assert response.data["next"] is not None


def test_filters_and_ordering_apply(anonymous, challenge):
    Challenge.objects.create(
        title="Regex hunt", description="d", difficulty="advanced", category="regex", points=90
    )
    assert anonymous.get("/api/challenges/", {"difficulty": "beginner"}).data["count"] == 1
    # The UI sends the human label for a category; the API maps it to the stored value.
    assert anonymous.get("/api/challenges/", {"category": "Regular Expressions"}).data["count"] == 1
    assert anonymous.get("/api/challenges/", {"search": "regex"}).data["count"] == 1
    response = anonymous.get("/api/challenges/", {"ordering": "points"})
    assert [row["points"] for row in response.data["results"]] == [90, 20]
    assert anonymous.get("/api/challenges/", {"difficulty": "beginner", "category": "python"}).data["count"] == 0


def test_detail_by_id_and_by_slug_match(anonymous, challenge):
    by_id = anonymous.get("/api/challenges/{}/".format(challenge.pk))
    by_slug = anonymous.get("/api/challenges/{}/".format(challenge.slug))
    assert by_id.status_code == by_slug.status_code == status.HTTP_200_OK
    assert by_id.data["id"] == by_slug.data["id"] == challenge.pk
    assert by_id.data["starter_code"]["python"].startswith("def two_sum")
    assert by_id.data["function_name"] == "two_sum"
    assert by_id.data["examples"][0]["input"] == [1, 2]
    assert anonymous.get("/api/challenges/does-not-exist/").status_code == status.HTTP_404_NOT_FOUND


def test_hidden_cases_are_never_serialised_in_detail(anonymous, challenge):
    response = anonymous.get("/api/challenges/{}/".format(challenge.slug))
    body = response.content.decode()
    assert [row["name"] for row in response.data["public_tests"]] == [PUBLIC_NAME]
    assert response.data["test_count"] == 2
    assert HIDDEN_NAME not in body
    assert HIDDEN_EXPECTED not in body


def test_unpublished_challenge_is_hidden_from_members(anonymous, learner, challenge):
    hidden = Challenge.objects.create(title="Draft task", description="d", is_published=False)
    assert anonymous.get("/api/challenges/").data["count"] == 1
    assert anonymous.get("/api/challenges/{}/".format(hidden.pk)).status_code == status.HTTP_404_NOT_FOUND
    client = APIClient()
    client.force_authenticate(user=learner)
    assert client.get("/api/challenges/{}/".format(hidden.pk)).status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------ run / submit


def test_run_and_submit_require_authentication(anonymous, challenge):
    for path in ("run", "submit"):
        response = anonymous.post("/api/challenges/{}/".format(challenge.pk) + path + "/", {"language": "javascript", "code": "x"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_run_executes_public_cases_only_and_stores_nothing(auth_client, challenge, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner())
    response = auth_client.post(
        "/api/challenges/{}/run/".format(challenge.pk), {"language": "javascript", "code": "return 3;"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["ok"] is True
    assert response.data["runtime_ms"] == 17
    assert [row["name"] for row in response.data["results"]] == [PUBLIC_NAME]
    assert response.data["summary"] == {"passed": 1, "total": 1}
    assert Submission.objects.count() == 0
    assert HIDDEN_EXPECTED not in response.content.decode()


def test_run_rejects_blank_code_and_unknown_language(auth_client, challenge):
    blank = auth_client.post("/api/challenges/{}/run/".format(challenge.pk), {"language": "javascript", "code": "   "}, format="json")
    assert blank.status_code == status.HTTP_400_BAD_REQUEST
    assert "code" in blank.data

    challenge.allowed_languages = ["javascript"]
    challenge.save()
    response = auth_client.post(
        "/api/challenges/{}/run/".format(challenge.pk), {"language": "python", "code": "def x(): pass"}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not allowed" in response.data["detail"]


def test_submit_awards_points_on_first_solve_only(auth_client, challenge, learner, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner())
    body = {"language": "python", "code": "def two_sum(numbers, target):\n    return 3\n"}

    first = auth_client.post("/api/challenges/{}/submit/".format(challenge.pk), body, format="json")
    assert first.status_code == status.HTTP_201_CREATED
    assert first.data["passed"] is True
    assert first.data["score"] == 100
    assert first.data["passed_count"] == first.data["total_tests"] == 2
    assert first.data["points_awarded"] == 20
    assert first.data["first_solve_bonus"] is True
    assert first.data["language"] == "python"

    learner.profile.refresh_from_db()
    assert learner.profile.total_xp == 20
    assert PointEvent.objects.filter(user=learner, reason="challenge_solve").count() == 1
    challenge.refresh_from_db()
    assert (challenge.submission_count, challenge.accepted_count) == (1, 1)

    second = auth_client.post("/api/challenges/{}/submit/".format(challenge.pk), body, format="json")
    assert second.status_code == status.HTTP_201_CREATED
    assert second.data["points_awarded"] == 0
    assert second.data["first_solve_bonus"] is False
    learner.profile.refresh_from_db()
    assert learner.profile.total_xp == 20
    assert PointEvent.objects.filter(user=learner, reason="challenge_solve").count() == 1
    assert Submission.objects.filter(user=learner, challenge=challenge).count() == 2


def test_submit_hides_expected_values_of_hidden_cases(auth_client, challenge, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner())
    response = auth_client.post(
        "/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "return 3;"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data["results"]) == 2
    hidden_row = next(row for row in response.data["results"] if row["name"] == HIDDEN_NAME)
    assert hidden_row["passed"] is True
    assert hidden_row["expected"] is None
    assert hidden_row["actual"] is None
    body = response.content.decode()
    assert HIDDEN_EXPECTED not in body
    assert "runner_report" not in body
    # The stored submission keeps the grading report server-side only.
    submission = Submission.objects.get(pk=response.data["id"])
    assert len(submission.runner_report) == 2


def test_submit_without_passing_earns_nothing(auth_client, challenge, learner, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner(fail_names=[HIDDEN_NAME]))
    response = auth_client.post(
        "/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "return 0;"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["passed"] is False
    assert response.data["score"] == 50
    assert response.data["points_awarded"] == 0
    assert response.data["summary"] == {"passed": 1, "total": 2}
    assert PointEvent.objects.filter(user=learner).count() == 0
    assert Submission.objects.count() == 1


def test_unreachable_runner_is_503_and_never_a_pass(auth_client, challenge, monkeypatch):
    def unavailable(**kwargs):
        raise RunnerUnavailable("The code runner is not reachable.")

    monkeypatch.setattr(services, "runner_run", unavailable)

    run = auth_client.post("/api/challenges/{}/run/".format(challenge.pk), {"language": "javascript", "code": "1"}, format="json")
    assert run.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "runner" in run.data["detail"].lower()
    assert "results" not in run.data

    submit = auth_client.post(
        "/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "1"}, format="json"
    )
    assert submit.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert Submission.objects.count() == 0
    assert not Submission.objects.filter(passed=True).exists()


def test_submit_needs_grading_data(auth_client, monkeypatch, learner):
    empty = Challenge.objects.create(title="No tests yet", description="d", allowed_languages=["javascript"])
    monkeypatch.setattr(services, "runner_run", passing_runner())
    response = auth_client.post("/api/challenges/{}/submit/".format(empty.pk), {"language": "javascript", "code": "1"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no test cases" in response.data["detail"].lower()


# ------------------------------------------------------------------- submissions


def test_my_submissions_history_supports_challenge_filter(auth_client, challenge, other_member, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner())
    auth_client.post("/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "return 3;"}, format="json")

    foreign = Submission.objects.create(user=other_member, challenge=challenge, language="javascript", code="x", passed=True, score=100)
    response = auth_client.get("/api/challenges/submissions/me/", {"challenge": challenge.pk})
    assert response.status_code == status.HTTP_200_OK
    ids = [row["id"] for row in response.data["results"]]
    assert foreign.pk not in ids
    assert len(ids) == 1
    assert response.data["results"][0]["challenge"]["slug"] == "two-sum"
    assert HIDDEN_EXPECTED not in response.content.decode()

    assert auth_client.get("/api/challenges/submissions/me/", {"challenge": 999999}).data["count"] == 0


def test_challenge_specific_history_returns_best_and_recent(auth_client, challenge, monkeypatch):
    monkeypatch.setattr(services, "runner_run", passing_runner(fail_names=[HIDDEN_NAME]))
    auth_client.post("/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "nope"}, format="json")
    monkeypatch.setattr(services, "runner_run", passing_runner())
    auth_client.post("/api/challenges/{}/submit/".format(challenge.pk), {"language": "javascript", "code": "return 3;"}, format="json")

    response = auth_client.get("/api/challenges/{}/submissions/me/".format(challenge.slug))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["best"]["passed"] is True
    assert len(response.data["recent"]) == 2
    assert response.data["total"] == 2


def test_my_submissions_requires_authentication(anonymous, challenge):
    assert anonymous.get("/api/challenges/submissions/me/").status_code == status.HTTP_401_UNAUTHORIZED
    assert anonymous.get("/api/challenges/{}/submissions/me/".format(challenge.pk)).status_code == status.HTTP_401_UNAUTHORIZED


# -------------------------------------------------------------------- leaderboard


def test_leaderboard_ranks_by_real_points_and_solves(auth_client, challenge, learner, other_member):
    second = Challenge.objects.create(title="Streak builder", description="d", points=30, difficulty="intermediate")
    for member, solved, amount in ((learner, 1, 40), (other_member, 2, 30)):
        for index in range(solved):
            Submission.objects.create(
                user=member, challenge=challenge if index == 0 else second, language="javascript", code="x", passed=True, score=100
            )
        award_xp(member, amount, reason="test_award_{}".format(amount), source_type="lesson", source_id=member.pk)

    response = auth_client.get("/api/challenges/leaderboard/", {"period": "alltime"})
    assert response.status_code == status.HTTP_200_OK
    rows = response.data["results"]
    assert [row["display_name"] for row in rows] == ["Lear One", "Some Other"]
    assert [row["rank"] for row in rows] == [1, 2]
    assert rows[0]["points"] == 40
    assert rows[0]["solved_count"] == 1
    assert rows[1]["solved_count"] == 2
    assert rows[0]["user"]["id"] == learner.pk
    assert "email" not in rows[0]["user"]
    assert rows[0]["avatar"] is None

    alltime = {row["user"]["id"]: row["points"] for row in rows}
    weekly = {row["user"]["id"]: row["points"] for row in auth_client.get("/api/challenges/leaderboard/", {"period": "weekly"}).data["results"]}
    assert alltime == weekly  # awards happened inside the current week
    assert auth_client.get("/api/challenges/leaderboard/", {"period": "nonsense"}).status_code == status.HTTP_200_OK


def test_leaderboard_ignores_events_older_than_the_week(auth_client, challenge, learner, other_member):
    award_xp(other_member, 500, reason="old_award", source_type="lesson", source_id=other_member.pk)
    PointEvent.objects.filter(user=other_member).update(
        created_at=datetime.datetime(2019, 1, 1, tzinfo=datetime.timezone.utc)
    )

    assert [row["user"]["id"] for row in auth_client.get("/api/challenges/leaderboard/", {"period": "weekly"}).data["results"]] == []
    alltime = auth_client.get("/api/challenges/leaderboard/", {"period": "alltime"}).data["results"]
    assert [row["user"]["id"] for row in alltime] == [other_member.pk]
    assert alltime[0]["points"] == 500
