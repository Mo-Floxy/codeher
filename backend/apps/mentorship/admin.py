from django.contrib import admin

from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "current_role", "company", "capacity", "matched_count", "rating_average", "is_approved",
                    "is_accepting")
    list_filter = ("is_approved", "is_accepting")
    search_fields = ("user__email", "user__display_name", "bio", "current_role", "company")
    list_select_related = ("user", "approved_by")
    ordering = ("-is_approved", "-matched_count", "user__display_name")
    readonly_fields = ("created_at", "updated_at", "matched_count", "rating_average", "has_capacity")

    @admin.display(description="user", ordering="user__email")
    def user(self, obj):
        return obj.user.email


class MentorshipSessionInline(admin.TabularInline):
    model = MentorshipSession
    fk_name = "request"
    extra = 0
    fields = ("mentor", "learner", "starts_at", "duration_minutes", "status")


@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    inlines = [MentorshipSessionInline]
    list_display = ("learner", "mentor", "goal", "status", "session_count", "responded_at", "created_at")
    list_filter = ("status", "mentor", "learner")
    search_fields = ("goal", "message", "learner__email", "mentor__email")
    list_select_related = ("learner", "mentor")
    ordering = ("-created_at",)
    # session_count is denormalised and responded_at is stamped by the request workflow.
    readonly_fields = ("created_at", "updated_at", "session_count", "responded_at")


@admin.register(MentorshipSession)
class MentorshipSessionAdmin(admin.ModelAdmin):
    list_display = ("request", "mentor", "learner", "starts_at", "duration_minutes", "status", "learner_attended",
                    "upcoming")
    list_filter = ("status", "mentor", "learner")
    search_fields = ("agenda", "notes", "mentor__email", "learner__email")
    list_select_related = ("request", "mentor", "learner")
    ordering = ("starts_at",)
    readonly_fields = ("created_at", "updated_at", "reminder_sent_at")

    @admin.display(description="upcoming", boolean=True, ordering="starts_at")
    def upcoming(self, obj):
        return obj.is_upcoming
