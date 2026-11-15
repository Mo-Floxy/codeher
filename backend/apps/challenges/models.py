from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimestampedModel


class Challenge(TimestampedModel):
    DIFFICULTY_CHOICES = [("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")]
    CATEGORY_CHOICES = [
        ("javascript", "JavaScript"),
        ("python", "Python"),
        ("algorithms", "Algorithms"),
        ("web", "Web development"),
        ("data", "Data structures"),
        ("regex", "Regular expressions"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=300, blank=True)
    description = models.TextField(help_text="What the learner must implement, written for a beginner.")
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, default="beginner", db_index=True)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, default="javascript", db_index=True)
    # The function the learner must define; the runner calls it with each test's args.
    function_name = models.CharField(max_length=60, default="solution")
    starter_code = models.JSONField(default=dict, blank=True, help_text='{"javascript": "...", "python": "..."}')
    # [{"input": [...], "explanation": "..."}] shown in the UI.
    examples = models.JSONField(default=list, blank=True)
    hints = models.JSONField(default=list, blank=True)
    topics = models.JSONField(default=list, blank=True)
    points = models.PositiveIntegerField(default=20)
    allowed_languages = models.JSONField(default=list, blank=True, help_text='["javascript", "python"]')
    time_limit_ms = models.PositiveIntegerField(default=2000)
    memory_limit_mb = models.PositiveIntegerField(default=128)
    submission_count = models.PositiveIntegerField(default=0)
    accepted_count = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("difficulty", "position", "title")
        indexes = [models.Index(fields=["is_published", "difficulty", "category"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    @property
    def pass_rate_percent(self):
        if not self.submission_count:
            return 0
        return round(100 * self.accepted_count / self.submission_count)

    @property
    def difficulty_weight(self):
        return {"beginner": 1, "intermediate": 2, "advanced": 3}.get(self.difficulty, 1)


class ChallengeTestCase(TimestampedModel):
    """Grading data. Hidden cases are never serialised to the frontend."""

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="test_cases")
    name = models.CharField(max_length=120)
    args = models.JSONField(default=list, help_text="Positional arguments passed to the solution function.")
    expected = models.JSONField(help_text="Compared with deep equality against the returned value.")
    is_public = models.BooleanField(default=False, help_text="Public cases are shown in the instructions.")
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("position", "id")

    def __str__(self):
        return f"{self.challenge_id}: {self.name}"


class Submission(TimestampedModel):
    LANGUAGE_CHOICES = [("javascript", "JavaScript"), ("python", "Python")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    language = models.CharField(max_length=12, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    passed_count = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False, db_index=True)
    score = models.PositiveIntegerField(default=0, help_text="Percent of tests passed.")
    points_awarded = models.PositiveIntegerField(default=0)
    runtime_ms = models.PositiveIntegerField(default=0)
    # Populated when the runner rejected or crashed on the code.
    error = models.TextField(blank=True)
    runner_report = models.JSONField(default=list, blank=True)
    is_first_solve = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["challenge", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["challenge", "passed"]),
        ]

    def __str__(self):
        return f"{self.user_id} on {self.challenge_id}: {self.score}%"

    @property
    def failed_count(self):
        return max(0, self.total_tests - self.passed_count)
