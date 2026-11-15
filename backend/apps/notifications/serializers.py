"""Notification serialisers.

Every row is addressed to a single recipient, and the API scopes every route to
that recipient, so the serialiser is a plain projection of the model.
"""

from rest_framework import serializers

from apps.notifications.models import Notification


def avatar_url(request, user):
    """Absolute avatar URL for a member, or None when they have no image."""
    if request is None or user is None:
        return None
    profile = getattr(user, "profile", None)
    avatar = getattr(profile, "avatar", None) if profile else None
    if not avatar:
        return None
    try:
        url = avatar.url
    except (ValueError, NotImplementedError):
        return None
    return request.build_absolute_uri(url) if url else None


def actor_payload(user, request=None):
    if user is None:
        return None
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "avatar": avatar_url(request, user),
    }


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    is_unread = serializers.BooleanField(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    # `link` is the contract field; `url` and `message` are aliases the web client reads.
    url = serializers.CharField(source="link", read_only=True)
    message = serializers.CharField(source="body", read_only=True)
    actor = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "kind_label",
            "title",
            "body",
            "message",
            "link",
            "url",
            "actor",
            "is_read",
            "is_unread",
            "read_at",
            "archived_at",
            "created_at",
            "updated_at",
        )

    def get_is_read(self, obj):
        return obj.read_at is not None

    def get_actor(self, obj):
        if obj.actor_id is None:
            return None
        return actor_payload(obj.actor, self.context.get("request"))
