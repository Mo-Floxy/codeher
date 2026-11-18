"""Serializers for accounts and profiles.

The public profile serializer drops every field the owner chose to keep private,
so visibility flags are enforced server-side rather than by hiding markup.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.core.media import MediaUrlField
from apps.users.models import Profile, User


def avatar_url(profile, request):
    if profile is None or not profile.avatar:
        return None
    url = profile.avatar.url
    return request.build_absolute_uri(url) if request is not None else url


def safe_profile(user):
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return user.profile
    except ObjectDoesNotExist:
        return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "display_name", "role", "is_staff", "date_joined"]
        read_only_fields = ["id", "username", "email", "role", "is_staff", "date_joined"]


class UserBriefSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "avatar", "headline", "level"]

    def get_avatar(self, user):
        return avatar_url(safe_profile(user), self.context.get("request"))

    def get_headline(self, user):
        profile = safe_profile(user)
        return profile.headline if profile else ""

    def get_level(self, user):
        profile = safe_profile(user)
        return profile.level if profile else 1


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # The settings page uploads through /api/uploads/ and then saves the URL it was
    # handed, so a plain ImageField rejected every one of those saves.
    avatar = MediaUrlField(use_url=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source="user.date_joined", read_only=True)
    level_progress_percent = serializers.SerializerMethodField()
    next_level_xp = serializers.SerializerMethodField()
    completed_course_count = serializers.SerializerMethodField()
    badge_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "avatar",
            "avatar_url",
            "headline",
            "bio",
            "interests",
            "skill_level",
            "learning_technologies",
            "timezone_name",
            "country",
            "is_profile_public",
            "show_email",
            "show_projects",
            "show_badges",
            "show_streak",
            "total_xp",
            "level",
            "level_progress_percent",
            "next_level_xp",
            "current_streak",
            "longest_streak",
            "last_activity_date",
            "weekly_goal_minutes",
            "followers_count",
            "following_count",
            "joined_at",
            "completed_course_count",
            "badge_count",
        ]
        read_only_fields = [
            "total_xp",
            "level",
            "current_streak",
            "longest_streak",
            "last_activity_date",
        ]

    def get_avatar_url(self, profile):
        return avatar_url(profile, self.context.get("request"))

    def get_level_progress_percent(self, profile):
        from apps.achievements.services import level_progress

        return level_progress(profile.total_xp, profile.level)

    def get_next_level_xp(self, profile):
        from apps.achievements.services import next_level_xp

        return next_level_xp(profile.level)

    def get_completed_course_count(self, profile):
        from apps.progress.models import Enrollment

        return Enrollment.objects.filter(user=profile.user, is_completed=True).count()

    def get_badge_count(self, profile):
        from apps.achievements.models import UserAchievement

        return UserAchievement.objects.filter(user=profile.user).count()

    def get_followers_count(self, profile):
        return profile.user.followers_set.count()

    def get_following_count(self, profile):
        return profile.user.following_set.count()


class PublicProfileSerializer(serializers.ModelSerializer):
    """What a stranger may see. Private values are stripped server-side."""

    username = serializers.CharField(source="user.username")
    display_name = serializers.CharField(source="user.display_name")
    avatar_url = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source="user.date_joined")
    email = serializers.SerializerMethodField()
    current_streak = serializers.IntegerField(read_only=True)
    badge_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "username",
            "display_name",
            "avatar_url",
            "email",
            "headline",
            "bio",
            "interests",
            "skill_level",
            "learning_technologies",
            "country",
            "total_xp",
            "level",
            "current_streak",
            "badge_count",
            "project_count",
            "followers_count",
            "following_count",
            "joined_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        viewer = getattr(request, "user", None)
        is_self = bool(viewer and viewer.is_authenticated and viewer.pk == instance.user_id)
        is_admin = bool(viewer and getattr(viewer, "is_admin", False))
        data["is_self"] = is_self

        if is_self or is_admin:
            return data

        if not instance.is_profile_public:
            restricted = {}
            for key in ("id", "user_id", "username", "display_name", "avatar_url", "joined_at"):
                restricted[key] = data.get(key)
            restricted["is_private"] = True
            return restricted

        if not instance.show_email:
            data["email"] = None
        if not instance.show_badges:
            data["badge_count"] = None
        if not instance.show_streak:
            data["current_streak"] = None
        if not instance.show_projects:
            data["project_count"] = None
        return data

    def get_avatar_url(self, profile):
        return avatar_url(profile, self.context.get("request"))

    def get_email(self, profile):
        return profile.user.email

    def get_badge_count(self, profile):
        from apps.achievements.models import UserAchievement

        return UserAchievement.objects.filter(user=profile.user).count()

    def get_followers_count(self, profile):
        return profile.user.followers_set.count()

    def get_following_count(self, profile):
        return profile.user.following_set.count()

    def get_project_count(self, profile):
        from apps.community.models import Project

        return Project.objects.filter(user=profile.user, status="published").count()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="That email is already registered.")]
    )
    username = serializers.SlugField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(), message="That username is taken.")],
    )
    display_name = serializers.CharField(max_length=160)
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"}, label="Confirm password")
    accept_terms = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        # Email is the sign-in identifier and login compares it lowercased, so
        # registration must normalise before the uniqueness check runs —
        # otherwise "Ada@example.com" and "ada@example.com" both take the address.
        if isinstance(data.get("email"), str):
            data = {**data, "email": data["email"].strip().lower()}
        return super().to_internal_value(data)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        candidate = User(email=attrs["email"], username=attrs["username"], display_name=attrs["display_name"])
        validate_password(attrs["password"], candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        validated_data.pop("accept_terms", None)
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if user is None:
            raise serializers.ValidationError({"detail": "The email or password is incorrect."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account has been deactivated."})
        attrs["user"] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        return attrs


class MePatchSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=160, required=False)
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        # Same normalisation as registration, checked here so a taken address is a
        # 400 with a message rather than a database IntegrityError.
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("That email is already in use.")
        return value
