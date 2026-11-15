from django.contrib import admin

from apps.challenges.models import Challenge, ChallengeTestCase, Submission


class ChallengeTestCaseInline(admin.TabularInline):
    model = ChallengeTestCase
    extra = 0
    fields = ("name", "args", "expected", "is_public", "position")


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    inlines = [ChallengeTestCaseInline]
    list_display = ("title", "difficulty", "category", "points", "submission_count", "accepted_count",
                    "pass_rate_percent", "is_published", "position")
    list_filter = ("is_published", "difficulty", "category")
    search_fields = ("title", "summary", "description")
    ordering = ("difficulty", "position", "title")
    readonly_fields = ("created_at", "updated_at", "pass_rate_percent", "difficulty_weight", "submission_count",
                       "accepted_count")


@admin.register(ChallengeTestCase)
class ChallengeTestCaseAdmin(admin.ModelAdmin):
    list_display = ("name", "challenge", "is_public", "position")
    list_filter = ("is_public", "challenge__category")
    search_fields = ("name", "challenge__title")
    list_select_related = ("challenge",)
    ordering = ("challenge", "position", "id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "challenge", "language", "score", "passed_count", "total_tests", "passed", "runtime_ms",
                    "is_first_solve", "created_at")
    list_filter = ("passed", "language", "is_first_solve", "challenge__category")
    search_fields = ("user__email", "challenge__title")
    list_select_related = ("user", "challenge")
    ordering = ("-created_at",)
    # Grading output is produced by the code runner and must not be hand-edited.
    readonly_fields = ("created_at", "updated_at", "passed_count", "total_tests", "passed", "score",
                       "points_awarded", "runtime_ms", "error", "runner_report", "is_first_solve", "failed_count")
