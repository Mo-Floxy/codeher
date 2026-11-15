"""Administrative serializers.

Kept separate from the public serializers because the admin tables expose draft and
hidden rows, counters and ownership fields a learner must never write.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.challenges.models import Challenge
from apps.community.models import Report
from apps.core.models import Announcement, Event, Testimonial
from apps.courses.serializers import (
    CourseModuleWriteSerializer,
    CourseWriteSerializer,
    LearningPathWriteSerializer,
    LessonWriteSerializer,
    QuizWriteSerializer,
)
from apps.mentorship.models import MentorProfile

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    total_xp = serializers.IntegerField(source="profile.total_xp", read_only=True)
    level = serializers.IntegerField(source="profile.level", read_only=True)
    current_streak = serializers.IntegerField(source="profile.current_streak", read_only=True)
    enrollments = serializers.IntegerField(read_only=True)
    posts = serializers.IntegerField(read_only=True)
    submissions = serializers.IntegerField(read_only=True)
    is_mentor = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "display_name",
            "role",
            "is_active",
            "is_staff",
            "is_email_verified",
            "is_mentor",
            "date_joined",
            "last_login",
            "total_xp",
            "level",
            "current_streak",
            "enrollments",
            "posts",
            "submissions",
        ]
        read_only_fields = fields

    def get_is_mentor(self, user):
        return MentorProfile.objects.filter(user=user, is_approved=True).exists()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role", "is_active", "display_name"]

    def validate_role(self, value):
        if value not in dict(User.ROLE_CHOICES):
            raise serializers.ValidationError("Unsupported role.")
        return value


class ChallengeWriteSerializer(serializers.ModelSerializer):
    test_cases = serializers.JSONField(required=False, write_only=True)

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "difficulty",
            "category",
            "function_name",
            "starter_code",
            "examples",
            "hints",
            "topics",
            "points",
            "allowed_languages",
            "time_limit_ms",
            "memory_limit_mb",
            "is_published",
            "position",
            "submission_count",
            "accepted_count",
            "test_cases",
        ]
        read_only_fields = ["id", "submission_count", "accepted_count"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["test_cases"] = [
            {
                "id": case.pk,
                "name": case.name,
                "args": case.args,
                "expected": case.expected,
                "is_public": case.is_public,
                "position": case.position,
            }
            for case in instance.test_cases.all()
        ]
        return data

    def _replace_cases(self, challenge, cases):
        from apps.challenges.models import ChallengeTestCase

        challenge.test_cases.all().delete()
        for index, case in enumerate(cases, start=1):
            ChallengeTestCase.objects.create(
                challenge=challenge,
                name=case.get("name") or f"Test {index}",
                args=case.get("args") or [],
                expected=case.get("expected"),
                is_public=bool(case.get("is_public", False)),
                position=case.get("position", index),
            )

    def create(self, validated_data):
        cases = validated_data.pop("test_cases", [])
        challenge = Challenge.objects.create(**validated_data)
        self._replace_cases(challenge, cases)
        return challenge

    def update(self, instance, validated_data):
        cases = validated_data.pop("test_cases", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if cases is not None:
            self._replace_cases(instance, cases)
        return instance


class MentorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    active_mentees = serializers.SerializerMethodField()

    class Meta:
        model = MentorProfile
        fields = [
            "id",
            "user",
            "user_email",
            "display_name",
            "username",
            "expertise",
            "bio",
            "current_role",
            "company",
            "years_experience",
            "availability_note",
            "preferred_slots",
            "languages",
            "capacity",
            "active_mentees",
            "is_approved",
            "is_accepting",
            "matched_count",
            "rating_average",
        ]
        read_only_fields = ["matched_count", "rating_average"]

    def get_active_mentees(self, profile):
        from apps.mentorship.models import MentorshipRequest

        return MentorshipRequest.objects.filter(
            mentor=profile.user, status=MentorshipRequest.STATUS_ACCEPTED
        ).count()


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "body",
            "audience",
            "course",
            "learning_path",
            "created_by",
            "created_by_name",
            "sent_at",
            "recipient_count",
            "created_at",
        ]
        read_only_fields = ["created_by", "sent_at", "recipient_count"]

    def get_created_by_name(self, announcement):
        return announcement.created_by.display_name if announcement.created_by else ""


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ["id", "user", "attribution", "role", "quote", "course", "is_published", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "description", "kind", "starts_at", "ends_at", "url", "course", "is_published"]


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    target_title = serializers.SerializerMethodField()
    target_author = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "target_type",
            "reason",
            "details",
            "status",
            "action_taken",
            "resolution_note",
            "created_at",
            "resolved_at",
            "created_by",
            "created_by_name",
            "resolved_by_name",
            "target_title",
            "target_author",
            "post",
            "comment",
            "project",
        ]
        read_only_fields = fields

    def get_created_by_name(self, report):
        return report.created_by.display_name

    def get_resolved_by_name(self, report):
        return report.resolved_by.display_name if report.resolved_by else None

    def get_target_title(self, report):
        target = report.target
        return getattr(target, "title", "") if target else ""

    def get_target_author(self, report):
        target = report.target
        if target is None:
            return None
        return {
            "id": target.user_id,
            "display_name": target.user.display_name,
            "email": target.user.email,
        }


__all__ = [
    "AdminUserSerializer",
    "AdminUserUpdateSerializer",
    "AnnouncementSerializer",
    "ChallengeWriteSerializer",
    "CourseModuleWriteSerializer",
    "CourseWriteSerializer",
    "EventSerializer",
    "LearningPathWriteSerializer",
    "LessonWriteSerializer",
    "MentorProfileSerializer",
    "QuizWriteSerializer",
    "ReportSerializer",
    "TestimonialSerializer",
]
