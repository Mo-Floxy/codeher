from django.contrib import admin

from apps.community.models import Comment, Engagement, Post, Project, Report


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("user", "parent", "body", "status", "likes_count")
    readonly_fields = ("likes_count",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
    list_display = ("title", "user", "type", "status", "likes_count", "comments_count", "solved", "last_activity_at")
    list_filter = ("status", "type")
    search_fields = ("title", "body", "user__email")
    list_select_related = ("user",)
    ordering = ("-last_activity_at",)
    # Engagement counters are denormalised from Engagement rows by the services layer.
    readonly_fields = ("created_at", "updated_at", "likes_count", "comments_count", "bookmarks_count")

    @admin.display(description="solved", boolean=True, ordering="helpful_comment")
    def solved(self, obj):
        return obj.is_solved


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_body", "post", "user", "status", "likes_count", "created_at")
    list_filter = ("status", "post__type")
    search_fields = ("body", "post__title", "user__email")
    list_select_related = ("post", "user", "parent")
    ordering = ("created_at",)
    readonly_fields = ("created_at", "updated_at", "likes_count")

    @admin.display(description="body", ordering="body")
    def short_body(self, obj):
        return obj.body[:60]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "trending_score", "likes_count", "views_count", "last_activity_at")
    list_filter = ("status", "course")
    search_fields = ("title", "description", "user__email")
    list_select_related = ("user", "course")
    ordering = ("-trending_score", "-last_activity_at")
    # Counters and trending_score are recomputed by community.services.
    readonly_fields = ("created_at", "updated_at", "likes_count", "comments_count", "bookmarks_count", "views_count",
                       "trending_score")


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "post", "project", "comment", "created_at")
    list_filter = ("kind",)
    search_fields = ("user__email", "post__title", "project__title")
    list_select_related = ("user", "post", "project", "comment")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("created_by", "target_type", "reason", "status", "resolved_by", "resolved_at", "created_at")
    list_filter = ("status", "target_type", "reason")
    search_fields = ("details", "created_by__email", "resolution_note")
    list_select_related = ("created_by", "resolved_by")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
