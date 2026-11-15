"""Challenge serialisers.

Grading data never leaves the server: `ChallengeTestCase` rows are only ever
serialised when they are explicitly marked `is_public`, and submission payloads
carry counts instead of runner reports so a hidden case's expected value cannot
be read from a learner's own history.
"""

from django.conf import settings
from rest_framework import serializers

from apps.challenges.models import Challenge, ChallengeTestCase, Submission


def absolute_media_url(request, file_field):
    """Absolute URL for a stored file, or None when nothing is attached."""
    if not file_field:
        return None
    try:
        url = file_field.url
    except (ValueError, NotImplementedError):
        return None
    if not url:
        return None
    return request.build_absolute_uri(url) if request is not None else url


def public_user_payload(user, request=None, profile=None):
    """Compact member shape used by leaderboards and notification actors.

    Email is deliberately absent: leaderboards are readable by any member.
    """
    if user is None:
        return None
    profile = profile if profile is not None else getattr(user, "profile", None)
    avatar = absolute_media_url(request, getattr(profile, "avatar", None)) if profile else None
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "avatar": avatar,
        "role": user.role,
        "date_joined": user.date_joined,
    }


class ChallengeCardSerializer(serializers.ModelSerializer):
    """List card: metadata only, no starter bodies and no test rows."""

    excerpt = serializers.CharField(source="summary", read_only=True)
    languages = serializers.SerializerMethodField()
    is_solved = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = (
            "id",
            "slug",
            "title",
            "summary",
            "excerpt",
            "difficulty",
            "category",
            "points",
            "topics",
            "languages",
            "time_limit_ms",
            "submission_count",
            "accepted_count",
            "pass_rate_percent",
            "is_solved",
            "position",
            "created_at",
        )

    def get_languages(self, obj):
        return list(obj.allowed_languages or ["javascript"])

    def get_is_solved(self, obj):
        # Annotated by ChallengeViewSet only for authenticated requests.
        return bool(getattr(obj, "is_solved", False))


class PublicTestCaseSerializer(serializers.ModelSerializer):
    """A sample case the brief already shows the learner."""

    input = serializers.JSONField(source="args", read_only=True)

    class Meta:
        model = ChallengeTestCase
        fields = ("id", "name", "input", "expected", "position")


class ChallengeDetailSerializer(ChallengeCardSerializer):
    starter_code = serializers.SerializerMethodField()
    public_tests = serializers.SerializerMethodField()
    test_count = serializers.SerializerMethodField()

    class Meta(ChallengeCardSerializer.Meta):
        fields = ChallengeCardSerializer.Meta.fields + (
            "description",
            "function_name",
            "examples",
            "hints",
            "starter_code",
            "public_tests",
            "test_count",
            "memory_limit_mb",
            "allowed_languages",
        )

    def get_starter_code(self, obj):
        raw = obj.starter_code if isinstance(obj.starter_code, dict) else {}
        return {
            "javascript": raw.get("javascript", "") or "",
            "python": raw.get("python", "") or "",
        }

    def get_public_tests(self, obj):
        cases = obj.test_cases.filter(is_public=True)
        return PublicTestCaseSerializer(cases, many=True, context=self.context).data

    def get_test_count(self, obj):
        # A count only — the hidden cases themselves stay server-side.
        return obj.test_cases.count()


class ChallengeBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ("id", "slug", "title", "difficulty", "category", "points")


class ExecutionRequestSerializer(serializers.Serializer):
    """Body of `run/` and `submit/`: `{language, code}`."""

    language = serializers.CharField(required=False, allow_blank=True, max_length=20)
    code = serializers.CharField(allow_blank=False, max_length=settings.RUNNER_MAX_CODE_BYTES)

    def validate_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Write some code before sending it to the sandbox.")
        if len(value.encode("utf-8")) > settings.RUNNER_MAX_CODE_BYTES:
            raise serializers.ValidationError(
                f"Your code is larger than the {settings.RUNNER_MAX_CODE_BYTES} byte sandbox limit."
            )
        return value

    def validate_language(self, value):
        return (value or "javascript").strip().lower()


class SubmissionSerializer(serializers.ModelSerializer):
    challenge = ChallengeBriefSerializer(read_only=True)
    challenge_id = serializers.PrimaryKeyRelatedField(source="challenge", read_only=True)
    first_solve_bonus = serializers.BooleanField(source="is_first_solve", read_only=True)
    failed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id",
            "challenge",
            "challenge_id",
            "language",
            "code",
            "passed_count",
            "failed_count",
            "total_tests",
            "passed",
            "score",
            "points_awarded",
            "first_solve_bonus",
            "is_first_solve",
            "runtime_ms",
            "error",
            "created_at",
        )
        # runner_report is intentionally absent: it embeds hidden expectations.


RESULT_FIELDS = ("name", "passed", "expected", "actual", "error")


def normalise_results(results, reveal_for=None):
    """Trim runner rows to the documented result shape.

    `reveal_for=None` keeps expected/actual (used by `run/`, which only executes
    public cases). Pass a set of public case names to blank the expectations of
    every other case, so a graded report cannot leak hidden assertions.
    """
    normalised = []
    for item in results or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "Test case")
        row = {
            "name": name,
            "passed": bool(item.get("passed")),
            "error": item.get("error") or None,
        }
        visible = reveal_for is None or name in reveal_for
        row["expected"] = item.get("expected") if visible else None
        row["actual"] = item.get("actual") if visible else None
        normalised.append(row)
    return normalised


class LeaderboardEntrySerializer(serializers.Serializer):
    """One standings row, built from PointEvent and Submission aggregates."""

    rank = serializers.IntegerField()
    user = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    points = serializers.IntegerField()
    solved_count = serializers.IntegerField(source="solved")

    def get_user(self, obj):
        return public_user_payload(obj["user"], self.context.get("request"), obj.get("profile"))

    def get_display_name(self, obj):
        return obj["user"].display_name or obj["user"].username

    def get_avatar(self, obj):
        profile = obj.get("profile")
        return absolute_media_url(self.context.get("request"), getattr(profile, "avatar", None)) if profile else None
