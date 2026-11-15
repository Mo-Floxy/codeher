from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimestampedModel

LEVELS = [("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")]


class LearningPath(TimestampedModel):
    """A curriculum track such as 'React Development' that groups courses."""

    title = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVELS, default="beginner")
    color = models.CharField(max_length=9, default="#8b5cf6", help_text="Hex accent used by the card art.")
    icon = models.CharField(max_length=40, blank=True, help_text="Lucide icon name.")
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "title")
        verbose_name_plural = "learning paths"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180]
        super().save(*args, **kwargs)


class Course(TimestampedModel):
    CATEGORY_CHOICES = [
        ("web", "Web development"),
        ("javascript", "JavaScript"),
        ("python", "Python"),
        ("react", "React"),
        ("backend", "Backend"),
        ("databases", "Databases"),
        ("tools", "Developer tools"),
        ("security", "Security"),
        ("career", "Career"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVELS, default="beginner", db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="web", db_index=True)
    duration_hours = models.PositiveIntegerField(default=4)
    thumbnail = models.ImageField(upload_to="course-thumbnails/", blank=True, null=True)
    objectives = models.JSONField(default=list, blank=True)
    requirements = models.JSONField(default=list, blank=True)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses_taught"
    )
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    enrolled_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("learning_path", "position", "title")
        indexes = [
            models.Index(fields=["is_published", "level"]),
            models.Index(fields=["is_published", "category"]),
            models.Index(fields=["-enrolled_count"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "course"
            candidate = base
            suffix = 2
            while Course.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def lesson_count(self):
        return self.lessons.filter(is_published=True).count()

    def clean(self):
        if self.duration_hours and self.duration_hours > 500:
            raise ValidationError({"duration_hours": "Duration looks unrealistic — check the value."})


class CourseModule(TimestampedModel):
    """A named section inside a course that orders lessons."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=400, blank=True)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("position", "id")
        constraints = [models.UniqueConstraint(fields=["course", "position"], name="uniq_module_position")]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lesson(TimestampedModel):
    KIND_CHOICES = [("text", "Text"), ("code", "Code example"), ("quiz", "Quiz")]

    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="lessons")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=220)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="text")
    # Ordered content blocks: heading | paragraph | list | code | note | image.
    body_blocks = models.JSONField(default=list, blank=True)
    code_example = models.JSONField(default=dict, blank=True)
    summary = models.CharField(max_length=400, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=10)
    xp = models.PositiveIntegerField(default=settings.XP_RULES["lesson_complete"])
    position = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    requires_enrollment = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "id")
        constraints = [models.UniqueConstraint(fields=["module", "position"], name="uniq_lesson_position")]
        indexes = [models.Index(fields=["course", "is_published"])]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.kind == "code" and not (self.code_example or {}).get("code"):
            errors["code_example"] = "A code lesson needs a code_example with `code` and `language`."
        if self.body_blocks and not isinstance(self.body_blocks, list):
            errors["body_blocks"] = "body_blocks must be a list of block objects."
        if errors:
            raise ValidationError(errors)

    def validate_blocks(self):
        allowed = {"heading", "paragraph", "list", "code", "note", "image"}
        for index, block in enumerate(self.body_blocks or []):
            if not isinstance(block, dict) or block.get("type") not in allowed:
                raise ValidationError({"body_blocks": f"Block {index} has an unsupported type."})
            if block["type"] == "image" and not block.get("alt"):
                raise ValidationError({"body_blocks": f"Image block {index} needs alt text."})


class Quiz(TimestampedModel):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200, blank=True)
    passing_percent = models.PositiveIntegerField(default=70)
    max_attempts = models.PositiveIntegerField(default=0, help_text="0 means unlimited attempts.")
    xp = models.PositiveIntegerField(default=settings.XP_RULES["quiz_pass"])

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

    def clean(self):
        if self.lesson.kind != "quiz":
            raise ValidationError({"lesson": "Quizzes attach only to lessons of kind 'quiz'."})
        if not 1 <= self.passing_percent <= 100:
            raise ValidationError({"passing_percent": "Use a value between 1 and 100."})


class QuizQuestion(TimestampedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    # [{"text": "...", "is_correct": true}, ...]
    choices = models.JSONField(default=list)
    hint = models.CharField(max_length=400, blank=True)
    explanation = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("position", "id")

    def __str__(self):
        return self.prompt[:60]

    @property
    def correct_index(self):
        for index, choice in enumerate(self.choices or []):
            if choice.get("is_correct"):
                return index
        return None

    def clean(self):
        choices = self.choices or []
        if len(choices) < 2:
            raise ValidationError({"choices": "Provide at least two choices."})
        correct = [choice for choice in choices if choice.get("is_correct")]
        if len(correct) != 1:
            raise ValidationError({"choices": "Exactly one choice must be marked correct."})
