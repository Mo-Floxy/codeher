from django.contrib import admin

from apps.core.models import Announcement, Event, Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("attribution", "role", "user", "course", "is_published", "created_at")
    list_filter = ("is_published", "course")
    search_fields = ("attribution", "role", "quote")
    list_select_related = ("user", "course")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "starts_at", "ends_at", "course", "is_published")
    list_filter = ("kind", "is_published", "course")
    search_fields = ("title", "description", "url")
    list_select_related = ("course",)
    ordering = ("starts_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "course", "learning_path", "created_by", "sent_at", "recipient_count",
                    "created_at")
    list_filter = ("audience", "course", "learning_path")
    search_fields = ("title", "body")
    list_select_related = ("course", "learning_path", "created_by")
    ordering = ("-created_at",)
    # sent_at and recipient_count are stamped when the announcement fans out into notifications.
    readonly_fields = ("created_at", "updated_at", "sent_at", "recipient_count")
