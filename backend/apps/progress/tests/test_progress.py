"""Progress, XP, streaks, certificates and the dashboard aggregate.

These cover the two rules the product depends on: progress is always derived from
stored completion rows, and a repeated request must never award points twice.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.achievements.models import PointEvent
from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz, QuizQuestion
from apps.progress.models import ActivityLog, Certificate, Enrollment, LessonCompletion
from apps.users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = "CodeHer!Test2026"


def make_user(name="ada", role="learner"):
    return User.objects.create_user(
        email=f"{name}@example.com", username=name, password=PASSWORD, display_name=name.title(), role=role
    )


def client(user=None):
    api = APIClient()
    if user is not None:
        api.force_authenticate(user=user)
    return api


@pytest.fixture
def course(db):
    path = LearningPath.objects.create(title="JavaScript for Beginners", level="beginner")
    row = Course.objects.create(
        title="Closures and Scope",
        description="How functions capture variables.",
        level="beginner",
        category="javascript",
        duration_hours=4,
        learning_path=path,
        instructor=make_user("grace", role="mentor"),
    )
    module = CourseModule.objects.create(course=row, title="Unit 1", position=1)
    for index in range(3):
        Lesson.objects.create(
            course=row,
            module=module,
            title=f"Lesson {index + 1}",
            position=index + 1,
            xp=20,
            estimated_minutes=12,
            body_blocks=[{"type": "paragraph", "text": "Text"}],
        )
    return row


def enroll(api, course):
    return api.post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")


def complete(api, lesson, **payload):
    return api.post(f"/api/learning/lessons/{lesson.pk}/complete/", payload, format="json")


class TestEnrollment:
    def test_enrolling_twice_creates_one_row_and_one_counter(self, course):
        ada = make_user("ada")
        api = client(ada)
        first, second = enroll(api, course), enroll(api, course)
        assert first.status_code == 201 and second.status_code == 200
        assert second.json()["created"] is False
        assert Enrollment.objects.filter(user=ada, course=course).count() == 1
        course.refresh_from_db()
        assert course.enrolled_count == 1

    def test_new_learner_starts_at_zero_progress(self, course):
        enrollment = enroll(client(make_user("ada")), course).json()["enrollment"]
        assert enrollment["progress_percent"] == 0
        assert enrollment["completed_lesson_count"] == 0
        assert enrollment["total_lesson_count"] == 3
        assert enrollment["is_completed"] is False


class TestLessonCompletion:
    def test_first_completion_awards_xp_once(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        lesson = course.lessons.first()

        response = complete(api, lesson, time_spent_seconds=300)
        assert response.status_code == 201
        body = response.json()
        assert body["xp_awarded"] == 20
        assert body["duplicate"] is False
        assert body["progress_percent"] == 33
        ada.profile.refresh_from_db()
        assert ada.profile.total_xp == 20

    def test_replaying_a_completion_is_idempotent(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        lesson = course.lessons.first()
        complete(api, lesson)

        again = complete(api, lesson)
        assert again.status_code == 200
        assert again.json()["duplicate"] is True
        assert again.json()["xp_awarded"] == 0

        ada.profile.refresh_from_db()
        assert ada.profile.total_xp == 20
        assert LessonCompletion.objects.filter(user=ada, lesson=lesson).count() == 1
        assert PointEvent.objects.filter(user=ada, reason="lesson_complete").count() == 1

    def test_completing_every_lesson_finishes_the_course_once(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        for lesson in course.lessons.order_by("position"):
            response = complete(api, lesson).json()
        assert response["course_completed"] is True
        assert response["progress_percent"] == 100

        enrollment = Enrollment.objects.get(user=ada, course=course)
        assert enrollment.is_completed and enrollment.completed_at

        # 3 lessons x 20 XP plus one course bonus, and no duplicate certificates.
        ada.profile.refresh_from_db()
        assert ada.profile.total_xp == 60 + 150
        assert Certificate.objects.filter(user=ada, course=course).count() == 1

        complete(api, course.lessons.last())
        ada.profile.refresh_from_db()
        assert ada.profile.total_xp == 210
        assert Certificate.objects.filter(user=ada, course=course).count() == 1

    def test_unenrolled_completion_is_refused(self, course):
        lesson = course.lessons.first()
        response = complete(client(make_user("ada")), lesson)
        assert response.status_code == 403
        assert "enroll" in response.json()["detail"].lower()

    def test_unpublished_lesson_cannot_be_completed(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        hidden = Lesson.objects.create(
            course=course, module=course.modules.first(), title="Draft", position=40, is_published=False
        )
        assert complete(api, hidden).status_code == 403

    def test_next_lesson_is_offered_until_the_end(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        first, second, third = course.lessons.order_by("position")
        assert complete(api, first).json()["next_lesson"]["id"] == second.pk
        assert complete(api, second).json()["next_lesson"]["id"] == third.pk
        assert complete(api, third).json()["next_lesson"] is None

    def test_time_spent_is_capped_instead_of_stored_absurd(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        complete(api, course.lessons.first(), time_spent_seconds=10_000_000)
        completion = LessonCompletion.objects.get(user=ada, lesson=course.lessons.first())
        assert completion.time_spent_seconds == 4 * 3600


class TestStreaksAndActivity:
    def test_completion_writes_todays_activity_row(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        complete(api, course.lessons.first(), time_spent_seconds=600)

        day = ActivityLog.objects.get(user=ada, day=timezone.localdate())
        assert day.lessons_completed == 1
        assert day.minutes >= 1
        ada.profile.refresh_from_db()
        assert ada.profile.current_streak >= 1
        assert ada.profile.last_activity_date == timezone.localdate()

    def test_repeated_lessons_on_the_same_day_do_not_inflate_the_streak(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        for lesson in course.lessons.all():
            complete(api, lesson)
        ada.profile.refresh_from_db()
        assert ada.profile.current_streak == 1
        assert ActivityLog.objects.filter(user=ada).count() == 1

    def test_a_gap_of_days_breaks_the_streak_but_keeps_the_longest(self, course):
        ada = make_user("ada")
        enroll(client(ada), course)
        ada.profile.current_streak = 4
        ada.profile.longest_streak = 4
        ada.profile.last_activity_date = timezone.localdate() - timedelta(days=5)
        ada.profile.save()

        complete(client(ada), course.lessons.first())
        ada.profile.refresh_from_db()
        assert ada.profile.current_streak == 1
        assert ada.profile.longest_streak == 4

    def test_activity_endpoint_sums_the_same_rows(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        complete(api, course.lessons.first(), time_spent_seconds=600)
        body = api.get("/api/progress/activity/?days=7").json()
        assert body["totals"]["lessons"] == 1
        assert body["totals"]["minutes"] >= 1
        assert body["series"][-1]["date"] == timezone.localdate().isoformat()


class TestBookmarks:
    def test_bookmark_is_a_toggle_and_appears_in_the_listing(self, course):
        ada = make_user("ada")
        api = client(ada)
        lesson = course.lessons.first()
        assert api.post(f"/api/learning/lessons/{lesson.pk}/bookmark/", {}, format="json").json()["bookmarked"] is True
        assert api.get("/api/progress/bookmarks/").json()["count"] == 1
        assert api.post(f"/api/learning/lessons/{lesson.pk}/bookmark/", {}, format="json").json()["bookmarked"] is False
        assert api.get("/api/progress/bookmarks/").json()["count"] == 0

    def test_another_learners_bookmarks_stay_private(self, course):
        ada = make_user("ada")
        client(ada).post(f"/api/learning/lessons/{course.lessons.first().pk}/bookmark/", {}, format="json")
        assert client(make_user("nia")).get("/api/progress/bookmarks/").json()["count"] == 0


class TestCertificates:
    def test_certificate_list_and_detail_are_owner_scoped(self, course):
        ada, nia = make_user("ada"), make_user("nia")
        api = client(ada)
        enroll(api, course)
        for lesson in course.lessons.order_by("position"):
            complete(api, lesson)

        rows = api.get("/api/learning/me/certificates/").json()["results"]
        assert len(rows) == 1
        assert rows[0]["serial"].startswith("CH-")
        certificate = Certificate.objects.get(user=ada, course=course)
        assert api.get(f"/api/learning/me/certificates/{certificate.pk}/").status_code == 200
        assert client(nia).get(f"/api/learning/me/certificates/{certificate.pk}/").status_code == 404

    def test_serial_is_unique_per_issue(self, course):
        for name in ("ada", "nia"):
            learner = make_user(name)
            api = client(learner)
            enroll(api, course)
            for lesson in course.lessons.order_by("position"):
                complete(api, lesson)
        serials = set(Certificate.objects.values_list("serial", flat=True))
        assert len(serials) == 2


class TestProgressSummary:
    def test_new_account_sees_honest_zeros(self, course):
        body = client(make_user("ada")).get("/api/progress/summary/").json()
        assert body["enrolled_courses"] == 0
        assert body["lessons_completed"] == 0
        assert body["xp"] == 0
        assert body["level"] == 1

    def test_summary_follows_the_stored_rows(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        for lesson in course.lessons.order_by("position")[:2]:
            complete(api, lesson)
        body = api.get("/api/progress/summary/").json()
        assert body["enrolled_courses"] == 1
        assert body["lessons_completed"] == 2
        assert body["xp"] == 40
        assert body["level_for_current_xp"] == body["level"]


class TestDashboard:
    def test_a_brand_new_learner_gets_empty_states_not_invented_numbers(self, course):
        body = client(make_user("ada")).get("/api/dashboard/").json()
        assert body["xp"] == 0 and body["level"] == 1
        assert body["enrolled_courses"] == 0
        assert body["continue_learning"] == []
        assert body["weekly_goal"]["actual_minutes"] == 0
        assert body["streak"]["current"] == 0
        assert body["achievements"] == []
        # Recommendations must come from the catalogue, and there is one published course.
        assert [row["slug"] for row in body["recommended_courses"]] == ["closures-and-scope"]

    def test_dashboard_reflects_real_activity(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        complete(api, course.lessons.first(), time_spent_seconds=900)

        body = api.get("/api/dashboard/").json()
        assert body["xp"] == 20
        assert body["enrolled_courses"] == 1
        assert body["completed_lessons"] == 1
        assert body["completion_rate_percent"] == 33
        assert body["weekly_goal"]["actual_minutes"] >= 1
        assert body["continue_learning"][0]["progress_percent"] == 33
        assert body["continue_learning"][0]["lesson"]["title"] == "Lesson 2"
        # The gap to the next level, never the absolute threshold.
        assert body["xp_to_next_level"] == body["next_level_xp"] - body["xp"] >= 0

    def test_enrolled_courses_are_not_recommended(self, course):
        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        assert api.get("/api/dashboard/").json()["recommended_courses"] == []

    def test_dashboard_requires_a_session(self, course):
        assert client().get("/api/dashboard/").status_code == 401


class TestQuizAttempts:
    def test_attempt_count_is_stored_and_limited(self, course, db):
        lesson = course.lessons.last()
        lesson.kind = "quiz"
        lesson.position = 4
        lesson.save(update_fields=["kind", "position"])
        quiz = Quiz.objects.create(lesson=lesson, title="Wrap-up", passing_percent=60, max_attempts=2)
        QuizQuestion.objects.create(
            quiz=quiz,
            prompt="Which keyword makes a private variable?",
            choices=[{"text": "var"}, {"text": "let", "is_correct": True}],
            position=1,
        )

        ada = make_user("ada")
        api = client(ada)
        enroll(api, course)
        wrong = {"answers": [{"question_id": quiz.questions.first().pk, "choice_index": 0}]}
        assert api.post(f"/api/learning/quizzes/{quiz.pk}/submit/", wrong, format="json").json()["passed"] is False
        assert api.post(f"/api/learning/quizzes/{quiz.pk}/submit/", wrong, format="json").json()["passed"] is False
        exhausted = api.post(f"/api/learning/quizzes/{quiz.pk}/submit/", wrong, format="json")
        assert exhausted.status_code == 403
        assert "attempt" in exhausted.json()["detail"].lower()
        assert Enrollment.objects.filter(user=ada).exists()
