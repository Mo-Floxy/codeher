from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class Achievement(TimestampedModel):
    """Catalogue entry. Progress is always evaluated from real rows, never trusted input."""

    CATEGORY_CHOICES = [
        ("learning", "Learning"),
        ("consistency", "Consistency"),
        ("challenges", "Challenges"),
        ("community", "Community"),
        ("career", "Career"),
    ]
    # Which counter the badge watches, used by services.evaluate_all.
    METRIC_CHOICES = [
        ("lessons_completed", "Lessons completed"),
        ("courses_completed", "Courses completed"),
        ("streak_days", "Current streak"),
        ("challenges_solved", "Challenges solved"),
        ("projects_published", "Projects published"),
        ("posts_created", "Posts created"),
        ("comments_created", "Comments created"),
        ("mentor_sessions", "Mentorship sessions"),
        ("total_xp", "Total XP"),
        ("quizzes_passed", "Quizzes passed"),
    ]

    code = models.SlugField(max_length=60, unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=300)
    # Shown on locked badges so learners know what the bar is.
    requirement_value = models.PositiveIntegerField(default=1)
    metric = models.CharField(max_length=30, choices=METRIC_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="learning")
    icon = models.CharField(max_length=40, default="Trophy", help_text="Lucide icon name.")
    color = models.CharField(max_length=9, default="#a855f7")
    xp_reward = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("category", "requirement_value", "title")

    def __str__(self):
        return f"{self.title} ({self.requirement_value}× {self.metric})"


class UserAchievement(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="awards")
    earned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-earned_at",)
        constraints = [models.UniqueConstraint(fields=["user", "achievement"], name="uniq_user_achievement")]


class PointEvent(models.Model):
    """Immutable audit log of every XP award.

    The unique constraint is what makes double-award attacks (repeat submissions,
    replayed completion calls) impossible rather than merely discouraged.
    """

    SOURCE_CHOICES = [
        ("lesson", "Lesson"),
        ("quiz", "Quiz"),
        ("course", "Course"),
        ("challenge", "Challenge"),
        ("project", "Project"),
        ("post", "Post"),
        ("comment", "Comment"),
        ("mentorship", "Mentorship"),
        ("achievement", "Achievement"),
        ("admin", "Administrator"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="point_events")
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=60)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=40)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["user", "source_type", "source_id", "reason"], name="uniq_point_award")
        ]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"+{self.amount} XP {self.reason} ({self.source_type}:{self.source_id})"
