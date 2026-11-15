from django.contrib import admin

from apps.achievements.models import Achievement, PointEvent, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "metric", "requirement_value", "xp_reward", "is_active")
    list_filter = ("category", "metric", "is_active")
    search_fields = ("code", "title", "description")
    ordering = ("category", "requirement_value", "title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "earned_at")
    list_filter = ("achievement__category", "achievement")
    search_fields = ("user__email", "achievement__title", "achievement__code")
    list_select_related = ("user", "achievement")
    ordering = ("-earned_at",)
    readonly_fields = ("created_at", "updated_at", "earned_at")


@admin.register(PointEvent)
class PointEventAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "source_type", "source_id", "created_at")
    list_filter = ("source_type",)
    search_fields = ("user__email", "reason", "note", "source_id")
    list_select_related = ("user",)
    ordering = ("-created_at",)
    # PointEvent is an append-only audit log; awards are written by achievements.services.
    readonly_fields = ("created_at",)
