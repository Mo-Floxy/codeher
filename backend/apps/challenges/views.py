"""Challenge API.

Django never executes learner code: `run/` and `submit/` delegate to
`apps.challenges.services`, which proxies to the isolated sandbox. A sandbox that
cannot be reached raises `RunnerUnavailable` (503) and is allowed to propagate, so
an unreachable runner is never rendered as a passing result.
"""

from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.achievements.models import PointEvent
from apps.challenges import services
from apps.challenges.filters import (
    DIFFICULTY_ANNOTATION,
    ORDERING_ALIASES,
    REAL_ORDERING_FIELDS,
    ChallengeFilter,
    ChallengeOrderingFilter,
)
from apps.challenges.models import Challenge, Submission
from apps.challenges.serializers import (
    ChallengeCardSerializer,
    ChallengeDetailSerializer,
    ExecutionRequestSerializer,
    LeaderboardEntrySerializer,
    SubmissionSerializer,
    normalise_results,
)
from apps.core.exceptions import ValidationFailed
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAuthenticatedOrReadOnly
from apps.core.throttling import SandboxThrottle
from apps.users.models import Profile

LEADERBOARD_LIMIT = 50


class ChallengeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """`/challenges/` — public catalogue, per-member execution endpoints."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    filterset_class = ChallengeFilter
    filter_backends = (DjangoFilterBackend, SearchFilter, ChallengeOrderingFilter)
    search_fields = ("title", "summary", "description", "slug")
    ordering_fields = REAL_ORDERING_FIELDS + tuple(ORDERING_ALIASES) + ("difficulty_rank",)
    # Accepts either the numeric id or the slug: /challenges/7/ and /challenges/two-sum/.
    lookup_value_regex = "[^/.]+"

    def get_queryset(self):
        user = self.request.user
        authenticated = bool(user and user.is_authenticated)
        is_manager = authenticated and (user.is_staff or getattr(user, "role", "") == "admin")

        queryset = Challenge.objects.all()
        if not is_manager:
            queryset = queryset.filter(is_published=True)

        queryset = queryset.annotate(difficulty_rank=DIFFICULTY_ANNOTATION)
        if authenticated:
            solved = Submission.objects.filter(challenge=OuterRef("pk"), user=user, passed=True)
            queryset = queryset.annotate(is_solved=Exists(solved))
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChallengeDetailSerializer
        return ChallengeCardSerializer

    def get_throttles(self):
        """Only the two endpoints that start a sandbox process are rate-limited.

        Putting the scope on the whole viewset instead would cap catalogue browsing
        at the same rate, which a user paging through the feed can reach without
        executing a single line of code.
        """
        if self.action in {"run", "submit"}:
            return [SandboxThrottle()]
        return super().get_throttles()

    def get_object(self):
        """Resolve the lookup as a primary key when numeric, otherwise as a slug."""
        value = str(self.kwargs[self.lookup_field])
        queryset = self.filter_queryset(self.get_queryset())
        if value.isdigit():
            obj = get_object_or_404(queryset, pk=int(value))
        else:
            obj = get_object_or_404(queryset, slug=value)
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=False, methods=["get"], url_path="leaderboard", permission_classes=(IsAuthenticatedOrReadOnly,))
    def leaderboard(self, request, *args, **kwargs):
        """Standings built from real Submission and PointEvent rows."""
        period = "weekly" if str(request.query_params.get("period", "weekly")).lower().startswith("week") else "alltime"
        limit = _positive_int(request.query_params.get("limit"), default=LEADERBOARD_LIMIT, maximum=100)
        rows = build_leaderboard(period=period, limit=limit)
        page = self.paginate_queryset(rows)
        if page is not None:
            serializer = LeaderboardEntrySerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        serializer = LeaderboardEntrySerializer(rows, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="submissions/me", permission_classes=(IsAuthenticated,))
    def my_submissions(self, request, *args, **kwargs):
        """History across every challenge, optionally `?challenge=<id>`."""
        queryset = (
            Submission.objects.filter(user=request.user)
            .select_related("challenge")
            .order_by("-created_at", "-id")
        )
        challenge = request.query_params.get("challenge")
        if challenge not in (None, ""):
            if not str(challenge).isdigit():
                raise ValidationFailed("The challenge filter must be a numeric id.")
            queryset = queryset.filter(challenge_id=int(challenge))
        page = self.paginate_queryset(queryset)
        serializer = SubmissionSerializer(page if page is not None else queryset, many=True, context=self.get_serializer_context())
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="submissions/me", permission_classes=(IsAuthenticated,))
    def my_challenge_submissions(self, request, pk=None):
        """`{best, recent}` for one challenge."""
        challenge = self.get_object()
        submissions = Submission.objects.filter(user=request.user, challenge=challenge).order_by("-created_at", "-id")
        best = services.personal_best(request.user, challenge)
        recent = submissions[:10]
        context = self.get_serializer_context()
        return Response(
            {
                "challenge": ChallengeCardSerializer(challenge, context=context).data,
                "best": SubmissionSerializer(best, context=context).data if best else None,
                "recent": SubmissionSerializer(recent, many=True, context=context).data,
                "total": submissions.count(),
            }
        )

    @action(detail=True, methods=["post"], permission_classes=(IsAuthenticated,))
    def run(self, request, pk=None):
        """Trial execution against the public cases. Never scored, never stored."""
        challenge = self.get_object()
        payload = ExecutionRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            report = services.run(
                request.user,
                challenge,
                code=payload.validated_data["code"],
                language=payload.validated_data.get("language") or "javascript",
            )
        except services.LanguageNotAllowed as exc:
            raise ValidationFailed(str(exc)) from exc

        error = report.get("error") or ""
        results = normalise_results(report.get("results"))
        return Response(
            {
                "ok": bool(report.get("ok", not error)) and not error,
                "results": results,
                "runtime_ms": int(report.get("runtime_ms") or 0),
                "error": error,
                "summary": report.get("summary")
                or {"passed": sum(1 for row in results if row["passed"]), "total": len(results)},
            }
        )

    @action(detail=True, methods=["post"], permission_classes=(IsAuthenticated,))
    def submit(self, request, pk=None):
        """Graded run over every case, including the hidden ones."""
        challenge = self.get_object()
        payload = ExecutionRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            submission, report = services.submit(
                request.user,
                challenge,
                code=payload.validated_data["code"],
                language=payload.validated_data.get("language") or "javascript",
            )
        except services.LanguageNotAllowed as exc:
            raise ValidationFailed(str(exc)) from exc
        except ValueError as exc:
            # A challenge without grading data cannot be scored; tell the client.
            raise ValidationFailed(str(exc)) from exc

        public_names = set(challenge.test_cases.filter(is_public=True).values_list("name", flat=True))
        data = SubmissionSerializer(submission, context=self.get_serializer_context()).data
        data["ok"] = submission.passed
        data["first_solve_bonus"] = bool(submission.is_first_solve)
        data["results"] = normalise_results(report.get("results"), reveal_for=public_names)
        data["summary"] = {"passed": submission.passed_count, "total": submission.total_tests}
        data["runtime_ms"] = int(report.get("runtime_ms") or submission.runtime_ms or 0)
        data["error"] = report.get("error") or submission.error
        return Response(data, status=status.HTTP_201_CREATED)


def build_leaderboard(period="alltime", limit=LEADERBOARD_LIMIT):
    """Rank members by XP earned and distinct challenges solved in the period."""
    since = timezone.now() - timedelta(days=7) if period == "weekly" else None

    points_qs = PointEvent.objects.all()
    if since:
        points_qs = points_qs.filter(created_at__gte=since)
    points_by_user = {
        row["user_id"]: int(row["total"] or 0)
        for row in points_qs.values("user_id").annotate(total=Sum("amount")).order_by()
        if row["total"]
    }

    solved_qs = Submission.objects.filter(passed=True)
    if since:
        solved_qs = solved_qs.filter(created_at__gte=since)
    solved_by_user = {
        row["user_id"]: int(row["solved"])
        for row in solved_qs.values("user_id").annotate(solved=Count("challenge", distinct=True)).order_by()
        if row["solved"]
    }

    user_ids = set(points_by_user) | set(solved_by_user)
    rows = []
    for profile in Profile.objects.filter(user_id__in=user_ids, user__is_active=True).select_related("user"):
        points = points_by_user.get(profile.user_id, 0)
        solved = solved_by_user.get(profile.user_id, 0)
        if not points and not solved:
            continue
        rows.append({"user": profile.user, "profile": profile, "points": points, "solved": solved})

    rows.sort(key=lambda row: (-row["points"], -row["solved"], row["user"].display_name.lower()))
    rows = rows[: max(1, limit)]
    return [dict(row, rank=index + 1) for index, row in enumerate(rows)]


def _positive_int(raw, default, maximum):
    try:
        value = int(str(raw))
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, maximum)
