from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Cast, Concat
from django.utils import timezone

from apps.core.models import TimestampedModel


def _require_exactly_one_target(instance, field_names):
    """Application-level twin of the `exactly_one_*` check constraint.

    TiDB reports itself as MySQL 5.7, so Django's
    `supports_table_check_constraints` is False there and the check is skipped with a
    models.W036 warning. The rule still has to hold, because every read path assumes
    exactly one populated target.
    """
    populated = [name for name in field_names if getattr(instance, f"{name}_id") is not None]
    if len(populated) != 1:
        raise ValidationError(
            {"__all__": f"Exactly one of {', '.join(field_names)} must be set (got {len(populated)})."}
        )


def _target_ref(*field_names):
    """`'post:12'` for whichever of the given foreign keys is set, otherwise NULL.

    Written as CASE rather than COALESCE over a concatenation on purpose: Django's
    `Concat` wraps nullable arguments in `COALESCE(x, '')` on SQLite but not on MySQL,
    so a comment row would yield `'post:'` on one server and NULL on the other. The
    table prefix matters too — post 12 and comment 12 share an id but are different
    targets, and an unprefixed value would refuse a like on both.
    """
    return models.Case(
        *(
            models.When(
                **{f"{name}__isnull": False},
                then=Concat(
                    Value(f"{name}:"),
                    Cast(F(name), models.CharField(max_length=20)),
                    output_field=models.CharField(max_length=32),
                ),
            )
            for name in field_names
        ),
        default=Value(None, output_field=models.CharField(max_length=32)),
        output_field=models.CharField(max_length=32),
    )


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
    STATUS_CHOICES = [("published", "Published"), ("hidden", "Hidden"), ("draft", "Draft")]

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
        choices=STATUS_CHOICES,
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

    # Which target this row points at, flattened into one comparable value. The three
    # nullable foreign keys need a *conditional* unique index to be deduplicated, and
    # neither MySQL nor TiDB creates one (Django skips it with models.W036), so the
    # database-level guarantee lives here instead: a plain unique index over a column
    # that is NULL exactly when no target is set.
    target_ref = models.GeneratedField(
        output_field=models.CharField(max_length=32),
        expression=_target_ref("post", "project", "comment"),
        db_persist=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "kind", "target_ref"], name="uniq_engagement_target"),
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

    def clean(self):
        super().clean()
        _require_exactly_one_target(self, ("post", "project", "comment"))


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
    target_ref = models.GeneratedField(
        output_field=models.CharField(max_length=32),
        expression=_target_ref("post", "comment", "project"),
        db_persist=False,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "target_type", "target_ref"], name="uniq_report_target"
            ),
        ]

    def __str__(self):
        return f"{self.target_type} {self.reason} ({self.status})"

    def clean(self):
        super().clean()
        _require_exactly_one_target(self, ("post", "comment", "project"))
        populated = [name for name in ("post", "comment", "project") if getattr(self, f"{name}_id") is not None]
        if populated and populated[0] != self.target_type:
            raise ValidationError(
                {"target_type": f"Marked as a {self.target_type} report but attached to a {populated[0]}."}
            )

    @property
    def target(self):
        return getattr(self, self.target_type, None)
