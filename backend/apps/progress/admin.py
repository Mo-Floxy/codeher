from django.contrib import admin

from apps.progress.models import (
    ActivityLog,
    Certificate,
    Enrollment,
    LessonBookmark,
    LessonCompletion,
    QuizAttempt,
)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "progress_percent", "completed_lesson_count", "total_lesson_count",
                    "is_completed", "completed_at")
    list_filter = ("is_completed", "course", "enrolled_via")
    search_fields = ("user__email", "course__title")
    list_select_related = ("user", "course", "last_lesson")
    ordering = ("-created_at",)
    # Progress counters are recomputed by Enrollment.recalculate() from LessonCompletion rows.
    readonly_fields = ("created_at", "updated_at", "completed_lesson_count", "total_lesson_count",
                       "progress_percent", "is_completed", "completed_at")


@admin.register(LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "lesson", "time_spent_seconds", "created_at")
    list_filter = ("course",)
    search_fields = ("user__email", "lesson__title", "course__title")
    list_select_related = ("user", "lesson", "course")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(LessonBookmark)
class LessonBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "course", "created_at")
    list_filter = ("lesson__course",)
    search_fields = ("user__email", "lesson__title")
    list_select_related = ("user", "lesson", "lesson__course")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="course", ordering="lesson__course__title")
    def course(self, obj):
        return obj.lesson.course


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score_percent", "correct_count", "total_count", "passed", "attempt_number",
                    "created_at")
    list_filter = ("passed", "quiz__lesson__course")
    search_fields = ("user__email", "quiz__title", "quiz__lesson__title")
    list_select_related = ("user", "quiz", "quiz__lesson")
    ordering = ("-created_at",)
    # Scoring results are written by the quiz-grading service, not by hand.
    readonly_fields = ("created_at", "updated_at", "score_percent", "correct_count", "total_count", "passed", "detail")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("serial", "user", "course", "learner_name", "final_percent", "issued_at")
    list_filter = ("course",)
    search_fields = ("serial", "learner_name", "user__email", "course__title")
    list_select_related = ("user", "course")
    ordering = ("-issued_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "day", "minutes", "lessons_completed", "quizzes_passed", "challenges_solved", "xp_earned")
    list_filter = ("day",)
    search_fields = ("user__email",)
    list_select_related = ("user",)
    ordering = ("-day",)
