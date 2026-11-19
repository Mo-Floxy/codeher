from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class Notification(TimestampedModel):
    KIND_CHOICES = [
        ("comment", "New comment"),
        ("reply", "Reply to you"),
        ("mention", "Mention"),
        ("mentorship_update", "Mentorship request update"),
        ("session_reminder", "Upcoming session"),
        ("course_announcement", "Course announcement"),
        ("challenge_result", "Challenge result"),
        ("achievement", "Achievement unlocked"),
        ("follow", "New follower"),
        ("moderation", "Moderation notice"),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=24, choices=KIND_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=500, blank=True)
    # Where the frontend should navigate when the row is opened.
    link = models.CharField(max_length=300, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_notified"
    )
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    # Dedupe key, e.g. ("comment", 41) so a re-edited comment cannot spam the inbox.
    dedupe_key = models.CharField(max_length=120, blank=True)
    # NULL when `dedupe_key` is blank. A conditional unique index is not created by
    # MySQL or TiDB, so the exemption is expressed as NULL — those rows stay unconstrained.
    dedupe_ref = models.GeneratedField(
        output_field=models.CharField(max_length=120),
        expression=models.Case(
            models.When(dedupe_key="", then=models.Value(None, output_field=models.CharField(max_length=120))),
            default=models.F("dedupe_key"),
            output_field=models.CharField(max_length=120),
        ),
        db_persist=False,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["recipient", "read_at", "-created_at"]),
            models.Index(fields=["recipient", "kind"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["recipient", "kind", "dedupe_ref"], name="uniq_notification_dedupe_ref")
        ]

    def __str__(self):
        return f"{self.kind} → {self.recipient_id}: {self.title}"

    @property
    def is_unread(self):
        return self.read_at is None
