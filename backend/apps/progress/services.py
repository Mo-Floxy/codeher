"""Enrollment, lesson completion, quiz grading and certificates.

Progress is always derived from stored completion rows. Nothing in this module
trusts a client-supplied percentage.
"""

import logging
import secrets

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.achievements.services import award_xp, evaluate_achievements, recalculate_streak, touch_activity
from apps.courses.models import Course, Lesson
from apps.progress.models import Certificate, Enrollment, LessonBookmark, LessonCompletion, QuizAttempt

logger = logging.getLogger("apps.progress")


def enroll(user, course):
    """Idempotent enrollment. Returns (enrollment, created_bool)."""
    enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)
    if created:
        enrollment.recalculate()
        Course.objects.filter(pk=course.pk).update(enrolled_count=enrollment.course.enrollments.count())
    return enrollment, created


def _require_lesson_access(user, lesson):
    if not lesson.is_published or not lesson.course.is_published:
        return "This lesson is not available yet."
    if lesson.requires_enrollment and not Enrollment.objects.filter(user=user, course=lesson.course).exists():
        return "Enroll in the course before completing this lesson."
    return None


def complete_lesson(user, lesson, time_spent_seconds=0):
    """Record a completion once, award XP once, and refresh derived progress.

    Returns {"created": bool, "enrollment": Enrollment, "xp_awarded": int}.
    """
    reason = _require_lesson_access(user, lesson)
    if reason:
        raise PermissionError(reason)

    with transaction.atomic():
        try:
            # Its own savepoint: catching the IntegrityError inside the enclosing
            # block would leave the transaction unusable for the rest of the call.
            with transaction.atomic():
                completion = LessonCompletion.objects.create(
                    user=user,
                    lesson=lesson,
                    course=lesson.course,
                    time_spent_seconds=max(0, min(int(time_spent_seconds or 0), 4 * 3600)),
                )
            created = True
        except IntegrityError:
            completion = LessonCompletion.objects.get(user=user, lesson=lesson)
            created = False

        enrollment = Enrollment.objects.get(user=user, course=lesson.course)
        enrollment.last_lesson = lesson
        enrollment.recalculate(commit=False)
        enrollment.save(update_fields=["total_lesson_count", "completed_lesson_count", "progress_percent", "is_completed", "completed_at", "last_lesson", "updated_at"])

    xp_awarded = 0
    if created:
        awarded, _ = award_xp(
            user,
            lesson.xp or settings.XP_RULES["lesson_complete"],
            reason="lesson_complete",
            source_type="lesson",
            source_id=lesson.pk,
            note=lesson.title,
        )
        if awarded:
            xp_awarded = lesson.xp or settings.XP_RULES["lesson_complete"]
        minutes = max(1, round((completion.time_spent_seconds or lesson.estimated_minutes) / 60))
        touch_activity(user, minutes=minutes, lessons=1, xp=xp_awarded)
        recalculate_streak(user)

    if enrollment.is_completed:
        certificate = issue_certificate(user, enrollment.course)
        _on_course_completed(user, enrollment.course, certificate)

    if created:
        evaluate_achievements(user)

    return {"created": created, "enrollment": enrollment, "xp_awarded": xp_awarded}


def toggle_bookmark(user, lesson):
    bookmark = LessonBookmark.objects.filter(user=user, lesson=lesson).first()
    if bookmark:
        bookmark.delete()
        return False
    LessonBookmark.objects.create(user=user, lesson=lesson)
    return True


def grade_quiz(user, quiz, answers):
    """Score answers against stored correct choices.

    `answers` is {question_id: choice_index}. Never trusts a client-reported score.
    """
    reason = None
    if not quiz.lesson.course.is_published:
        reason = "This quiz is not available."
    elif quiz.lesson.requires_enrollment and not Enrollment.objects.filter(
        user=user, course=quiz.lesson.course
    ).exists():
        reason = "Enroll in the course before taking this quiz."
    if reason:
        raise PermissionError(reason)

    if quiz.max_attempts:
        used = QuizAttempt.objects.filter(user=user, quiz=quiz).count()
        if used >= quiz.max_attempts:
            raise PermissionError("You have used every attempt allowed for this quiz.")

    questions = list(quiz.questions.all())
    if not questions:
        raise PermissionError("This quiz has no questions yet.")

    detail = []
    correct = 0
    for question in questions:
        raw = answers.get(question.pk) or answers.get(str(question.pk))
        chosen = None
        if raw is not None:
            try:
                chosen = int(raw)
            except (TypeError, ValueError):
                chosen = None
        is_correct = chosen is not None and chosen == question.correct_index
        if is_correct:
            correct += 1
        detail.append(
            {
                "question_id": question.pk,
                "choice_index": chosen,
                "correct": is_correct,
                "correct_index": question.correct_index,
                "explanation": question.explanation,
            }
        )

    total = len(questions)
    score = round(100 * correct / total)
    passed = score >= quiz.passing_percent

    attempt_number = QuizAttempt.objects.filter(user=user, quiz=quiz).count() + 1
    try:
        with transaction.atomic():
            attempt = QuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                score_percent=score,
                correct_count=correct,
                total_count=total,
                passed=passed,
                detail=detail,
                attempt_number=attempt_number,
            )
    except IntegrityError:
        # A concurrent retry claimed this attempt number; recount and give up quietly.
        attempt = QuizAttempt.objects.filter(user=user, quiz=quiz).order_by("-attempt_number").first()
        attempt.xp_awarded = 0
        return attempt

    if passed:
        awarded, _ = award_xp(
            user,
            quiz.xp or settings.XP_RULES["quiz_pass"],
            reason="quiz_pass",
            source_type="quiz",
            source_id=quiz.pk,
            note=quiz.lesson.title,
        )
        attempt.xp_awarded = quiz.xp if awarded else 0
        touch_activity(user, quizzes=1, xp=attempt.xp_awarded)
        recalculate_streak(user)
        evaluate_achievements(user)
    else:
        attempt.xp_awarded = 0

    return attempt


def lesson_next(user, lesson):
    """The following published lesson in course order, or None."""
    return (
        Lesson.objects.filter(course=lesson.course, is_published=True, position__gt=lesson.position)
        .order_by("position", "id")
        .first()
    )


def issue_certificate(user, course):
    """Certificates are unique per learner+course; re-issuing returns the existing row."""
    certificate, created = Certificate.objects.get_or_create(
        user=user,
        course=course,
        defaults={
            "serial": generate_serial(),
            "learner_name": user.display_name,
            "issued_at": timezone.now(),
            "hours_studied": course.duration_hours,
            "final_percent": 100,
        },
    )
    return certificate


def generate_serial():
    return f"CH-{timezone.now():%Y}-{secrets.token_hex(6).upper()}"


def _on_course_completed(user, course, certificate):
    awarded, _ = award_xp(
        user,
        settings.XP_RULES["course_complete"],
        reason="course_complete",
        source_type="course",
        source_id=course.pk,
        note=course.title,
    )
    if awarded:
        touch_activity(user, xp=settings.XP_RULES["course_complete"])

    from apps.notifications.services import notify

    notify(
        user,
        kind="course_announcement",
        title=f"Course completed: {course.title}",
        body="Your completion record is available for download.",
        link=f"/learning/{course.slug}/certificate",
        dedupe_key=f"certificate:{certificate.pk}",
    )


def sync_counters(course):
    """Keep the denormalised enrollment count honest after admin edits."""
    course.enrolled_count = Enrollment.objects.filter(course=course).count()
    course.save(update_fields=["enrolled_count", "updated_at"])
    return course.enrolled_count
