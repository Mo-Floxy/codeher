from django.db import models


class TimestampedModel(models.Model):
    """Created/updated timestamps shared by every domain model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Testimonial(TimestampedModel):
    """A genuine member quote, published only after admin curation.

    The landing page falls back to clearly-labelled sample content when no
    row exists, so an empty table here is meaningful rather than misleading.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
    )
    attribution = models.CharField(max_length=160, help_text="Name shown publicly, e.g. 'Amara O.'")
    role = models.CharField(max_length=160, blank=True)
    quote = models.TextField(max_length=900)
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="testimonials")
    is_published = models.BooleanField(default=False, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "testimonials"

    def __str__(self):
        return f"{self.attribution}: {self.quote[:48]}"


class Event(TimestampedModel):
    KIND_CHOICES = [
        ("workshop", "Workshop"),
        ("study_group", "Study group"),
        ("webinar", "Webinar"),
        ("hackathon", "Hackathon"),
        ("office_hours", "Office hours"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="study_group")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    url = models.URLField(blank=True)
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    is_published = models.BooleanField(default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ("starts_at",)

    def __str__(self):
        return f"{self.title} @ {self.starts_at:%Y-%m-%d}"


class Announcement(TimestampedModel):
    """Course-scoped broadcast that fans out into notifications."""

    AUDIENCE_CHOICES = [
        ("all_members", "All members"),
        ("course_enrolled", "Enrolled learners of one course"),
        ("path_enrolled", "Enrolled learners of a path"),
    ]

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="course_enrolled")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, null=True, blank=True, related_name="announcements")
    learning_path = models.ForeignKey(
        "courses.LearningPath", on_delete=models.CASCADE, null=True, blank=True, related_name="announcements"
    )
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="announcements_created")
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
