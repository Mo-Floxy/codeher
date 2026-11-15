"""Gamification serialisers.

Badge progress is always derived from the live counters in
`apps.achievements.services.compute_metrics`, never from anything the client sends.
"""

from rest_framework import serializers

from apps.achievements.models import Achievement, PointEvent, UserAchievement

MAX_WEEKLY_MINUTES = 7 * 24 * 60


def avatar_url(request, profile):
    """Absolute avatar URL, or None when no image is stored."""
    avatar = getattr(profile, "avatar", None) if profile else None
    if not avatar:
        return None
    try:
        url = avatar.url
    except (ValueError, NotImplementedError):
        return None
    if not url:
        return None
    return request.build_absolute_uri(url) if request is not None else url


def member_payload(user, request=None, profile=None):
    """Compact public member shape used by rankings. Email stays private."""
    if user is None:
        return None
    profile = profile if profile is not None else getattr(user, "profile", None)
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "avatar": avatar_url(request, profile),
        "role": user.role,
        "date_joined": user.date_joined,
    }


class AchievementBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = (
            "id",
            "code",
            "title",
            "description",
            "category",
            "metric",
            "requirement_value",
            "icon",
            "color",
            "xp_reward",
        )


class AchievementCatalogueSerializer(serializers.ModelSerializer):
    """Catalogue row annotated with the requesting member's own progress.

    The view supplies `metrics` (live counters) and `earned` (achievement id ->
    earned_at) in the serializer context so a whole page costs one query each.
    """

    is_earned = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    earned_at = serializers.SerializerMethodField()
    requirement = serializers.SerializerMethodField()
    requirement_text = serializers.SerializerMethodField()
    metric_label = serializers.CharField(source="get_metric_display", read_only=True)

    class Meta:
        model = Achievement
        fields = AchievementBriefSerializer.Meta.fields + (
            "is_earned",
            "current_value",
            "progress_percent",
            "earned_at",
            "requirement",
            "requirement_text",
            "metric_label",
        )

    def get_is_earned(self, obj):
        return obj.pk in self._earned()

    def get_current_value(self, obj):
        return int(self._metrics().get(obj.metric, 0) or 0)

    def get_progress_percent(self, obj):
        target = obj.requirement_value or 1
        return max(0, min(100, round(100 * self.get_current_value(obj) / target)))

    def get_earned_at(self, obj):
        return self._earned().get(obj.pk)

    def get_requirement(self, obj):
        return "{} {}".format(obj.requirement_value, obj.get_metric_display().lower())

    def get_requirement_text(self, obj):
        return "{} — {} to unlock".format(obj.description, self.get_requirement(obj))

    def _earned(self):
        return self.context.get("earned") or {}

    def _metrics(self):
        return self.context.get("metrics") or {}


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementBriefSerializer(read_only=True)
    badge = serializers.CharField(source="achievement.code", read_only=True)
    title = serializers.CharField(source="achievement.title", read_only=True)
    description = serializers.CharField(source="achievement.description", read_only=True)
    icon = serializers.CharField(source="achievement.icon", read_only=True)
    color = serializers.CharField(source="achievement.color", read_only=True)

    class Meta:
        model = UserAchievement
        fields = ("id", "achievement", "badge", "title", "description", "icon", "color", "earned_at")


class PointEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointEvent
        fields = ("id", "amount", "reason", "source_type", "source_id", "note", "created_at")


class WeeklyGoalInputSerializer(serializers.Serializer):
    """PATCH body for `/achievements/me/goals/`."""

    weekly_goal_minutes = serializers.IntegerField(min_value=0, max_value=MAX_WEEKLY_MINUTES)


class GoalProgressSerializer(serializers.Serializer):
    """Read model for the weekly goal, computed from real activity rows."""

    target_minutes = serializers.IntegerField()
    weekly_goal_minutes = serializers.IntegerField()
    actual_minutes = serializers.IntegerField()
    achieved = serializers.BooleanField()
    progress_percent = serializers.IntegerField()
    percent = serializers.IntegerField()
    remaining_minutes = serializers.IntegerField()


class LeaderboardRowSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    value = serializers.IntegerField()
    total_xp = serializers.SerializerMethodField()
    current_streak = serializers.SerializerMethodField()

    def get_user(self, obj):
        return member_payload(obj["user"], self.context.get("request"), obj.get("profile"))

    def get_display_name(self, obj):
        return obj["user"].display_name or obj["user"].username

    def get_avatar(self, obj):
        return avatar_url(self.context.get("request"), obj.get("profile"))

    def get_total_xp(self, obj):
        return int(getattr(obj.get("profile"), "total_xp", 0) or 0)

    def get_current_streak(self, obj):
        return int(getattr(obj.get("profile"), "current_streak", 0) or 0)
