from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


class Enrollment(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="enrollments")
    # Denormalised progress so dashboards avoid counting rows per request.
    completed_lesson_count = models.PositiveIntegerField(default=0)
    total_lesson_count = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_lesson = models.ForeignKey(
        "courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    enrolled_via = models.CharField(max_length=30, default="catalog")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "course"], name="uniq_enrollment")]
        indexes = [models.Index(fields=["user", "-created_at"])]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user_id} in {self.course_id}"

    def recalculate(self, commit=True):
        """Refresh counters from LessonCompletion rows — the single source of truth."""
        from apps.courses.models import Lesson

        lessons = Lesson.objects.filter(course=self.course, is_published=True)
        completed = LessonCompletion.objects.filter(user=self.user, lesson__course=self.course).values("lesson")
        completed_ids = {row["lesson"] for row in completed}

        self.total_lesson_count = lessons.count()
        self.completed_lesson_count = len(completed_ids)
        self.progress_percent = (
            0 if not self.total_lesson_count else round(100 * self.completed_lesson_count / self.total_lesson_count)
        )
        if self.total_lesson_count and self.completed_lesson_count >= self.total_lesson_count:
            if not self.is_completed:
                self.is_completed = True
                self.completed_at = timezone.now()
        else:
            self.is_completed = False
            self.completed_at = None
        if commit:
            self.save(
                update_fields=[
                    "total_lesson_count",
                    "completed_lesson_count",
                    "progress_percent",
                    "is_completed",
                    "completed_at",
                    "updated_at",
                ]
            )


class LessonCompletion(TimestampedModel):
    """Idempotent completion record: one row per learner per lesson, ever."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_completions")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="completions")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="lesson_completions")
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="uniq_lesson_completion")]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user_id} finished lesson {self.lesson_id}"


class LessonBookmark(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_bookmarks")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="bookmarks")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="uniq_lesson_bookmark")]


class QuizAttempt(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey("courses.Quiz", on_delete=models.CASCADE, related_name="attempts")
    score_percent = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    # [{question_id, choice_index, correct, correct_index}]
    detail = models.JSONField(default=list, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["user", "quiz", "-created_at"])]
        constraints = [
            models.UniqueConstraint(fields=["user", "quiz", "attempt_number"], name="uniq_quiz_attempt_number")
        ]

    def __str__(self):
        return f"{self.user_id} scored {self.score_percent}% on quiz {self.quiz_id}"


class Certificate(TimestampedModel):
    """Issued when an enrollment reaches 100%; serial makes it verifiable."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="certificates")
    serial = models.CharField(max_length=40, unique=True)
    learner_name = models.CharField(max_length=160)
    issued_at = models.DateTimeField(default=timezone.now, db_index=True)
    hours_studied = models.PositiveIntegerField(default=0)
    final_percent = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ("-issued_at",)
        constraints = [models.UniqueConstraint(fields=["user", "course"], name="uniq_certificate")]

    def __str__(self):
        return f"Certificate {self.serial} for {self.learner_name}"


class ActivityLog(models.Model):
    """One row per learner per active day — the basis for streaks and weekly charts."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    day = models.DateField(db_index=True)
    minutes = models.PositiveIntegerField(default=0)
    lessons_completed = models.PositiveIntegerField(default=0)
    quizzes_passed = models.PositiveIntegerField(default=0)
    challenges_solved = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "day"], name="uniq_activity_day")]
        ordering = ("-day",)

    def __str__(self):
        return f"{self.user_id} on {self.day}"
