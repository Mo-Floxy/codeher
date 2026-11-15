from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "title", "actor", "unread", "read_at", "archived_at", "created_at")
    list_filter = ("kind",)
    search_fields = ("title", "body", "recipient__email", "dedupe_key")
    list_select_related = ("recipient", "actor")
    ordering = ("-created_at",)
    # Delivery/stamp fields are set by the notification fan-out, not edited by hand.
    readonly_fields = ("created_at", "updated_at", "read_at", "archived_at", "dedupe_key")

    @admin.display(description="unread", boolean=True, ordering="read_at")
    def unread(self, obj):
        return obj.is_unread
