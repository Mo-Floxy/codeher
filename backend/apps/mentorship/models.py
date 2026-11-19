from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


class MentorProfile(TimestampedModel):
    """A learner who volunteered to mentor. Admin approval gates discovery."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentor_profile")
    expertise = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True, max_length=3000)
    availability_note = models.CharField(max_length=300, blank=True)
    # ["Saturday morning", "Weekday evenings", ...]
    preferred_slots = models.JSONField(default=list, blank=True)
    capacity = models.PositiveIntegerField(default=3, help_text="Active mentees at once.")
    years_experience = models.PositiveIntegerField(default=0)
    current_role = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True, max_length=500)
    languages = models.JSONField(default=list, blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    is_accepting = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="mentors_approved"
    )
    matched_count = models.PositiveIntegerField(default=0)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ("-is_approved", "-matched_count", "user__display_name")
        indexes = [models.Index(fields=["is_approved", "is_accepting"])]

    def __str__(self):
        return f"Mentor {self.user.email}"

    @property
    def has_capacity(self):
        return MentorshipRequest.objects.filter(
            mentor=self.user, status=MentorshipRequest.STATUS_ACCEPTED
        ).count() < self.capacity


class MentorshipRequest(TimestampedModel):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentorship_requests")
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incoming_requests")
    goal = models.CharField(max_length=300)
    message = models.TextField(max_length=4000)
    preferred_slots = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    mentor_note = models.TextField(blank=True, max_length=2000)
    declined_reason = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    # Denormalised so the learner inbox does not join sessions.
    session_count = models.PositiveIntegerField(default=0)
    # 1 while the request is live, NULL once it is declined/withdrawn/completed/cancelled.
    # Same reason as the generated columns in apps.community: "unique only while pending
    # or accepted" needs a conditional index, which MySQL and TiDB never create.
    live_flag = models.GeneratedField(
        output_field=models.SmallIntegerField(),
        expression=models.Case(
            models.When(status__in=[STATUS_PENDING, STATUS_ACCEPTED], then=models.Value(1)),
            default=models.Value(None, output_field=models.SmallIntegerField()),
            output_field=models.SmallIntegerField(),
        ),
        db_persist=False,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["mentor", "status"]), models.Index(fields=["learner", "status"])]
        constraints = [
            models.CheckConstraint(condition=~models.Q(learner=models.F("mentor")), name="no_self_mentorship"),
            # One live request per learner/mentor pair; history is kept for closed pairs.
            models.UniqueConstraint(fields=["learner", "mentor", "live_flag"], name="uniq_live_mentorship_request"),
        ]

    def clean(self):
        super().clean()
        if self.learner_id is not None and self.learner_id == self.mentor_id:
            raise ValidationError({"mentor": "You cannot request mentorship from yourself."})

    def __str__(self):
        return f"{self.learner_id} -> {self.mentor_id}: {self.status}"


class MentorshipSession(TimestampedModel):
    request = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name="sessions")
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentor_sessions")
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learner_sessions")
    starts_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=45)
    agenda = models.TextField(blank=True, max_length=2000)
    # Mentor-only: learners see it only when they are the participant.
    meeting_url = models.URLField(blank=True, max_length=500)
    notes = models.TextField(blank=True, max_length=4000)
    status = models.CharField(
        max_length=12,
        choices=[("scheduled", "Scheduled"), ("completed", "Completed"), ("cancelled", "Cancelled")],
        default="scheduled",
        db_index=True,
    )
    learner_attended = models.BooleanField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("starts_at",)
        indexes = [models.Index(fields=["mentor", "starts_at"]), models.Index(fields=["learner", "starts_at"])]

    def __str__(self):
        return f"Session {self.id} at {self.starts_at:%Y-%m-%d %H:%M}"

    @property
    def is_upcoming(self):
        return self.status == "scheduled" and self.starts_at > timezone.now()
