from django.apps import AppConfig
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, username, password, **extra):
        if not email:
            raise ValueError("An email address is required.")
        if not username:
            raise ValueError("A username is required.")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            display_name=extra.pop("display_name", username),
            **extra,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        # Every account gets its gamification/visibility row at creation time so
        # no read path has to defend against a missing profile.
        Profile.objects.using(self._db).get_or_create(user=user)
        return user

    def create_user(self, email, username, password=None, **extra):
        extra.setdefault("role", "learner")
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, username, password, **extra)

    def create_superuser(self, email, username, password=None, **extra):
        extra.setdefault("role", "admin")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra["is_staff"] is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra["is_superuser"] is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create(email, username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Email is the sign-in identifier; username powers profile URLs."""

    ROLE_CHOICES = [("learner", "Learner"), ("mentor", "Mentor"), ("admin", "Admin")]

    email = models.EmailField(unique=True, db_index=True)
    username = models.SlugField(max_length=150, unique=True)
    display_name = models.CharField(max_length=160)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="learner", db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ("-date_joined",)
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self):
        return f"{self.display_name} <{self.email}>"

    @property
    def is_admin(self):
        return self.role == "admin" or self.is_staff

    @property
    def is_mentor_role(self):
        return self.role in {"mentor", "admin"}

    def natural_key(self):
        return (self.email,)


class Profile(TimestampedModel):
    SKILL_LEVELS = [("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(max_length=2000, blank=True)
    interests = models.JSONField(default=list, blank=True)
    learning_technologies = models.JSONField(default=list, blank=True)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default="beginner")
    timezone_name = models.CharField(max_length=60, default="UTC")
    country = models.CharField(max_length=80, blank=True)

    # Gamification state, recalculated by apps.achievements.services.
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    weekly_goal_minutes = models.PositiveIntegerField(default=90)

    # Visibility controls honoured by the public profile serializer.
    is_profile_public = models.BooleanField(default=True)
    show_email = models.BooleanField(default=False)
    show_projects = models.BooleanField(default=True)
    show_badges = models.BooleanField(default=True)
    show_streak = models.BooleanField(default=True)

    objects = models.Manager()

    class Meta:
        verbose_name_plural = "profiles"
        indexes = [
            models.Index(fields=["-total_xp"]),
            models.Index(fields=["-current_streak"]),
        ]

    def __str__(self):
        return f"Profile of {self.user.email}"


class Follow(TimestampedModel):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_set")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers_set")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="uniq_follow_pair"),
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")), name="no_self_follow"),
        ]
        indexes = [models.Index(fields=["following", "-created_at"])]

    def __str__(self):
        return f"{self.follower_id} -> {self.following_id}"
