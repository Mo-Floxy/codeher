"""Gamification API.

Progress, XP and rankings are read from stored rows through
`apps.achievements.services`; nothing here trusts a client-supplied count.
"""

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.achievements import services
from apps.achievements.models import Achievement, PointEvent, UserAchievement
from apps.achievements.serializers import (
    AchievementCatalogueSerializer,
    GoalProgressSerializer,
    LeaderboardRowSerializer,
    PointEventSerializer,
    UserAchievementSerializer,
    WeeklyGoalInputSerializer,
)
from apps.core.pagination import StandardResultsSetPagination
from apps.users.models import Profile

LEADERBOARD_LIMIT = 50


def ensure_profile(user):
    """Members always have a profile; create one defensively if the row is missing."""
    profile = getattr(user, "profile", None)
    if profile is None:
        profile = Profile.objects.get_or_create(user=user)[0]
    return profile


class AchievementViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """`/achievements/` catalogue plus the member's own progress surfaces."""

    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    serializer_class = AchievementCatalogueSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = {"category": ["exact"], "metric": ["exact"]}
    search_fields = ("title", "description", "code")
    ordering_fields = ("requirement_value", "title", "category", "xp_reward", "id")

    def get_queryset(self):
        return Achievement.objects.filter(is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        # Only the catalogue page needs live counters and the earned map.
        if self.action == "list" and user and user.is_authenticated and "earned" not in context:
            awards = UserAchievement.objects.filter(user=user).values_list("achievement_id", "earned_at")
            context["earned"] = dict(awards)
            context["metrics"] = services.compute_metrics(user)
        return context

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request, *args, **kwargs):
        """Earned badges and the member's XP totals."""
        profile = ensure_profile(request.user)
        total_xp = int(profile.total_xp or 0)
        level = int(profile.level or 0) or services.level_for_xp(total_xp)
        awards = UserAchievement.objects.filter(user=request.user).select_related("achievement").order_by("-earned_at")
        context = self.get_serializer_context()
        events = PointEvent.objects.filter(user=request.user).order_by("-created_at")[:10]
        return Response(
            {
                "earned": UserAchievementSerializer(awards, many=True, context=context).data,
                "earned_count": len(awards),
                "catalogue_count": self.get_queryset().count(),
                "xp": {
                    "total": total_xp,
                    "awarded": services.xp_total(request.user),
                    "level": level,
                    "next_level_xp": services.next_level_xp(level),
                    "progress_percent": services.level_progress(total_xp, level),
                },
                "streak": {
                    "current": profile.current_streak,
                    "longest": profile.longest_streak,
                    "last_activity_date": profile.last_activity_date,
                },
                "metrics": services.compute_metrics(request.user),
                "recent_awards": PointEventSerializer(events, many=True, context=context).data,
            }
        )

    @action(detail=False, methods=["get"], url_path="leaderboard")
    def leaderboard(self, request, *args, **kwargs):
        """Rankings delegated to the service; only the users are serialised here."""
        scope = "streak" if str(request.query_params.get("scope", "xp")).lower() == "streak" else "xp"
        period = "weekly" if str(request.query_params.get("period", "alltime")).lower().startswith("week") else "alltime"
        limit = _positive_int(request.query_params.get("limit"), default=LEADERBOARD_LIMIT, maximum=100)

        rows = services.leaderboard(scope=scope, period=period, limit=limit)
        profiles = Profile.objects.filter(user_id__in=[row["user"].pk for row in rows]).select_related("user")
        by_user = {profile.user_id: profile for profile in profiles}
        rows = [dict(row, profile=by_user.get(row["user"].pk)) for row in rows]

        context = self.get_serializer_context()
        context["scope"] = scope
        context["period"] = period
        page = self.paginate_queryset(rows)
        serializer = LeaderboardRowSerializer(page if page is not None else rows, many=True, context=context)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get", "patch"], url_path="me/goals")
    def goals(self, request, *args, **kwargs):
        """Weekly study goal: read progress, PATCH the target."""
        profile = ensure_profile(request.user)
        if request.method.lower() == "patch":
            payload = WeeklyGoalInputSerializer(data=request.data)
            payload.is_valid(raise_exception=True)
            profile.weekly_goal_minutes = payload.validated_data["weekly_goal_minutes"]
            profile.save(update_fields=["weekly_goal_minutes", "updated_at"])

        target = int(profile.weekly_goal_minutes or 0)
        actual = int(services.weekly_minutes(request.user))
        progress = 0 if target <= 0 else max(0, min(100, round(100 * actual / target)))
        payload = {
            "target_minutes": target,
            "weekly_goal_minutes": target,
            "actual_minutes": actual,
            "achieved": bool(target) and actual >= target,
            "progress_percent": progress,
            "percent": progress,
            "remaining_minutes": max(0, target - actual),
        }
        return Response(GoalProgressSerializer(payload).data)

    @action(detail=False, methods=["get"], url_path="me/levels")
    def levels(self, request, *args, **kwargs):
        """The published level table with the learner's current position marked."""
        profile = ensure_profile(request.user)
        total_xp = int(profile.total_xp or 0)
        current = services.level_for_xp(total_xp)
        rows = [
            {
                "level": index + 1,
                "title": "Level {}".format(index + 1),
                "min_xp": threshold,
                "is_current": index + 1 == current,
                "is_reached": total_xp >= threshold,
            }
            for index, threshold in enumerate(settings.LEVEL_THRESHOLDS)
        ]
        return Response(
            {
                "levels": rows,
                "current_level": current,
                "level": current,
                "total_xp": total_xp,
                "next_level_xp": services.next_level_xp(current),
                "progress_percent": services.level_progress(total_xp, current),
            }
        )


def _positive_int(raw, default, maximum):
    try:
        value = int(str(raw))
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, maximum)
