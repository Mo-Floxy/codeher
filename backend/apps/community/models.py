from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


class Post(TimestampedModel):
    TYPE_CHOICES = [
        ("question", "Question"),
        ("discussion", "Discussion"),
        ("showcase", "Showcase"),
        ("experience", "Learning experience"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    type = models.CharField(max_length=12, choices=TYPE_CHOICES, default="discussion", db_index=True)
    title = models.CharField(max_length=220)
    body = models.TextField(max_length=8000)
    tags = models.JSONField(default=list, blank=True)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    # Moderation state: removed content stays in the row for the audit trail.
    status = models.CharField(
        max_length=12,
        choices=[("published", "Published"), ("hidden", "Hidden"), ("draft", "Draft")],
        default="published",
        db_index=True,
    )
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)
    helpful_comment = models.ForeignKey(
        "community.Comment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_helpful_for",
    )
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-last_activity_at",)
        indexes = [
            models.Index(fields=["type", "-created_at"]),
            models.Index(fields=["status", "-last_activity_at"]),
        ]

    def __str__(self):
        return self.title

    def visible_to(self, user):
        if self.status == "published":
            return True
        return bool(user and user.is_authenticated and (user.is_staff or user.id == self.user_id))

    @property
    def is_solved(self):
        return self.helpful_comment_id is not None


class Comment(TimestampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    body = models.TextField(max_length=4000)
    status = models.CharField(
        max_length=12,
        choices=[("published", "Published"), ("hidden", "Hidden")],
        default="published",
    )
    likes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=["post", "created_at"])]

    def __str__(self):
        return f"Comment by {self.user_id} on post {self.post_id}"


class Project(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=4000)
    technologies = models.JSONField(default=list, blank=True)
    repo_url = models.URLField(blank=True, max_length=500)
    live_url = models.URLField(blank=True, max_length=500)
    screenshot = models.ImageField(upload_to="project-screenshots/", blank=True, null=True)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    status = models.CharField(
        max_length=12,
        choices=[("published", "Published"), ("hidden", "Hidden"), ("draft", "Draft")],
        default="published",
        db_index=True,
    )
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    # Engagement decayed by age, refreshed on interaction — see services.recalculate_trending.
    trending_score = models.FloatField(default=0.0, db_index=True)
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-trending_score", "-last_activity_at")
        indexes = [
            models.Index(fields=["status", "-trending_score"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def add_view(self):
        self.views_count = models.F("views_count") + 1
        self.save(update_fields=["views_count"])


class Engagement(TimestampedModel):
    """One row per (user, target, kind). Exactly one target FK must be set."""

    KIND_CHOICES = [("like", "Like"), ("bookmark", "Bookmark")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="engagements")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name="engagements")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name="engagements")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="engagements")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post", "kind"], name="uniq_post_engagement", condition=models.Q(post__isnull=False)),
            models.UniqueConstraint(fields=["user", "project", "kind"], name="uniq_project_engagement", condition=models.Q(project__isnull=False)),
            models.UniqueConstraint(fields=["user", "comment", "kind"], name="uniq_comment_engagement", condition=models.Q(comment__isnull=False)),
            models.CheckConstraint(
                condition=(
                    (models.Q(post__isnull=False) & models.Q(project__isnull=True) & models.Q(comment__isnull=True))
                    | (models.Q(project__isnull=False) & models.Q(post__isnull=True) & models.Q(comment__isnull=True))
                    | (models.Q(comment__isnull=False) & models.Q(post__isnull=True) & models.Q(project__isnull=True))
                ),
                name="exactly_one_engagement_target",
            ),
        ]
        indexes = [models.Index(fields=["user", "kind"])]

    def __str__(self):
        return f"{self.kind} by {self.user_id}"


class Report(TimestampedModel):
    REASON_CHOICES = [
        ("harassment", "Harassment or hate speech"),
        ("spam", "Spam or advertising"),
        ("unsafe", "Unsafe or malicious content"),
        ("plagiarism", "Stolen or plagiarised work"),
        ("privacy", "Personal data exposed"),
        ("other", "Something else"),
    ]
    TARGET_CHOICES = [("post", "Post"), ("comment", "Comment"), ("project", "Project")]
    STATUS_CHOICES = [("pending", "Pending"), ("resolved", "Resolved"), ("dismissed", "Dismissed")]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_created")
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name="reports")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="reports")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name="reports")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports_resolved"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    action_taken = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["created_by", "target_type", "post"], name="uniq_post_report", condition=models.Q(post__isnull=False)),
            models.UniqueConstraint(fields=["created_by", "target_type", "comment"], name="uniq_comment_report", condition=models.Q(comment__isnull=False)),
            models.UniqueConstraint(fields=["created_by", "target_type", "project"], name="uniq_project_report", condition=models.Q(project__isnull=False)),
        ]

    def __str__(self):
        return f"{self.target_type} {self.reason} ({self.status})"

    @property
    def target(self):
        return getattr(self, self.target_type, None)
