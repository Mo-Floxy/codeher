"""Learning catalogue serializers.

Per-learner progress comes from a subquery on the requester's own Enrollment row,
so a card's percentage is always that person's real state rather than a course-wide
average.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz, QuizQuestion
from apps.progress.models import Certificate, Enrollment, QuizAttempt
from apps.users.serializers import avatar_url, safe_profile


class InstructorSerializer(serializers.Serializer):
    """Course cards show the instructor, whose headline and avatar live on Profile."""

    id = serializers.IntegerField()
    display_name = serializers.CharField()
    username = serializers.CharField()
    headline = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_headline(self, instructor):
        profile = safe_profile(instructor)
        return profile.headline if profile else ""

    def get_avatar(self, instructor):
        return avatar_url(safe_profile(instructor), self.context.get("request"))


class PathSummarySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = ["id", "slug", "title", "description", "level", "color", "icon", "course_count"]

    def get_course_count(self, path):
        return path.courses.filter(is_published=True).count()


class PathSerializer(serializers.ModelSerializer):
    """Path cards including how much of it the requester has finished."""

    course_count = serializers.SerializerMethodField()
    completed_course_count = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "level",
            "color",
            "icon",
            "position",
            "course_count",
            "completed_course_count",
            "courses",
        ]

    def get_course_count(self, path):
        return path.courses.filter(is_published=True).count()

    def get_completed_course_count(self, path):
        from apps.progress.models import Enrollment

        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return 0
        return Enrollment.objects.filter(
            user=request.user, course__learning_path=path, is_completed=True
        ).count()

    def get_courses(self, path):
        courses = list(path.courses.filter(is_published=True))
        return CourseCardSerializer(courses, many=True, context=self.context).data


class CourseCardSerializer(serializers.ModelSerializer):
    path = PathSummarySerializer(source="learning_path")
    instructor = InstructorSerializer()
    thumbnail = serializers.SerializerMethodField()
    lesson_count = serializers.IntegerField(read_only=True)
    total_lessons = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    completed_lesson_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "title",
            "subtitle",
            "description",
            "level",
            "category",
            "duration_hours",
            "thumbnail",
            "objectives",
            "requirements",
            "path",
            "instructor",
            "position",
            "lesson_count",
            "total_lessons",
            "enrolled_count",
            "progress_percent",
            "completed_lesson_count",
            "is_enrolled",
            "is_completed",
        ]

    def get_total_lessons(self, course):
        return course.lesson_count

    def get_thumbnail(self, course):
        if not course.thumbnail:
            return None
        url = course.thumbnail.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def _enrollment(self, course):
        cached = self.context.get("_enrollments")
        if cached is None:
            request = self.context.get("request")
            if not (request and request.user.is_authenticated):
                cached = {}
            else:
                from apps.progress.models import Enrollment

                cached = {
                    row["course"]: row
                    for row in Enrollment.objects.filter(user=request.user).values(
                        "course", "progress_percent", "completed_lesson_count", "is_completed"
                    )
                }
            self.context["_enrollments"] = cached
        return cached.get(course.pk)

    def get_progress_percent(self, course):
        row = self._enrollment(course)
        return row["progress_percent"] if row else 0

    def get_completed_lesson_count(self, course):
        row = self._enrollment(course)
        return row["completed_lesson_count"] if row else 0

    def get_is_enrolled(self, course):
        return self._enrollment(course) is not None

    def get_is_completed(self, course):
        row = self._enrollment(course)
        return bool(row and row["is_completed"])


class CourseSerializer(CourseCardSerializer):
    """Detail view: adds the learner's bookmark ids and the next lesson to take."""

    next_lesson = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()

    class Meta(CourseCardSerializer.Meta):
        fields = CourseCardSerializer.Meta.fields + ["is_published", "next_lesson", "certificate"]

    def get_next_lesson(self, course):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return None
        from apps.progress.models import Enrollment, LessonCompletion

        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if enrollment is None:
            return None
        done = set(
            LessonCompletion.objects.filter(user=request.user, lesson__course=course).values_list(
                "lesson_id", flat=True
            )
        )
        for lesson in course.lessons.filter(is_published=True).order_by("position", "id"):
            if lesson.pk not in done:
                return {"id": lesson.pk, "title": lesson.title, "position": lesson.position}
        return None

    def get_certificate(self, course):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return None
        from apps.progress.models import Certificate

        certificate = Certificate.objects.filter(user=request.user, course=course).first()
        if certificate is None:
            return None
        return CertificateSerializer(certificate).data


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Learner-facing: the answer key never leaves the server."""

    id = serializers.IntegerField()
    text = serializers.CharField(source="prompt")
    choices = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = ["id", "text", "choices", "hint", "position"]

    def get_choices(self, question):
        return [
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in (question.choices or [])
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    attempts_used = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "lesson",
            "passing_percent",
            "max_attempts",
            "xp",
            "questions",
            "question_count",
            "attempts_used",
            "best_score",
        ]

    def get_question_count(self, quiz):
        return quiz.questions.count()

    def get_attempts_used(self, quiz):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return 0
        from apps.progress.models import QuizAttempt

        return QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()

    def get_best_score(self, quiz):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return None
        from django.db.models import Max

        from apps.progress.models import QuizAttempt

        return QuizAttempt.objects.filter(user=request.user, quiz=quiz).aggregate(best=Max("score_percent"))["best"]


class LessonSerializer(serializers.ModelSerializer):
    module = serializers.IntegerField(source="module_id")
    module_title = serializers.CharField(source="module.title")
    course_title = serializers.CharField(source="course.title")
    course_slug = serializers.CharField(source="course.slug")
    quiz = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "course_title",
            "course_slug",
            "module",
            "module_title",
            "title",
            "kind",
            "summary",
            "body_blocks",
            "code_example",
            "estimated_minutes",
            "xp",
            "position",
            "requires_enrollment",
            "quiz",
            "completed",
            "bookmarked",
            "locked",
            "previous_lesson",
            "next_lesson",
        ]


    def get_quiz(self, lesson):
        if lesson.kind != "quiz":
            return None
        quiz = Quiz.objects.filter(lesson=lesson).first()
        if quiz is None:
            return None
        return QuizSerializer(quiz, context=self.context).data

    def get_completed(self, lesson):
        return lesson.pk in _state(self.context, lesson)["completed"]

    def get_bookmarked(self, lesson):
        return lesson.pk in _state(self.context, lesson)["bookmarked"]

    def get_locked(self, lesson):
        if not lesson.requires_enrollment:
            return False
        return lesson.course_id not in _state(self.context, lesson)["enrolled"]

    def _neighbour(self, lesson, direction):
        if direction == "prev":
            return (
                Lesson.objects.filter(course_id=lesson.course_id, is_published=True, position__lt=lesson.position)
                .order_by("-position")
                .first()
            )
        return (
            Lesson.objects.filter(course_id=lesson.course_id, is_published=True, position__gt=lesson.position)
            .order_by("position")
            .first()
        )

    def get_previous_lesson(self, lesson):
        neighbour = self._neighbour(lesson, "prev")
        return {"id": neighbour.pk, "title": neighbour.title} if neighbour else None

    def get_next_lesson(self, lesson):
        neighbour = self._neighbour(lesson, "next")
        return {"id": neighbour.pk, "title": neighbour.title} if neighbour else None


class LessonSummarySerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    kind = serializers.CharField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "kind",
            "summary",
            "position",
            "estimated_minutes",
            "xp",
            "requires_enrollment",
            "completed",
            "bookmarked",
            "locked",
        ]

    def get_completed(self, lesson):
        return lesson.pk in _state(self.context, None)["completed"]

    def get_bookmarked(self, lesson):
        return lesson.pk in _state(self.context, None)["bookmarked"]

    def get_locked(self, lesson):
        if not lesson.requires_enrollment:
            return False
        return lesson.course_id not in _state(self.context, None)["enrolled"]



class CurriculumModuleSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = ["id", "title", "summary", "position", "lessons"]

    def get_lessons(self, module):
        lessons = module.lessons.filter(is_published=True)
        return LessonSummarySerializer(lessons, many=True, context=self.context).data


class CourseEnrollSerializer(serializers.Serializer):
    """Empty body accepted; enrollment state is derived server-side."""

    enrolled = serializers.BooleanField(default=True)


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseCardSerializer()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "completed_lesson_count",
            "total_lesson_count",
            "progress_percent",
            "is_completed",
            "completed_at",
            "last_lesson",
            "created_at",
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.lesson.title")
    lesson = serializers.IntegerField(source="quiz.lesson_id")
    course = serializers.IntegerField(source="quiz.lesson.course_id")

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "lesson",
            "course",
            "score_percent",
            "correct_count",
            "total_count",
            "passed",
            "attempt_number",
            "detail",
            "created_at",
        ]


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title")
    course_slug = serializers.CharField(source="course.slug")
    course_level = serializers.CharField(source="course.level")
    duration_hours = serializers.IntegerField(source="course.duration_hours")
    instructor_name = serializers.CharField(
        source="course.instructor.display_name", default="", allow_blank=True, allow_null=True
    )

    class Meta:
        model = Certificate
        fields = [
            "id",
            "serial",
            "learner_name",
            "issued_at",
            "hours_studied",
            "final_percent",
            "course",
            "course_title",
            "course_slug",
            "course_level",
            "duration_hours",
            "instructor_name",
        ]


def learner_state(request):
    """Completed / bookmarked / enrolled id sets, memoised per serializer context."""
    if not (request and request.user.is_authenticated):
        return {"completed": set(), "bookmarked": set(), "enrolled": set()}

    from apps.progress.models import Enrollment, LessonBookmark, LessonCompletion

    user = request.user
    return {
        "completed": set(LessonCompletion.objects.filter(user=user).values_list("lesson_id", flat=True)),
        "bookmarked": set(LessonBookmark.objects.filter(user=user).values_list("lesson_id", flat=True)),
        "enrolled": set(Enrollment.objects.filter(user=user).values_list("course_id", flat=True)),
    }


def _state(context, lesson):
    cached = context.get("_lesson_state")
    if cached is None:
        cached = learner_state(context.get("request"))
        context["_lesson_state"] = cached
    return cached


class LearningPathWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = ["id", "title", "slug", "description", "level", "color", "icon", "position", "is_published"]
        read_only_fields = ["id"]


class CourseWriteSerializer(serializers.ModelSerializer):
    """Admin/instructor edits. Slug is generated by the model when left blank."""

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "description",
            "level",
            "category",
            "duration_hours",
            "thumbnail",
            "objectives",
            "requirements",
            "learning_path",
            "instructor",
            "position",
            "is_published",
        ]
        read_only_fields = ["id"]

    def validate_objectives(self, value):
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError("Objectives must be a list of strings.")
        return value or []

    def validate(self, attrs):
        concrete = {field.name for field in Course._meta.fields}
        instance = Course(**{key: value for key, value in attrs.items() if key in concrete})
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages})
        return attrs


class CourseModuleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = ["id", "course", "title", "summary", "position"]
        read_only_fields = ["id"]


class QuizQuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ["id", "quiz", "prompt", "choices", "hint", "explanation", "position"]
        read_only_fields = ["id"]


class QuizWriteSerializer(serializers.ModelSerializer):
    questions = QuizQuestionWriteSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = ["id", "lesson", "title", "passing_percent", "max_attempts", "xp", "questions"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        questions = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        for index, question in enumerate(questions, start=1):
            QuizQuestion.objects.create(quiz=quiz, position=question.get("position", index), **question)
        return quiz

    def update(self, instance, validated_data):
        questions = validated_data.pop("questions", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if questions is not None:
            instance.questions.all().delete()
            for index, question in enumerate(questions, start=1):
                QuizQuestion.objects.create(quiz=instance, position=question.get("position", index), **question)
        return instance


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "module",
            "course",
            "title",
            "kind",
            "summary",
            "body_blocks",
            "code_example",
            "estimated_minutes",
            "xp",
            "position",
            "is_published",
            "requires_enrollment",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        concrete = {field.name for field in Lesson._meta.fields}
        instance = self.instance or Lesson()
        for key, value in attrs.items():
            if key in concrete:
                setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
            )
        return attrs
