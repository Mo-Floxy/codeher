"""Catalogue, curriculum access rules and course authoring permissions."""

import pytest
from rest_framework.test import APIClient

from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz, QuizQuestion
from apps.users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = "CodeHer!Test2026"


def make_user(name="ada", role="learner"):
    return User.objects.create_user(
        email=f"{name}@example.com", username=name, password=PASSWORD, display_name=name.title(), role=role
    )


def api(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def titles(payload):
    return sorted(row["title"] for row in payload["results"])


def make_path(title="React Development", **overrides):
    return LearningPath.objects.create(title=title, description="Build interfaces.", level="beginner", **overrides)


def make_course(path, title="Hooks in Practice", instructor=None, **overrides):
    return Course.objects.create(
        title=title,
        subtitle="State, effects and refs.",
        description="A hands-on course about React hooks.",
        level="intermediate",
        category="react",
        duration_hours=6,
        learning_path=path,
        instructor=instructor,
        **overrides,
    )


def make_lessons(course, count=3, module=None, **overrides):
    module = module or CourseModule.objects.create(course=course, title="Unit 1", position=1)
    return [
        Lesson.objects.create(
            course=course,
            module=module,
            title=f"Lesson {index + 1}",
            position=index + 1,
            body_blocks=[{"type": "paragraph", "text": "Content"}],
            **overrides,
        )
        for index in range(count)
    ]


def make_quiz_lesson(course, module):
    lesson = Lesson.objects.create(
        course=course, module=module, title="Check your understanding", kind="quiz", position=4
    )
    quiz = Quiz.objects.create(lesson=lesson, title="Hooks quiz", passing_percent=50)
    QuizQuestion.objects.create(
        quiz=quiz,
        prompt="Which hook runs after paint?",
        choices=[{"text": "useMemo"}, {"text": "useEffect", "is_correct": True}],
        position=1,
    )
    QuizQuestion.objects.create(
        quiz=quiz,
        prompt="What does useRef return?",
        choices=[{"text": "A mutable box", "is_correct": True}, {"text": "A proxy"}],
        position=2,
    )
    return lesson, quiz


class TestCatalog:
    def test_paths_lists_only_published_tracks_with_their_courses(self):
        published = make_path(title="Python Programming")
        make_path(title="Secret Draft", is_published=False)
        course = make_course(published, title="Python Basics")
        make_lessons(course, count=2)

        body = api().get("/api/learning/paths/").json()
        assert body["count"] == 1
        row = body["results"][0]
        assert row["slug"] == "python-programming"
        assert row["course_count"] == 1
        assert row["lesson_count"] == 2

    def test_courses_are_public_and_paginated(self):
        path = make_path()
        for index in range(14):
            make_course(path, title=f"Course {index:02d}")
        body = api().get("/api/learning/courses/").json()
        assert body["count"] == 14
        assert len(body["results"]) == 12
        assert body["next"]

    def test_filters_search_level_category_and_path(self):
        path = make_path()
        css = make_course(path, title="CSS Layout Deep Dive", category="web", level="advanced")
        make_course(path, title="Python Basics", category="python", level="beginner")
        make_lessons(css)

        assert titles(api().get("/api/learning/courses/?search=layout").json()) == ["CSS Layout Deep Dive"]
        assert titles(api().get("/api/learning/courses/?level=beginner").json()) == ["Python Basics"]
        assert titles(api().get("/api/learning/courses/?category=web").json()) == ["CSS Layout Deep Dive"]
        assert titles(api().get(f"/api/learning/courses/?path_slug={path.slug}").json()) == [
            "CSS Layout Deep Dive",
            "Python Basics",
        ]

    def test_ordering_is_whitelisted(self):
        path = make_path()
        make_course(path, title="Aaaa", duration_hours=2)
        make_course(path, title="Bbbb", duration_hours=9)
        response = api().get("/api/learning/courses/?ordering=-duration_hours")
        assert [row["title"] for row in response.json()["results"]] == ["Bbbb", "Aaaa"]
        # An unknown ordering key must not become a database error.
        assert api().get("/api/learning/courses/?ordering=password__raw").status_code == 200

    def test_unpublished_course_is_invisible_to_learners_but_not_to_admins(self):
        hidden = make_course(make_path(), title="Unreleased", is_published=False)
        assert api().get(f"/api/learning/courses/{hidden.slug}/").status_code == 404
        assert api(make_user("nia")).get(f"/api/learning/courses/{hidden.slug}/").status_code == 404
        admin = api(make_user("root", role="admin"))
        assert admin.get(f"/api/learning/courses/{hidden.slug}/").status_code == 200

    def test_course_is_addressable_by_slug_or_id(self):
        course = make_course(make_path(), title="Naming Things")
        by_slug = api().get(f"/api/learning/courses/{course.slug}/")
        by_id = api().get(f"/api/learning/courses/{course.pk}/")
        assert by_slug.status_code == by_id.status_code == 200
        assert by_slug.json()["id"] == by_id.json()["id"] == course.pk

    def test_a_bad_lookup_is_a_404_not_a_500(self):
        assert api().get("/api/learning/courses/does-not-exist/").status_code == 404
        assert api().get("/api/learning/lessons/999999/").status_code == 404


class TestCourseAuthoring:
    def test_only_admins_may_create_courses(self):
        payload = {"title": "Git for Everyone", "level": "beginner", "category": "tools", "duration_hours": 3}
        assert api().post("/api/learning/courses/", payload, format="json").status_code == 401
        assert api(make_user("nia")).post("/api/learning/courses/", payload, format="json").status_code == 403

        response = api(make_user("root", role="admin")).post("/api/learning/courses/", payload, format="json")
        assert response.status_code == 201, response.data
        created = Course.objects.get(title="Git for Everyone")
        # The admin supplied no instructor, so the author is credited automatically.
        assert created.instructor.role == "admin"
        assert created.slug == "git-for-everyone"

    def test_admins_can_update_and_delete(self):
        course = make_course(make_path(), title="Old Title")
        admin = api(make_user("root", role="admin"))
        patched = admin.patch(f"/api/learning/courses/{course.slug}/", {"title": "New Title"}, format="json")
        assert patched.status_code == 200
        course.refresh_from_db()
        assert course.title == "New Title"
        assert admin.delete(f"/api/learning/courses/{course.slug}/").status_code == 204
        assert not Course.objects.filter(pk=course.pk).exists()

    def test_invalid_write_payloads_are_rejected(self):
        admin = api(make_user("root", role="admin"))
        assert admin.post("/api/learning/courses/", {"title": ""}, format="json").status_code == 400
        assert admin.post("/api/learning/courses/", {"title": "X", "level": "wizard"}, format="json").status_code == 400


class TestLessonAccess:
    def test_locked_lesson_asks_for_enrollment_before_content(self):
        course = make_course(make_path())
        lesson = make_lessons(course, count=1)[0]
        response = api().get(f"/api/learning/lessons/{lesson.pk}/")
        assert response.status_code == 403
        body = response.json()
        assert body["locked"] is True
        assert "body_blocks" not in body["lesson"]

        learner = make_user("ada")
        api(learner).post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")
        opened = api(learner).get(f"/api/learning/lessons/{lesson.pk}/")
        assert opened.status_code == 200
        assert opened.json()["body_blocks"]

    def test_open_lessons_are_readable_without_enrolling(self):
        course = make_course(make_path())
        lesson = make_lessons(course, count=1, requires_enrollment=False)[0]
        assert api().get(f"/api/learning/lessons/{lesson.pk}/").status_code == 200

    def test_curriculum_marks_completion_and_locking(self):
        course = make_course(make_path())
        make_lessons(course, count=3)
        anonymous = api().get(f"/api/learning/courses/{course.slug}/curriculum/")
        assert anonymous.status_code == 200
        assert anonymous.json()["enrolled"] is False
        assert anonymous.json()["progress_percent"] == 0

        learner = make_user("ada")
        client = api(learner)
        client.post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")
        client.post(f"/api/learning/lessons/{course.lessons.first().pk}/complete/", {}, format="json")
        body = client.get(f"/api/learning/courses/{course.slug}/curriculum/").json()
        flags = [row["completed"] for module in body["modules"] for row in module["lessons"]]
        assert flags.count(True) == 1
        assert body["progress_percent"] == 33

    def test_unpublished_lessons_never_reach_the_curriculum(self):
        course = make_course(make_path())
        module = CourseModule.objects.create(course=course, title="Unit 1", position=1)
        make_lessons(course, count=2, module=module)
        make_lessons(course, count=1, module=module, is_published=False, position=9)
        body = api().get(f"/api/learning/courses/{course.slug}/curriculum/").json()
        assert sum(len(module["lessons"]) for module in body["modules"]) == 2


class TestEnrollmentApi:
    def test_enroll_requires_a_session(self):
        course = make_course(make_path())
        assert api().post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json").status_code == 401

    def test_my_enrollments_only_shows_the_owner(self):
        course = make_course(make_path())
        ada, nia = make_user("ada"), make_user("nia")
        api(ada).post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")
        assert api(ada).get("/api/learning/me/enrollments/").json()["count"] == 1
        assert api(nia).get("/api/learning/me/enrollments/").json()["count"] == 0

    def test_unenrolling_recounts_the_public_counter(self):
        course = make_course(make_path())
        ada = make_user("ada")
        client = api(ada)
        client.post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")
        course.refresh_from_db()
        assert course.enrolled_count == 1
        client.delete(f"/api/learning/courses/{course.slug}/enroll/")
        course.refresh_from_db()
        assert course.enrolled_count == 0


class TestQuizzes:
    @pytest.fixture
    def quiz_lesson(self, db):
        course = make_course(make_path())
        module = CourseModule.objects.create(course=course, title="Unit 1", position=1)
        make_lessons(course, count=1, module=module)
        lesson, quiz = make_quiz_lesson(course, module)
        learner = make_user("ada")
        client = api(learner)
        client.post(f"/api/learning/courses/{course.slug}/enroll/", {}, format="json")
        return course, lesson, quiz, client

    def test_correct_answers_pass_and_report_per_question_feedback(self, quiz_lesson):
        _, lesson, quiz, client = quiz_lesson
        answers = [{"question_id": q.pk, "choice_index": q.correct_index} for q in quiz.questions.all()]
        body = client.post(f"/api/learning/quizzes/{quiz.pk}/submit/", {"answers": answers}, format="json").json()
        assert body["passed"] is True
        assert body["score_percent"] == 100
        assert body["correct"] == 2
        assert all(row["correct"] for row in body["results"])
        assert body["xp_awarded"] == quiz.xp

    def test_the_lesson_payload_hides_the_correct_choice(self, quiz_lesson):
        _, lesson, quiz, client = quiz_lesson
        questions = client.get(f"/api/learning/lessons/{lesson.pk}/").json()["quiz"]["questions"]
        assert len(questions) == 2
        for question in questions:
            assert "correct_index" not in question
            assert all("is_correct" not in choice for choice in question["choices"])

    def test_a_client_reported_score_is_ignored(self, quiz_lesson):
        _, _, quiz, client = quiz_lesson
        question = quiz.questions.first()
        payload = {
            "answers": [{"question_id": question.pk, "choice_index": 0}],
            "score_percent": 100,
            "passed": True,
        }
        body = client.post(f"/api/learning/quizzes/{quiz.pk}/submit/", payload, format="json").json()
        assert body["score_percent"] == 0
        assert body["passed"] is False
        assert body["xp_awarded"] == 0

    def test_answering_without_enrollment_is_refused(self):
        course = make_course(make_path())
        module = CourseModule.objects.create(course=course, title="Unit 1", position=1)
        make_lessons(course, count=1, module=module)
        _, quiz = make_quiz_lesson(course, module)
        response = api(make_user("ada")).post(
            f"/api/learning/quizzes/{quiz.pk}/submit/", {"answers": [{"question_id": 1, "choice_index": 0}]}, format="json"
        )
        assert response.status_code == 403

    def test_empty_answers_are_a_400(self, quiz_lesson):
        _, _, quiz, client = quiz_lesson
        assert client.post(f"/api/learning/quizzes/{quiz.pk}/submit/", {}, format="json").status_code == 400
