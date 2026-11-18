"""Serializers for the community API.

Write paths are deliberately thin here: every mutation that touches counters,
XP or notifications is executed by apps.community.services from the view layer.
"""

from rest_framework import serializers

from apps.core.media import MediaUrlField
from apps.courses.models import Course
from apps.community.models import Comment, Post, Project, Report


def _media_url(file_field, request):
    """Absolute URL for an uploaded file, or None — never a fake path."""
    if not file_field or request is None:
        return None
    return request.build_absolute_uri(file_field.url)


class AuthorSerializer(serializers.Serializer):
    """The author block embedded in every post/project payload."""

    id = serializers.IntegerField(source="pk")
    display_name = serializers.CharField()
    username = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    def get_avatar(self, user):
        profile = getattr(user, "profile", None)
        if profile is None or not profile.avatar:
            return None
        return _media_url(profile.avatar, self.context.get("request"))

    def get_level(self, user):
        profile = getattr(user, "profile", None)
        return profile.level if profile is not None else None


class TagListField(serializers.ListField):
    child = serializers.CharField(max_length=64, trim_whitespace=True)

    def to_representation(self, value):
        return super().to_representation(list(value or []))


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="user", read_only=True)
    type = serializers.ChoiceField(choices=Post.TYPE_CHOICES, required=False)
    title = serializers.CharField(min_length=3, max_length=220)
    body = serializers.CharField(min_length=1, max_length=8000)
    tags = TagListField(required=False)
    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), required=False, allow_null=True
    )
    helpful_comment = serializers.PrimaryKeyRelatedField(read_only=True)
    is_solved = serializers.BooleanField(read_only=True)
    liked = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "type", "title", "body", "tags", "course", "status", "author",
            "is_solved", "helpful_comment", "likes_count", "comments_count",
            "bookmarks_count", "liked", "bookmarked", "last_activity_at", "created_at",
        )
        read_only_fields = (
            "status", "likes_count", "comments_count", "bookmarks_count",
            "last_activity_at", "created_at",
        )

    def _flag(self, obj, name):
        # Set by the viewset's Exists() annotation when the viewer is known.
        return bool(getattr(obj, name, False))

    def get_liked(self, obj):
        return self._flag(obj, "liked")

    def get_bookmarked(self, obj):
        return self._flag(obj, "bookmarked")


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="user", read_only=True)
    body = serializers.CharField(min_length=1, max_length=4000)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "post", "parent", "body", "author", "likes_count", "replies", "created_at")
        read_only_fields = ("post", "likes_count", "created_at")

    def get_replies(self, obj):
        # The view prefetches one level only, so .all() stays cache-friendly.
        children = obj.replies.select_related("user__profile").order_by("created_at")
        return CommentSerializer(children, many=True, context=self.context).data


class ProjectSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="user", read_only=True)
    title = serializers.CharField(min_length=3, max_length=200)
    description = serializers.CharField(min_length=1, max_length=4000)
    technologies = TagListField(required=False)
    # Members may draft or publish; "hidden" belongs to moderation only. The field
    # stays a plain CharField so rows an admin hid still serialise without error.
    status = serializers.CharField(required=False)
    # Either a file in this request or the URL /api/uploads/ returned; rendered back
    # as an absolute URL, and None when no image is attached.
    screenshot = MediaUrlField(required=False, allow_null=True)
    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), required=False, allow_null=True
    )
    liked = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id", "title", "description", "technologies", "repo_url", "live_url",
            "screenshot", "course", "status", "author", "likes_count", "comments_count",
            "bookmarks_count", "views_count", "trending_score", "liked", "bookmarked",
            "last_activity_at", "created_at",
        )
        read_only_fields = (
            "likes_count", "comments_count", "bookmarks_count", "views_count",
            "trending_score", "last_activity_at", "created_at",
        )

    def validate_status(self, value):
        if value not in ("draft", "published"):
            raise serializers.ValidationError("Status must be either draft or published.")
        return value

    def _flag(self, obj, name):
        return bool(getattr(obj, name, False))

    def get_liked(self, obj):
        return self._flag(obj, "liked")

    def get_bookmarked(self, obj):
        return self._flag(obj, "bookmarked")


class ReportCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Report.REASON_CHOICES)
    details = serializers.CharField(required=False, allow_blank=True, max_length=2000, default="")


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ("id", "target_type", "reason", "details", "status", "created_at")
        read_only_fields = fields
